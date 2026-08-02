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

## Phase 6 AI, notification, and analytics security

The default advisory provider performs local deterministic analysis and transmits no data externally. The provider configuration is an import path, and any future adapter must undergo privacy, data-residency, retention, credential, timeout, and error-redaction review before production use. Secrets are environment variables and are never persisted in `AIReview` output.

Each AI review stores a private source snapshot and SHA-256 fingerprint for attribution. The API deliberately excludes the snapshot to reduce unnecessary disclosure. Provider exceptions are logged server-side and customers receive a generic failure message. AI request throttling applies even when the default provider is free, protecting future adapters from accidental consumption.

Notification selectors filter by recipient, and analytics first establish active tenant membership. Internal notification URLs do not bypass the permissions of their destination. No behavioural-tracking SDK or external analytics collector is included.

## Collaboration and portfolio security

Decision discussion is tenant-scoped and requires the same session-authenticated, CSRF-protected API boundary as other commands. Mention identifiers are resolved only among active members of the decision organisation. Replies must reference the same decision. Archived decisions reject new entries and resolutions.

The organisation portfolio and My work dashboard are read models over records already visible to the current user. They do not create a broader authorisation scope and do not expose raw cross-tenant identifiers. Discussion content is append-only; explicit resolution records preserve the original concern or question.

## Phase 10 password-recovery threat model

Password-recovery responses do not disclose whether an email address exists. Reset tokens are generated by Django, are not persisted as reusable secrets, expire through `PASSWORD_RESET_TIMEOUT`, and become invalid when the password changes. Links place the user identifier and token after `#`, preventing the initial SPA request from sending them to Nginx or Django access logs. The browser sends them only to the dedicated CSRF-protected confirmation endpoint.

Production deployments must use HTTPS, a stable secret key, a configured email provider, and `DJANGO_DEBUG=false`. Local development may display the link in the response so the console backend remains usable at zero recurring cost.

## Phase 10 export threat model

The principal risks are cross-tenant disclosure, privilege escalation, secret leakage, browser caching, and unbounded generation. Tenant-safe selectors establish visibility before export. Complete tenant archives require owner or administrator authority. Passwords and invitation token digests are excluded by field name. Responses are private and no-store, generation is rate limited, and each download is audited.

The current synchronous implementation is deliberately bounded to pre-revenue scale. Large customer datasets should move to a background or streaming implementation with expiring private object downloads while preserving the same permission and schema contracts.

## Phase 11 source files and feed retrieval

Source attachments are private customer records. The upload workflow:

- removes directory components from the submitted file name;
- generates the storage path from organisation, source, and attachment UUIDs;
- enforces an environment-configurable maximum size;
- permits only an explicit extension and MIME allowlist;
- verifies basic file signatures before storage;
- stores the original display name, size, MIME type, and SHA-256 digest;
- rejects duplicate file content on the same source;
- audits upload and download actions;
- authorises every download against current tenant membership;
- returns `Cache-Control: private, no-store` and `X-Content-Type-Options: nosniff`.

The files are stored, downloaded, and exported; the application does not render office documents or extract archives. A production deployment should add asynchronous malware scanning before accepting untrusted external uploads at larger scale. Core decision workflows must remain available if scanning is unavailable.

RSS and Atom retrieval is a bounded administrative convenience rather than a web crawler. It:

- accepts only HTTP and HTTPS URLs without embedded credentials;
- rejects private, loopback, link-local, multicast, reserved, and unspecified IP addresses;
- disables redirects;
- limits responses to 2 MB and ten seconds;
- parses XML with `defusedxml`;
- uses conditional requests where feeds provide ETag or Last-Modified;
- requires `FORESIGHT_FEED_ALLOWED_DOMAINS` outside debug mode;
- is manually triggered and rate limited;
- creates unassessed sources, never interpreted signals.

DNS rebinding is a residual risk in standard library HTTP resolution. The production allowlist should contain only domains the operator trusts, and feed retrieval may be disabled entirely by leaving the allowlist empty.

## Phase 14 privacy and manipulation safeguards

Blind evaluation is enforced server-side. Open-round serializers return only the caller's contribution and never send hidden peer data to the browser. Peer anonymity is a presentation and ordinary-user access rule, not destructive anonymisation: the database retains the contributor for duplicate prevention, abuse investigation, audit, and customer-owned exports.

Method-specific ballot validation prevents semantically invalid votes. Tenant, decision, option, criterion, round, portfolio, and candidate relationships are checked in transactional services. Aggregate recommendations cannot transition decisions, allocate resources, or impersonate accountable authority. The constrained portfolio method is deterministic and explicitly labelled as an explainable heuristic rather than an optimal solution.

## Phase 15 synthesis security

Integrated analysis is assembled only after tenant-safe decision selection. Related records are filtered through the selected decision or organisation; client-supplied organisation identifiers are never trusted. Optional issue links are validated against the same decision, and ownership is restricted to active organisation members.

Draft decision-quality reviews and draft executive summaries may contain provisional or sensitive judgement. They are excluded server-side from list and workspace responses for non-authorities; hiding controls in React is not treated as access control.

The analysis read model has no mutation dependency on lifecycle services. Approval of an executive summary is an attributable content-governance event, not decision finalisation. Search indexes only governed issues and non-superseded summaries, and export generation remains tenant-authorised and private.

## Phase 15.1 public forms and local access

Public demo requests use CSRF protection, strict serializers, anonymous throttling, bounded fields, mandatory contact consent, and a hidden honeypot. No client IP, user-agent fingerprint, password, tenant identifier, or inferred profile is stored in the record. Optional notification email is sent only after the database transaction commits and cannot make submission availability depend on an email provider.

The API continues to return the same `Invalid email or password.` response for missing accounts, wrong passwords, and inactive accounts. The explicit email backend performs a case-insensitive lookup and Django-style timing mitigation. Local bootstrap and password-reset management commands are hard blocked unless `DJANGO_DEBUG=true`; no production default credential exists.

## Phase 16 contribution privacy and delivery

Contribution selectors begin from a decision visible to the authenticated user and never trust a client-provided organisation boundary. Services revalidate assignee, reviewer, option, session, and participant relationships inside a transaction. Submitted revisions and review records are immutable, preserving attribution and preventing silent rewriting after review.

Draft request records remain hidden until opened. Draft submission content is filtered server-side so unrelated decision participants cannot retrieve unfinished work. Search excludes draft requests. Customer exports remain tenant-authorised and include the full attributable history.

Email is optional. Immediate assignment email is attempted only after the request exists, and failure cannot roll back the request or in-app notification. Digest failure is logged and does not advance the delivery timestamp. Core contribution commands do not require Celery or Redis.

The Phase 16 local-login provisioning command is available only with `DJANGO_DEBUG=true`. It resets the explicitly requested account to a generated password, ensures an active membership, writes the secret to a mode-`0600` file, and never prints the password. Production deployments cannot invoke it.

## Phase 17 tenant-governance security

Draft methods and draft method versions are restricted to owners and administrators. Ordinary members receive not-found responses for direct draft-object access. Organisation deletion history is owner-only. Deactivation and deletion require exact confirmation strings, meaningful rationale, and transactional server-side checks.

The local Phase 17 provisioner never accepts or embeds the weak password `Admin1`. In debug mode it generates a strong temporary password for `hello@crowdsmarter.com`, writes it to a mode-`0600` file, and prints only the path. In production mode the command refuses to run.

## Governed support access

Platform authority is explicit and separate from Django technical flags. Safe global summaries do not expose full tenant records. Detailed tenant access requires a specific reason, limited scope, and expiry. Operational actions require the stronger support-access level and generate attributable audit events. Platform administrators are not silently inserted into real client memberships or decision records.
