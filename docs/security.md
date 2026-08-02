# Security design and review checklist

## Implemented controls

- Django password hashing, validators, and server-side sessions;
- CSRF protection on login and every browser mutation;
- secure, HTTP-only session cookies and secure CSRF cookies in production;
- fail-fast production secret, host, origin, and database configuration;
- login and API throttling, with an optional shared Redis cache;
- active-membership tenant scoping before object retrieval;
- direct tenant ownership on security-sensitive child records with parent/tenant consistency validation;
- object-level role permissions and repeated service-layer authorisation;
- strict command serializers that reject unexpected or forbidden fields;
- lifecycle status changes only through locked, optimistic, human-authorised commands;
- immutable, sequenced lifecycle transitions;
- immutable, versioned stakeholder positions;
- immutable finalisation with a snapshot of current positions;
- generic lifecycle transitions cannot bypass option selection and finalisation;
- transactional protection of the last active organisation owner;
- offboarding protection for unfinished decision, active assumption, and unresolved risk ownership;
- generic login errors that do not disclose account existence;
- organisation-controlled registration with expiring and revocable invitation links;
- keyed invitation-token digests only—raw secrets are never stored in PostgreSQL;
- invitation secrets held in browser URL fragments and sent to Django only in a dedicated request header;
- invitation rotation invalidates earlier links, while acceptance rechecks issuer authority and email identity;
- `Cache-Control: no-store` on invitation inspection and acceptance responses;
- append-only audit events and manager-only tenant audit reads;
- read-only Django admin access to audited tenant-domain records;
- security headers, HTTPS redirect, HSTS, frame denial, content-type protection, and restrictive referrer policy;
- no mandatory external authentication, analytics, search, storage, or AI service.

## Trust boundaries

The public reverse proxy accepts browser traffic. Django is the policy enforcement point. PostgreSQL is the authoritative state store. Redis and Celery are optional and must never become the sole record of a completed human workflow. Static frontend code is untrusted input from the server's perspective; hiding a control in React is not authorisation.

## Human finalisation threat model

The principal risks are an unauthorised actor finalising a decision, stale pages overwriting newer state, selecting an option from another tenant or decision, omitting required decision authorities, silently erasing dissent, and later editing the result.

The implementation mitigates these risks by:

- resolving the decision through tenant-safe selectors;
- rechecking authority in a transactional service;
- locking the decision row and comparing `expected_status`;
- selecting only an active option from the same decision;
- deriving current positions from immutable versions;
- requiring every active decision owner and decision maker to have a current position;
- requiring explicit position-review confirmation;
- requiring dissent treatment when positions diverge from the selected option;
- creating finalisation, transition, and audit state atomically;
- preventing model and queryset update/delete operations on finalisation and positions.

Application-level immutability is not a substitute for least-privilege database accounts, protected backups, and controlled production administration.

## Invitation threat model

An invitation link is a bearer secret until the invited person authenticates or creates an account. The implementation uses 256-bit URL-safe randomness, a secret-keyed SHA-256 digest at rest, short configurable expiry, immediate revocation, rotation on resend, request throttling, CSRF protection on acceptance, and explicit email matching. Tokens are placed after the browser URL fragment marker (`#`) so the frontend server and reverse proxy do not receive them when serving the SPA.

An invitation is not a password-reset mechanism. If the invited email already belongs to an account, the person must sign in with that account before acceptance. Production deployments must keep `DJANGO_SECRET_KEY` stable because it keys stored token digests.

## Production actions before customer data

- conduct an independent application and deployment security review;
- verify HTTPS, proxy headers, cookie attributes, and host/origin configuration;
- establish least-privilege database and host accounts;
- test encrypted backup restoration;
- configure dependency and vulnerability update handling;
- add alerting for authentication abuse, repeated permission failures, server errors, and backup failures;
- define incident response, breach notification, retention, deletion, export, and legal-hold procedures;
- add malware/type/size validation before introducing file uploads;
- perform accessibility and browser security testing against the deployed origin.

## Future authentication

Enterprise SSO should integrate through Django-compatible standards and map identity into the same local user/membership model. It must not make tenant authorisation dependent on a paid identity vendor. API/mobile token authentication, if required, is a separate threat model and should not reuse browser token storage patterns.

## Public site and authenticated product boundary

The public landing page and authenticated application share one frontend build and origin. Public routes make no authenticated API calls. Protected routes still verify the Django session before rendering and preserve the requested destination through the sign-in redirect. This avoids cross-origin cookie configuration and keeps CSRF, session, content-security, and proxy behaviour consistent.

## Search privacy

Search establishes active tenant membership before constructing any query. Every searched model is filtered by the same organisation foreign key, and URLs point only to records that the authenticated user can subsequently retrieve through tenant-safe selectors. Search terms are not sent to an external index, model provider, analytics service, or vector store.
