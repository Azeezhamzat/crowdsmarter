import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link } from "react-router";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { Icon } from "../../components/Icon";
import { LogoMark } from "../../components/Logo";
import { buildMailto, contactChannels } from "../../config/contact";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import { requestPasswordReset } from "./api";

const schema = z.object({ email: z.string().email("Enter a valid email address.") });
type Input = z.infer<typeof schema>;

export function ForgotPasswordPage() {
  const form = useForm<Input>({ resolver: zodResolver(schema), defaultValues: { email: "" } });
  const reset = useMutation({ mutationFn: requestPasswordReset });

  return (
    <main id="main-content" className="auth-layout auth-layout--premium" tabIndex={-1}>
      <section className="auth-introduction auth-introduction--premium" aria-labelledby="recovery-product-title">
        <Link className="auth-brand" to="/"><LogoMark size={38} variant="inverse" /><strong>CrowdSmarter</strong></Link>
        <div className="auth-introduction__content">
          <p className="eyebrow">Secure account recovery</p>
          <h1 id="recovery-product-title">Recover access without involving an administrator.</h1>
          <p>Reset links are time-limited, become invalid after use, and do not reveal whether an email address is registered.</p>
          <div className="auth-proof-list">
            <span><Icon name="shield" size={17} />Generic responses prevent account discovery</span>
            <span><Icon name="check" size={17} />Existing sessions are protected</span>
            <span><Icon name="check" size={17} />Security events are auditable</span>
          </div>
        </div>
      </section>
      <section className="auth-card auth-card--premium" aria-labelledby="reset-request-title">
        <div className="auth-card__content">
          <span className="auth-card__icon"><Icon name="shield" size={24} /></span>
          <h2 id="reset-request-title">Reset your password</h2>
          <p className="muted">Enter the email address used for your CrowdSmarter account.</p>
          {reset.error ? <StatusMessage kind="error">{reset.error instanceof ApiError ? reset.error.message : "The request failed."}</StatusMessage> : null}
          {reset.data ? (
            <>
              <StatusMessage kind="success">{reset.data.detail}</StatusMessage>
              {reset.data.development_reset_url ? (
                <div className="development-link-card">
                  <strong>Local development link</strong>
                  <p>Because console email is enabled, use this link on this computer:</p>
                  <a href={reset.data.development_reset_url}>Choose a new password</a>
                </div>
              ) : null}
            </>
          ) : (
            <form onSubmit={form.handleSubmit((values) => reset.mutate(values))} noValidate>
              <label htmlFor="reset-email">Email address</label>
              <input id="reset-email" type="email" autoComplete="email" {...form.register("email")} />
              <FieldError message={form.formState.errors.email?.message} />
              <button className="button button--primary button--full button--large" type="submit" disabled={reset.isPending}>{reset.isPending ? "Sending…" : "Send reset link"}</button>
            </form>
          )}
          <div className="auth-support-contact auth-support-contact--recovery">
            <Icon name="users" size={17} />
            <span>Still unable to recover access?</span>
            <a href={buildMailto(contactChannels.support, "CrowdSmarter password recovery support")}>{contactChannels.support}</a>
          </div>
          <Link className="public-text-link auth-back-link" to="/login">Return to sign in</Link>
        </div>
      </section>
    </main>
  );
}
