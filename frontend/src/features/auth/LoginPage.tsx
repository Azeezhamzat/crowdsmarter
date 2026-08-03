import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useSearchParams } from "react-router";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { Icon } from "../../components/Icon";
import { buildMailto, contactChannels } from "../../config/contact";
import { ApiError } from "../../lib/api";
import { loginWithPassword, verifyMfaCode } from "./api";

const loginSchema = z.object({
  email: z.string().trim().email("Enter a valid email address."),
  password: z.string().min(1, "Enter your password."),
});

type LoginInput = z.infer<typeof loginSchema>;

export function LoginPage() {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [capsLockOn, setCapsLockOn] = useState(false);
  const [mfaRequired, setMfaRequired] = useState(false);
  const [mfaCode, setMfaCode] = useState("");
  const [searchParams] = useSearchParams();
  const requestedNext = searchParams.get("next") ?? "/app";
  const nextPath = requestedNext.startsWith("/") && !requestedNext.startsWith("//") ? requestedNext : "/app";
  const queryClient = useQueryClient();
  const form = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });
  const login = useMutation({
    mutationFn: loginWithPassword,
    onSuccess: async (result) => {
      if ("mfa_required" in result) {
        setMfaRequired(true);
        return;
      }
      queryClient.setQueryData(["current-user"], result);
      await navigate(nextPath, { replace: true });
    },
  });
  const verifyMfa = useMutation({
    mutationFn: () => verifyMfaCode(mfaCode.trim()),
    onSuccess: async (user) => {
      queryClient.setQueryData(["current-user"], user);
      await navigate(nextPath, { replace: true });
    },
  });

  const hasCredentialError = login.error instanceof ApiError && login.error.status === 400;

  if (mfaRequired) {
    return (
      <main id="main-content" className="auth-layout auth-layout--executive" tabIndex={-1}>
        <section className="auth-card auth-card--executive" aria-labelledby="mfa-title">
          <div className="auth-card__content auth-card__content--executive">
            <div className="auth-card__heading">
              <span className="auth-card__icon"><Icon name="shield" size={23} /></span>
              <div><p className="public-eyebrow">Two-factor authentication</p><h2 id="mfa-title">Enter your authentication code</h2></div>
            </div>
            <p className="muted">Open your authenticator app and enter the current 6-digit code, or use one of your backup codes.</p>
            {verifyMfa.error ? (
              <div className="auth-error-panel" role="alert" aria-live="assertive">
                <div className="auth-error-panel__heading"><Icon name="warning" size={19} /><strong>That code did not work.</strong></div>
                <p>{verifyMfa.error instanceof ApiError ? verifyMfa.error.message : "The verification request could not be completed."}</p>
              </div>
            ) : null}
            <form onSubmit={(event) => { event.preventDefault(); verifyMfa.mutate(); }} noValidate>
              <label htmlFor="mfa-code">Authentication or backup code</label>
              <input
                id="mfa-code"
                inputMode="numeric"
                autoComplete="one-time-code"
                autoFocus
                value={mfaCode}
                onChange={(event) => setMfaCode(event.target.value)}
              />
              <button className="button button--primary button--full button--large auth-submit" type="submit" disabled={verifyMfa.isPending || !mfaCode.trim()}>
                {verifyMfa.isPending ? "Verifying…" : <>Verify and continue <Icon name="arrow-right" size={18} /></>}
              </button>
            </form>
            <button
              className="public-text-link auth-back-link"
              type="button"
              onClick={() => { setMfaRequired(false); setMfaCode(""); login.reset(); }}
            >
              <Icon name="arrow-right" size={16} />Start over
            </button>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main id="main-content" className="auth-layout auth-layout--executive" tabIndex={-1}>
      <section className="auth-introduction auth-introduction--executive" aria-labelledby="product-title">
        <Link className="auth-brand" to="/">
          <span className="public-brand__mark" aria-hidden="true"><span /><span /><span /></span>
          <span><strong>The CrowdSmarter</strong><small>Foresight-to-decision intelligence</small></span>
        </Link>
        <div className="auth-introduction__content auth-introduction__content--executive">
          <div className="auth-context-pill"><Icon name="shield" size={16} />Secure organisational workspace</div>
          <p className="eyebrow">Welcome back</p>
          <h1 id="product-title">Continue the reasoning—not just the record.</h1>
          <p>Return to your organisation’s signals, scenarios, decisions, collective evaluations, implementation commitments, and learning history.</p>
          <div className="auth-proof-grid">
            <article><Icon name="search" size={19} /><span><strong>Anticipate</strong><small>Signals, systems, scenarios</small></span></article>
            <article><Icon name="decision" size={19} /><span><strong>Decide</strong><small>Evidence, options, authority</small></span></article>
            <article><Icon name="analytics" size={19} /><span><strong>Learn</strong><small>Outcomes and lessons</small></span></article>
          </div>
        </div>
        <div className="auth-introduction__footer">
          <span>New to CrowdSmarter?</span>
          <Link to="/request-demo">Request a tailored demonstration <Icon name="arrow-right" size={16} /></Link>
        </div>
      </section>

      <section className="auth-card auth-card--executive" aria-labelledby="sign-in-title">
        <div className="auth-card__content auth-card__content--executive">
          <div className="auth-card__heading">
            <span className="auth-card__icon"><Icon name="shield" size={23} /></span>
            <div><p className="public-eyebrow">Authorised access</p><h2 id="sign-in-title">Sign in to CrowdSmarter</h2></div>
          </div>
          <p className="muted">Use the email address associated with your organisation invitation.</p>

          {login.error ? (
            <div className="auth-error-panel" role="alert" aria-live="assertive">
              <div className="auth-error-panel__heading"><Icon name="warning" size={19} /><strong>We could not sign you in.</strong></div>
              <p>
                {hasCredentialError
                  ? "Check the email spelling and password. Email matching is case-insensitive. If the problem continues, reset your password below."
                  : login.error instanceof ApiError
                    ? login.error.message
                    : "The sign-in request could not be completed. Please try again."}
              </p>
              {hasCredentialError ? <Link to="/forgot-password">Reset your password securely <Icon name="arrow-right" size={15} /></Link> : null}
            </div>
          ) : null}

          <form
            onSubmit={form.handleSubmit((values) => login.mutate({
              email: values.email.trim().toLowerCase(),
              password: values.password,
            }))}
            noValidate
          >
            <label htmlFor="email">Email address</label>
            <input
              id="email"
              type="email"
              inputMode="email"
              autoComplete="email"
              autoCapitalize="none"
              spellCheck={false}
              placeholder="you@organisation.com"
              {...form.register("email")}
            />
            <FieldError message={form.formState.errors.email?.message} />

            <div className="auth-label-row"><label htmlFor="password">Password</label><Link to="/forgot-password">Forgot password?</Link></div>
            <div className="password-field password-field--executive">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                onKeyDown={(event) => setCapsLockOn(event.getModifierState("CapsLock"))}
                onKeyUp={(event) => setCapsLockOn(event.getModifierState("CapsLock"))}
                {...form.register("password")}
              />
              <button type="button" aria-label={showPassword ? "Hide password" : "Show password"} onClick={() => setShowPassword((visible) => !visible)}>
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
            {capsLockOn ? <p className="auth-caps-warning"><Icon name="warning" size={14} />Caps Lock is on.</p> : null}
            <FieldError message={form.formState.errors.password?.message} />

            <button aria-label="Sign in" className="button button--primary button--full button--large auth-submit" type="submit" disabled={login.isPending}>
              {login.isPending ? "Signing in securely…" : <>Sign in securely <Icon name="arrow-right" size={18} /></>}
            </button>
          </form>

          <div className="auth-access-help">
            <Icon name="users" size={18} />
            <div><strong>Do you not have an account yet?</strong><span>Accounts are normally created through an organisation invitation.</span></div>
            <Link to="/request-demo">Request demo</Link>
          </div>
          <div className="auth-support-contact">
            <Icon name="shield" size={17} />
            <span>Account access issue?</span>
            <a href={buildMailto(contactChannels.support, "CrowdSmarter account access support")}>{contactChannels.support}</a>
          </div>
          <Link className="public-text-link auth-back-link" to="/"><Icon name="arrow-right" size={16} />Return to the public site</Link>
        </div>
      </section>
    </main>
  );
}
