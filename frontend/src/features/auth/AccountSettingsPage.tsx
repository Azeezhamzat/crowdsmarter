import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { Icon } from "../../components/Icon";
import { buildMailto, contactChannels } from "../../config/contact";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import type { MFAEnrollment } from "../../lib/types";
import {
  beginMfaEnrollment,
  changePassword,
  confirmMfaEnrollment,
  disableMfa,
  fetchCurrentUser,
  getMfaStatus,
  requestEmailChange,
  updateProfile,
} from "./api";

const profileSchema = z.object({ first_name: z.string().max(150), last_name: z.string().max(150) });
const passwordSchema = z.object({
  current_password: z.string().min(1, "Enter your current password."),
  new_password: z.string().min(12, "Use at least 12 characters."),
  confirm_password: z.string(),
}).refine((value) => value.new_password === value.confirm_password, { path: ["confirm_password"], message: "Passwords do not match." });
const emailSchema = z.object({
  new_email: z.string().trim().email("Enter a valid email address."),
  current_password: z.string().min(1, "Enter your current password."),
});
type ProfileInput = z.infer<typeof profileSchema>;
type PasswordInput = z.infer<typeof passwordSchema>;
type EmailInput = z.infer<typeof emailSchema>;

export function AccountSettingsPage() {
  const queryClient = useQueryClient();
  const user = useQuery({ queryKey: ["current-user"], queryFn: fetchCurrentUser });
  const profileForm = useForm<ProfileInput>({ resolver: zodResolver(profileSchema), defaultValues: { first_name: "", last_name: "" } });
  const passwordForm = useForm<PasswordInput>({ resolver: zodResolver(passwordSchema), defaultValues: { current_password: "", new_password: "", confirm_password: "" } });
  const emailForm = useForm<EmailInput>({ resolver: zodResolver(emailSchema), defaultValues: { new_email: "", current_password: "" } });
  useEffect(() => {
    if (user.data) profileForm.reset({ first_name: user.data.first_name, last_name: user.data.last_name });
  }, [user.data, profileForm]);
  const profile = useMutation({
    mutationFn: updateProfile,
    onSuccess: (updated) => { queryClient.setQueryData(["current-user"], updated); profileForm.reset({ first_name: updated.first_name, last_name: updated.last_name }); },
  });
  const password = useMutation({
    mutationFn: (input: PasswordInput) => changePassword({ current_password: input.current_password, new_password: input.new_password }),
    onSuccess: () => passwordForm.reset(),
  });
  const emailChange = useMutation({
    mutationFn: requestEmailChange,
    onSuccess: () => emailForm.reset(),
  });

  const mfaStatus = useQuery({ queryKey: ["mfa-status"], queryFn: getMfaStatus });
  const [enrollment, setEnrollment] = useState<MFAEnrollment | null>(null);
  const [enrollCode, setEnrollCode] = useState("");
  const [backupCodes, setBackupCodes] = useState<string[] | null>(null);
  const [disablePassword, setDisablePassword] = useState("");
  const refreshMfaStatus = () => queryClient.invalidateQueries({ queryKey: ["mfa-status"] });
  const beginEnroll = useMutation({
    mutationFn: beginMfaEnrollment,
    onSuccess: (data) => { setEnrollment(data); setEnrollCode(""); setBackupCodes(null); },
  });
  const confirmEnroll = useMutation({
    mutationFn: () => confirmMfaEnrollment(enrollCode.trim()),
    onSuccess: async (data) => {
      setBackupCodes(data.backup_codes);
      setEnrollment(null);
      setEnrollCode("");
      await refreshMfaStatus();
    },
  });
  const disable = useMutation({
    mutationFn: () => disableMfa(disablePassword),
    onSuccess: async () => { setDisablePassword(""); await refreshMfaStatus(); },
  });

  return (
    <div className="settings-page">
      <div className="page-heading"><div><p className="eyebrow">Personal account</p><h1>Account settings</h1><p className="muted">Maintain your identity and security without administrator intervention.</p></div></div>
      <div className="settings-grid">
        <section className="overview-card" aria-labelledby="profile-title">
          <h2 id="profile-title">Profile</h2>
          <p className="muted">Your name appears on decisions, positions, audit events, and exports.</p>
          {profile.error ? <StatusMessage kind="error">{profile.error instanceof ApiError ? profile.error.message : "The profile could not be saved."}</StatusMessage> : null}
          {profile.isSuccess ? <StatusMessage kind="success">Profile updated.</StatusMessage> : null}
          <form onSubmit={profileForm.handleSubmit((values) => profile.mutate(values))} noValidate>
            <label htmlFor="first-name">First name</label><input id="first-name" {...profileForm.register("first_name")} /><FieldError message={profileForm.formState.errors.first_name?.message} />
            <label htmlFor="last-name">Last name</label><input id="last-name" {...profileForm.register("last_name")} /><FieldError message={profileForm.formState.errors.last_name?.message} />
            <button className="button button--primary" type="submit" disabled={profile.isPending}>{profile.isPending ? "Saving…" : "Save profile"}</button>
          </form>
        </section>
        <section className="overview-card" aria-labelledby="email-title">
          <h2 id="email-title">Email address</h2>
          <p className="muted">Change the address you use to sign in. We verify the new address before changing your account.</p>
          <label htmlFor="account-email">Current email address</label>
          <input id="account-email" value={user.data?.email ?? ""} readOnly />
          {emailChange.error ? <StatusMessage kind="error">{emailChange.error instanceof ApiError ? emailChange.error.message : "The email change could not be requested."}</StatusMessage> : null}
          {emailChange.isSuccess ? (
            <StatusMessage kind="success">
              Check the new email address and open its verification link. Your current email remains active until you confirm.
            </StatusMessage>
          ) : null}
          {emailChange.data?.development_verification_url ? (
            <p className="field-help">
              Local development only: <a href={emailChange.data.development_verification_url}>open the verification link</a>.
            </p>
          ) : null}
          <form onSubmit={emailForm.handleSubmit((values) => emailChange.mutate(values))} noValidate>
            <label htmlFor="new-account-email">New email address</label>
            <input id="new-account-email" type="email" autoComplete="email" {...emailForm.register("new_email")} />
            <FieldError message={emailForm.formState.errors.new_email?.message} />
            <label htmlFor="email-change-password">Confirm with current password</label>
            <input id="email-change-password" type="password" autoComplete="current-password" {...emailForm.register("current_password")} />
            <FieldError message={emailForm.formState.errors.current_password?.message} />
            <button className="button button--primary" type="submit" disabled={emailChange.isPending}>
              {emailChange.isPending ? "Sending verification…" : "Verify new email"}
            </button>
          </form>
        </section>
        <section className="overview-card" aria-labelledby="security-title">
          <h2 id="security-title">Password and security</h2>
          <p className="muted">Changing your password keeps this browser signed in and invalidates password-reset links.</p>
          {password.error ? <StatusMessage kind="error">{password.error instanceof ApiError ? password.error.message : "The password could not be changed."}</StatusMessage> : null}
          {password.isSuccess ? <StatusMessage kind="success">Password changed successfully.</StatusMessage> : null}
          <form onSubmit={passwordForm.handleSubmit((values) => password.mutate(values))} noValidate>
            <label htmlFor="current-account-password">Current password</label><input id="current-account-password" type="password" autoComplete="current-password" {...passwordForm.register("current_password")} /><FieldError message={passwordForm.formState.errors.current_password?.message} />
            <label htmlFor="new-account-password">New password</label><input id="new-account-password" type="password" autoComplete="new-password" {...passwordForm.register("new_password")} /><FieldError message={passwordForm.formState.errors.new_password?.message} />
            <label htmlFor="confirm-account-password">Confirm new password</label><input id="confirm-account-password" type="password" autoComplete="new-password" {...passwordForm.register("confirm_password")} /><FieldError message={passwordForm.formState.errors.confirm_password?.message} />
            <button className="button button--primary" type="submit" disabled={password.isPending}>{password.isPending ? "Changing…" : "Change password"}</button>
          </form>
        </section>
        <section className="overview-card" aria-labelledby="mfa-title">
          <h2 id="mfa-title">Two-factor authentication</h2>
          <p className="muted">Require a code from an authenticator app in addition to your password when signing in.</p>
          {beginEnroll.error ? <StatusMessage kind="error">{beginEnroll.error instanceof ApiError ? beginEnroll.error.message : "Enrollment could not be started."}</StatusMessage> : null}
          {confirmEnroll.error ? <StatusMessage kind="error">{confirmEnroll.error instanceof ApiError ? confirmEnroll.error.message : "That code did not match."}</StatusMessage> : null}
          {disable.error ? <StatusMessage kind="error">{disable.error instanceof ApiError ? disable.error.message : "Two-factor authentication could not be disabled."}</StatusMessage> : null}

          {backupCodes ? (
            <div className="mfa-backup-codes">
              <StatusMessage kind="success">Two-factor authentication is enabled. Save these backup codes now - each one only appears once, and any of them can sign you in if you lose access to your authenticator app.</StatusMessage>
              <ul className="mfa-backup-codes__list">{backupCodes.map((code) => <li key={code}><code>{code}</code></li>)}</ul>
              <button className="button button--secondary" type="button" onClick={() => setBackupCodes(null)}>Done</button>
            </div>
          ) : mfaStatus.data?.is_enabled ? (
            <div>
              <p><Icon name="shield" size={16} /> Two-factor authentication is currently enabled.</p>
              <label htmlFor="mfa-disable-password">Current password</label>
              <input id="mfa-disable-password" type="password" autoComplete="current-password" value={disablePassword} onChange={(event) => setDisablePassword(event.target.value)} />
              <button className="button button--danger-quiet" type="button" disabled={disable.isPending || !disablePassword} onClick={() => disable.mutate()}>
                {disable.isPending ? "Disabling…" : "Disable two-factor authentication"}
              </button>
            </div>
          ) : enrollment ? (
            <div>
              <p>Add this key to your authenticator app (Google Authenticator, 1Password, Authy, or similar):</p>
              <p className="mfa-secret"><code>{enrollment.secret}</code></p>
              <label htmlFor="mfa-enroll-code">Enter the 6-digit code it shows</label>
              <input id="mfa-enroll-code" inputMode="numeric" autoComplete="one-time-code" value={enrollCode} onChange={(event) => setEnrollCode(event.target.value)} />
              <button className="button button--primary" type="button" disabled={confirmEnroll.isPending || !enrollCode.trim()} onClick={() => confirmEnroll.mutate()}>
                {confirmEnroll.isPending ? "Confirming…" : "Confirm and enable"}
              </button>
            </div>
          ) : (
            <button className="button button--primary" type="button" disabled={beginEnroll.isPending} onClick={() => beginEnroll.mutate()}>
              {beginEnroll.isPending ? "Starting…" : "Enable two-factor authentication"}
            </button>
          )}
        </section>
      </div>
      <div className="account-operations-grid">
        <section className="overview-card account-contact-card" aria-labelledby="account-support-title">
          <span className="account-contact-card__icon"><Icon name="users" size={20} /></span>
          <div>
            <h2 id="account-support-title">Account and product support</h2>
            <p className="muted">Use the official CrowdSmarter address for access issues, account questions, and product support.</p>
            <a href={buildMailto(contactChannels.support, "CrowdSmarter account support", `Account email: ${user.data?.email ?? ""}\nIssue:`)}>{contactChannels.support}</a>
          </div>
        </section>
        {user.data?.is_staff ? (
          <section className="overview-card account-contact-card" aria-labelledby="system-admin-title">
            <span className="account-contact-card__icon"><Icon name="shield" size={20} /></span>
            <div>
              <h2 id="system-admin-title">System administration</h2>
              <p className="muted">Use Django administration for technical access, decision-enquiry triage, and exceptional data correction, not normal decision work.</p>
              <a href={contactChannels.adminUrl} target="_blank" rel="noreferrer">Open system administration <Icon name="external" size={15} /></a>
            </div>
          </section>
        ) : null}
      </div>
    </div>
  );
}
