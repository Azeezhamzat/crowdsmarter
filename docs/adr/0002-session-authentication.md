# ADR 0002: Use Django session authentication for the browser

- Status: Accepted
- Date: 2026-07-25

## Context

The first client is a React web application. Paid identity providers conflict with the zero-cost constraint, while browser-stored bearer tokens increase credential-handling risk.

## Decision

Use Django authentication, server-side sessions, secure cookies, and CSRF protection. Serve the browser application and API through one public origin in production.

## Consequences

Logout and revocation are straightforward, secrets are not exposed to browser storage, and no identity vendor is required. Native/mobile or third-party API clients may later use a separately designed token flow without replacing the browser flow.
