import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { Icon } from "../../components/Icon";
import { buildMailto, contactChannels } from "../../config/contact";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import { changePassword, fetchCurrentUser, updateProfile } from "./api";

const profileSchema = z.object({ first_name: z.string().max(150), last_name: z.string().max(150) });
const passwordSchema = z.object({
  current_password: z.string().min(1, "Enter your current password."),
  new_password: z.string().min(12, "Use at least 12 characters."),
  confirm_password: z.string(),
}).refine((value) => value.new_password === value.confirm_password, { path: ["confirm_password"], message: "Passwords do not match." });
type ProfileInput = z.infer<typeof profileSchema>;
type PasswordInput = z.infer<typeof passwordSchema>;

export function AccountSettingsPage() {
  const queryClient = useQueryClient();
  const user = useQuery({ queryKey: ["current-user"], queryFn: fetchCurrentUser });
  const profileForm = useForm<ProfileInput>({ resolver: zodResolver(profileSchema), defaultValues: { first_name: "", last_name: "" } });
  const passwordForm = useForm<PasswordInput>({ resolver: zodResolver(passwordSchema), defaultValues: { current_password: "", new_password: "", confirm_password: "" } });
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
            <label htmlFor="account-email">Email address</label><input id="account-email" value={user.data?.email ?? ""} readOnly /><p className="field-help">Email changes require a separately verified workflow and are not enabled in this release.</p>
            <button className="button button--primary" type="submit" disabled={profile.isPending}>{profile.isPending ? "Saving…" : "Save profile"}</button>
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
              <p className="muted">Use Django administration for technical access, demo-request triage, and exceptional data correction—not normal decision work.</p>
              <a href={contactChannels.adminUrl} target="_blank" rel="noreferrer">Open system administration <Icon name="external" size={15} /></a>
            </div>
          </section>
        ) : null}
      </div>
    </div>
  );
}
