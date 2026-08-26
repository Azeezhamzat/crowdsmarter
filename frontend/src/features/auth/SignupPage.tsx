import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { Icon } from "../../components/Icon";
import { LanguageSwitcher } from "../../components/LanguageSwitcher";
import { LogoMark } from "../../components/Logo";
import { ApiError } from "../../lib/api";
import { signupCatalog } from "../../lib/catalogs/signup";
import { useTranslations } from "../../lib/i18n";
import { signUp } from "./api";

const signupSchema = z.object({
  full_name: z.string().trim().min(2, "Enter your name."),
  email: z.string().trim().email("Enter a valid email address."),
  password: z.string().min(8, "Use at least 8 characters."),
  organisation_name: z.string().trim().min(2, "Give your commons a name."),
});

type SignupInput = z.infer<typeof signupSchema>;

export function SignupPage() {
  const navigate = useNavigate();
  const t = useTranslations(signupCatalog);
  const [showPassword, setShowPassword] = useState(false);
  const queryClient = useQueryClient();
  const form = useForm<SignupInput>({
    resolver: zodResolver(signupSchema),
    defaultValues: { full_name: "", email: "", password: "", organisation_name: "" },
  });
  const signup = useMutation({
    mutationFn: signUp,
    onSuccess: async (result) => {
      queryClient.setQueryData(["current-user"], result.user);
      await navigate(`/organisations/${result.organisation.id}/sessions`, { replace: true });
    },
  });

  return (
    <main id="main-content" className="auth-layout auth-layout--executive" tabIndex={-1}>
      <section className="auth-introduction auth-introduction--executive" aria-labelledby="signup-product-title">
        <Link className="auth-brand" to="/">
          <LogoMark size={38} variant="inverse" />
          <span><strong>CrowdSmarter</strong><small>Foresight. Collective intelligence. Decisions.</small></span>
        </Link>
        <div className="auth-introduction__content auth-introduction__content--executive">
          <div className="auth-context-pill"><Icon name="shield" size={16} />{t.eyebrow}</div>
          <div className="auth-language-row"><LanguageSwitcher /></div>
          <h1 id="signup-product-title">{t.heading}</h1>
          <p>{t.lead}</p>
          <div className="auth-proof-grid">
            <article><Icon name="search" size={19} /><span><strong>Anticipate</strong><small>Signals, systems, scenarios</small></span></article>
            <article><Icon name="decision" size={19} /><span><strong>Decide</strong><small>Evidence, options, authority</small></span></article>
            <article><Icon name="analytics" size={19} /><span><strong>Learn</strong><small>Outcomes and lessons</small></span></article>
          </div>
        </div>
      </section>

      <section className="auth-card auth-card--executive" aria-labelledby="signup-title">
        <div className="auth-card__content auth-card__content--executive">
          <div className="auth-card__heading">
            <span className="auth-card__icon"><Icon name="shield" size={23} /></span>
            <div><p className="public-eyebrow">{t.eyebrow}</p><h2 id="signup-title">{t.heading}</h2></div>
          </div>

          {signup.error ? (
            <div className="auth-error-panel" role="alert" aria-live="assertive">
              <div className="auth-error-panel__heading"><Icon name="warning" size={19} /><strong>We could not create your commons.</strong></div>
              <p>{signup.error instanceof ApiError ? signup.error.message : "The request could not be completed. Please try again."}</p>
            </div>
          ) : null}

          <form onSubmit={form.handleSubmit((values) => signup.mutate(values))} noValidate>
            <label htmlFor="full_name">{t.nameLabel}</label>
            <input id="full_name" autoComplete="name" {...form.register("full_name")} />
            <FieldError message={form.formState.errors.full_name?.message} />

            <label htmlFor="signup-email">{t.emailLabel}</label>
            <input
              id="signup-email"
              type="email"
              inputMode="email"
              autoComplete="email"
              autoCapitalize="none"
              spellCheck={false}
              {...form.register("email")}
            />
            <FieldError message={form.formState.errors.email?.message} />

            <label htmlFor="signup-password">{t.passwordLabel}</label>
            <div className="password-field password-field--executive">
              <input
                id="signup-password"
                type={showPassword ? "text" : "password"}
                autoComplete="new-password"
                {...form.register("password")}
              />
              <button type="button" aria-label={showPassword ? "Hide password" : "Show password"} onClick={() => setShowPassword((visible) => !visible)}>
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
            <p className="muted">{t.passwordHint}</p>
            <FieldError message={form.formState.errors.password?.message} />

            <label htmlFor="organisation_name">{t.commonsNameLabel}</label>
            <input id="organisation_name" {...form.register("organisation_name")} />
            <p className="muted">{t.commonsNameHint}</p>
            <FieldError message={form.formState.errors.organisation_name?.message} />

            <button aria-label={t.submitButton} className="button button--primary button--full button--large auth-submit" type="submit" disabled={signup.isPending}>
              {signup.isPending ? t.submittingButton : <>{t.submitButton} <Icon name="arrow-right" size={18} /></>}
            </button>
          </form>

          <div className="auth-access-help">
            <Icon name="users" size={18} />
            <div><strong>{t.alreadyHaveAccount}</strong></div>
            <Link to="/login">{t.signInLink}</Link>
          </div>
          <Link className="public-text-link auth-back-link" to="/"><Icon name="arrow-right" size={16} />Return to the public site</Link>
        </div>
      </section>
    </main>
  );
}
