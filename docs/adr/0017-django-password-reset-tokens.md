# ADR 0017 — Use Django password-reset tokens with fragment-based browser links

## Status

Accepted.

## Context

Users need self-service recovery without a paid identity provider. The flow must avoid account enumeration, database storage of reusable reset secrets, and routine proxy logging of bearer tokens.

## Decision

Use Django's `PasswordResetTokenGenerator` with URL-safe user identifiers. Reset links use `/reset-password#uid=...&token=...`, placing the secret in the browser fragment. The React application submits the values to a dedicated CSRF-protected endpoint. Public request responses are generic whether or not an account exists.

The token validity is controlled by `PASSWORD_RESET_TIMEOUT` and becomes invalid after the password changes. Request and confirmation endpoints are separately throttled. In local development only, the generated link may be returned to the browser because console email is the zero-cost default.

## Consequences

No reset-token model or paid authentication service is required. Production must keep `DJANGO_SECRET_KEY` stable, configure a real email provider, use HTTPS, and avoid enabling Django debug responses.
