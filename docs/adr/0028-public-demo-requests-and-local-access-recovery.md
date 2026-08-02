# ADR 0028 — Separate public demo requests from tenant data and keep local recovery debug-only

## Status

Accepted for Phase 15.1.

## Context

CrowdSmarter needs a credible public conversion path before customer pilots, but prospective-customer details are not customer-owned tenant records. The local Docker installation also needs a recoverable first-run path without creating a universal production credential or weakening authentication responses.

## Decision

1. Store demo requests in a dedicated `demo_requests` app with no organisation foreign key.
2. Accept submissions through one CSRF-protected, rate-limited, strict public endpoint.
3. Persist before optional email notification and never make an external email service a request dependency.
4. Keep organisation membership invitation-only.
5. Authenticate email addresses through an explicit case-insensitive backend.
6. Permit local account bootstrap and password repair only when `DJANGO_DEBUG=true`.
7. Create a local owner automatically only when no active account exists; never reset an existing active account during an upgrade.
8. Read repaired passwords from standard input so they do not appear in command history or process arguments.

## Consequences

- Public lead data has a clear privacy and retention boundary.
- The product can operate with the console email backend and zero recurring service cost.
- Production has no default password and no anonymous registration endpoint.
- Existing accounts are never silently modified by an upgrade.
- Local access failures have a deterministic repair path.
