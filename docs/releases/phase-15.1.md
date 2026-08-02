# Phase 15.1 release — Public product experience and access reliability

Phase 15.1 is a stabilisation release over Phase 15. It does not add a new decision methodology. It improves the professional public experience, introduces a complete request-demo workflow, and removes avoidable local sign-in failure modes before contribution orchestration begins.

## Customer-facing changes

- The public homepage now communicates CrowdSmarter as the continuous intelligence chain from strategic sensing to accountable action and organisational learning.
- The visual hierarchy, product preview, responsive behaviour, trust explanation, and executive calls to action have been rebuilt without adding a third-party design system or marketing dependency.
- `Request a demo` is available from the header, hero, trust section, final call to action, footer, and sign-in page.
- `/request-demo` provides a focused, accessible form that captures the prospect's organisation, role, organisation size, primary need, and relevant decision challenge.
- A successful request receives a non-sensitive reference identifier and does not create an account or subscribe the person to marketing.

## Demo-request boundary

The new `demo_requests` Django app stores public requests separately from customer tenant records. Public submissions are:

- CSRF protected;
- strictly validated;
- rate limited;
- protected by a honeypot field;
- normalised before persistence;
- not linked to an organisation tenant;
- optionally forwarded to `DEMO_REQUEST_RECIPIENT` using the existing configurable email backend;
- retained for review through Django admin.

Email delivery is best effort. A notification failure cannot discard an already accepted request.

## Authentication reliability

- Email authentication now uses an explicit case-insensitive backend rather than relying on database collation or implicit backend keyword behaviour.
- Email values are trimmed and lower-cased in the browser, serializer, and authentication backend.
- The sign-in page presents actionable recovery guidance instead of exposing the raw generic API response.
- Caps Lock detection, password visibility control, password recovery, and invitation guidance are available without weakening generic credential errors.
- `ensure_local_owner` creates a secure first-run owner and starter organisation only when a local debug installation has no active account.
- `reset_local_password` and `scripts/reset-local-password.sh` allow secure local password repair without placing the password in shell history.

Both local management commands refuse to run when `DJANGO_DEBUG` is false.

## Deliberate non-goals

Phase 15.1 does not introduce self-service public registration, marketing automation, CRM integration, paid email infrastructure, customer billing, or production identity federation. Organisation access remains invitation governed.
