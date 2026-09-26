import { useMutation } from "@tanstack/react-query";
import { useMemo } from "react";
import { Link } from "react-router";

import { Icon } from "../../components/Icon";
import { LogoMark } from "../../components/Logo";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import { confirmEmailChange } from "./api";

export function VerifyEmailChangePage() {
  const token = useMemo(() => {
    const params = new URLSearchParams(window.location.hash.replace(/^#/, ""));
    return params.get("token") ?? "";
  }, []);
  const confirmation = useMutation({ mutationFn: () => confirmEmailChange(token) });
  const linkMissing = !token;

  return (
    <main id="main-content" className="auth-layout auth-layout--premium" tabIndex={-1}>
      <section className="auth-introduction auth-introduction--premium" aria-labelledby="verify-email-product-title">
        <Link className="auth-brand" to="/"><LogoMark size={38} variant="inverse" /><strong>CrowdSmarter</strong></Link>
        <div className="auth-introduction__content">
          <p className="eyebrow">Account security</p>
          <h1 id="verify-email-product-title">Verify your new email address.</h1>
          <p>Your sign-in address changes only after you explicitly confirm it here.</p>
        </div>
      </section>
      <section className="auth-card auth-card--premium" aria-labelledby="verify-email-title">
        <div className="auth-card__content">
          <span className="auth-card__icon"><Icon name="shield" size={24} /></span>
          <h2 id="verify-email-title">Confirm email change</h2>
          {linkMissing ? <StatusMessage kind="error">This verification link is incomplete. Request a new one from account settings.</StatusMessage> : null}
          {confirmation.error ? (
            <StatusMessage kind="error">
              {confirmation.error instanceof ApiError ? confirmation.error.message : "The email address could not be changed."}
            </StatusMessage>
          ) : null}
          {confirmation.isSuccess ? (
            <>
              <StatusMessage kind="success">Your sign-in email is now {confirmation.data.email}.</StatusMessage>
              <Link className="button button--primary button--full button-link" to="/account">Return to account settings</Link>
            </>
          ) : (
            <button
              className="button button--primary button--full button--large"
              type="button"
              disabled={confirmation.isPending || linkMissing}
              onClick={() => confirmation.mutate()}
            >
              {confirmation.isPending ? "Confirming…" : "Confirm new email address"}
            </button>
          )}
          <Link className="public-text-link auth-back-link" to="/account">Back to account settings</Link>
        </div>
      </section>
    </main>
  );
}
