import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { Icon } from "../../components/Icon";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import { confirmPasswordReset } from "./api";

const schema = z.object({
  new_password: z.string().min(12, "Use at least 12 characters."),
  confirm_password: z.string(),
}).refine((value) => value.new_password === value.confirm_password, {
  path: ["confirm_password"], message: "Passwords do not match.",
});
type Input = z.infer<typeof schema>;

export function ResetPasswordPage() {
  const [showPassword, setShowPassword] = useState(false);
  const tokenParts = useMemo(() => {
    const params = new URLSearchParams(window.location.hash.replace(/^#/, ""));
    return { uid: params.get("uid") ?? "", token: params.get("token") ?? "" };
  }, []);
  const form = useForm<Input>({ resolver: zodResolver(schema), defaultValues: { new_password: "", confirm_password: "" } });
  const reset = useMutation({
    mutationFn: (input: Input) => confirmPasswordReset({ ...tokenParts, new_password: input.new_password }),
  });
  const linkMissing = !tokenParts.uid || !tokenParts.token;

  return (
    <main id="main-content" className="auth-layout auth-layout--premium" tabIndex={-1}>
      <section className="auth-introduction auth-introduction--premium" aria-labelledby="new-password-product-title">
        <Link className="auth-brand" to="/"><span className="public-brand__mark" aria-hidden="true"><span /><span /><span /></span><strong>The CrowdSmarter</strong></Link>
        <div className="auth-introduction__content">
          <p className="eyebrow">Account security</p>
          <h1 id="new-password-product-title">Choose a new password.</h1>
          <p>Your reset link is single-use in practice: changing the password invalidates the token immediately.</p>
        </div>
      </section>
      <section className="auth-card auth-card--premium" aria-labelledby="new-password-title">
        <div className="auth-card__content">
          <span className="auth-card__icon"><Icon name="shield" size={24} /></span>
          <h2 id="new-password-title">Create a new password</h2>
          {linkMissing ? <StatusMessage kind="error">This reset link is incomplete. Request a new link.</StatusMessage> : null}
          {reset.error ? <StatusMessage kind="error">{reset.error instanceof ApiError ? reset.error.message : "The password could not be reset."}</StatusMessage> : null}
          {reset.isSuccess ? (
            <><StatusMessage kind="success">Password reset successfully.</StatusMessage><Link className="button button--primary button--full button-link" to="/login">Sign in with the new password</Link></>
          ) : (
            <form onSubmit={form.handleSubmit((values) => reset.mutate(values))} noValidate>
              <label htmlFor="new-password">New password</label>
              <div className="password-field"><input id="new-password" type={showPassword ? "text" : "password"} autoComplete="new-password" {...form.register("new_password")} /><button type="button" onClick={() => setShowPassword((value) => !value)}>{showPassword ? "Hide" : "Show"}</button></div>
              <FieldError message={form.formState.errors.new_password?.message} />
              <label htmlFor="confirm-password">Confirm new password</label>
              <input id="confirm-password" type={showPassword ? "text" : "password"} autoComplete="new-password" {...form.register("confirm_password")} />
              <FieldError message={form.formState.errors.confirm_password?.message} />
              <button className="button button--primary button--full button--large" type="submit" disabled={reset.isPending || linkMissing}>{reset.isPending ? "Resetting…" : "Reset password"}</button>
            </form>
          )}
          <Link className="public-text-link auth-back-link" to="/forgot-password">Request another link</Link>
        </div>
      </section>
    </main>
  );
}
