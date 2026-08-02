# ADR 0009: Use expiring organisation-controlled invitations

## Status

Accepted.

## Context

The product needs a commercial onboarding path without a paid identity provider, unrestricted public registration, administrator-created passwords, or silent membership assignment. Invitation links are bearer credentials and may pass through browsers, email systems, reverse proxies, and logs.

## Decision

- Registration is invitation-only for now.
- Owners and administrators issue invitations; only owners may grant owner access.
- Membership is created only after explicit acceptance.
- New users choose their own password under Django's validators.
- Existing users must authenticate with the invited email; an invitation cannot reset a password.
- Raw secrets use at least 256 bits of randomness and are stored only as a `DJANGO_SECRET_KEY`-keyed SHA-256 digest.
- Browser links place the token in a URL fragment. The SPA passes it to Django through `X-Invitation-Token`, not an API URL or query string.
- Invitations expire after a configurable period, can be revoked, and rotate their secret when resent.
- Acceptance rechecks that the issuing manager still has sufficient authority.
- Email delivery is provider-configured and best-effort; the durable invitation record does not depend on a worker or SMTP availability.

## Consequences

The initial product has no open sign-up page. Organisations retain control of tenant access, token leakage through ordinary access logs is reduced, and paid authentication infrastructure remains unnecessary. Production operators must keep the Django secret stable and configure SMTP plus the public frontend base URL. Password reset and enterprise SSO remain separate future workflows.
