# Launch readiness (Phase 29 capstone)

Written at the end of Phase 29, the final phase of the roadmap in
`docs/project/claude-code-master-prompt.md`. This is a snapshot of what is
genuinely production-ready in this codebase versus what is deliberately
deferred because it needs real external infrastructure or credentials this
sandbox does not have. It exists to stop "29 phases done" from being
misread as "ready to take real customer traffic and real money" — those are
different claims, and this document draws the line between them honestly.

## What is production-ready

- **Core decision-intelligence workflow** (Phases 1-18): foresight, options,
  evidence/assumptions/risk, criteria, Delphi-style evaluation, decision
  finalisation, implementation, outcomes and lessons, portfolio and
  executive views. Backed by 384+ backend tests and 36 frontend test files,
  all passing.
- **Multi-tenant governance**: organisation creation, membership roles,
  invitation flows, ownership transfer, deactivation, and a delayed,
  auditable deletion safeguard (never immediate deletion) — see
  `docs/domain-model.md` and `docs/permissions.md`.
- **Accessibility**: WCAG 2.2 AA audited across all routes (Phase 20.1).
- **Data portability**: JSON/CSV/XLSX export with content-hash integrity and
  print-ready facilitation reports that a browser can save as PDF,
  documented in ADR 0026 territory and `docs/api.md`.
- **Advisory AI assistance**: rule-based, provider-independent, always
  human-reviewable and dismissible, with an evaluation harness tracking
  correction rate (Phase 27). See `docs/ai-architecture.md`.
- **Account security**: session auth, CSRF protection, rate limiting,
  password reset, and TOTP-based MFA with backup codes (Phase 28).
- **Audit history**: `AuditEvent` is genuinely append-only (save/delete and
  queryset `.update()`/`.delete()` all raise) and every mutating service
  call records one.
- **Plan entitlements** (Phase 29, this phase): every organisation is
  auto-enrolled in a plan with a trial period; `Plan.max_active_decisions`
  and `Plan.max_active_members` are enforced server-side
  (`apps/billing/services.py::assert_can_create_decision` /
  `assert_can_add_member`), tested against a dedicated low-limit plan so the
  guard is proven to actually fire, not just proven not to break existing
  data. Owners can self-serve change plans and set a billing contact from
  Organisation administration.
- **CI**: `.github/workflows/ci.yml` runs backend lint/mypy/migration-check/
  test and frontend lint/typecheck/test/build on every push.

## What is deliberately deferred, and why

None of the items below are gaps in engineering quality — each was
evaluated and intentionally scoped out because doing it properly requires
an external provider, credential, or piece of infrastructure this sandbox
cannot exercise. Building a fake version of any of these would be worse
than not building it, because it would look real without being trustworthy.
The pattern across every phase that hit this (25, 26, 27, 28, 29) has been
the same: build the self-contained, testable core of the feature now, and
document exactly what a real integration needs to add later.

### Payment processing and real billing (ADR 0031)

Nothing in this codebase charges a card, calls a payment provider, or
issues an invoice. `apps.billing` models *packaging tiers and usage limits*
only. ADR 0031 (`docs/adr/0031-billing-and-subscription-strategy.md`) is
the design document for connecting a real provider (Stripe Billing is the
recommendation) later: it covers provider choice, subscription lifecycle,
trials, invoices, tax/VAT, usage-based billing, grace periods and failed
payments, refunds, webhook handling, and audit — all deferred, all with a
stated plan.

### SSO/OIDC/SAML and SCIM provisioning

Phase 28 built TOTP-based MFA (a real RFC 6238 implementation, verified
against official test vectors) because it needs no external identity
provider. Enterprise SSO (SAML/OIDC) and SCIM user provisioning need a real
IdP (Okta, Azure AD, Google Workspace) to integrate against and test — that
does not exist in this sandbox. `docs/known-issues.md` and the accounts app
are the place to pick this up when a real IdP is available for testing.

### Production infrastructure and observability

The repository now includes a locally testable Prometheus, Loki, Alloy,
Grafana, and Alertmanager profile, structured request logs, request metrics,
readiness probes, a provisioned dashboard, and baseline availability/error/
latency alerts. This is a real centralised local foundation, but its receiver
does not send external notifications and the built-in metrics collector is
process-local. A production rollout still needs a deployment target, private
telemetry networking, host/database/backup/certificate monitoring, a tested
on-call receiver, and multiprocess-aware metrics or per-instance scraping.
There is still no managed PostgreSQL, CDN, autoscaling, APM, or tracing.

### Public trust center and support operations

`LandingPage.tsx`'s `#trust` section and `PlatformConfiguration`'s
`support_email`/`privacy_email`/`security_email` fields are the current
surface area. A dedicated public trust center (status page, security
whitepaper, compliance attestations), a help center, and a ticketed support
flow are not built — they would either duplicate content that belongs in
real operational tooling (a status page needs a real uptime feed to be
honest) or need policy decisions (a compliance page asserting SOC 2 status
that isn't true is actively harmful) that are the account owner's to make,
not something to fabricate.

### Enquiry-to-engagement conversion

`apps.demo_requests` fully covers decision-enquiry capture and qualification
status, but it does not automatically turn a qualified enquiry into an
engagement or provision an organisation. That conversion remains a deliberate
human gate: someone reviews the decision context, completes a fit assessment,
and agrees the appropriate next step. This matches the project's principle of
not automating consequential account actions without a human decision.

## Recommended order if this goes to real production

1. Decide on a deployment target and write the ADR (`docs/deployment.md`
   already has groundwork).
2. Deploy the supplied observability foundation privately, add infrastructure
   and error tracking, and prove an alert reaches the on-call recipient.
3. Connect Stripe Billing per ADR 0031, extending `OrganisationSubscription`
   rather than replacing it.
4. Add SSO/SAML/SCIM once a target enterprise customer's IdP is available
   to integrate and test against.
5. Build the public trust center pages once there are real operational
   facts (uptime history, a real security contact rotation) to put on them.

## What this document is not

This is not a security audit, not a compliance attestation, and not a
guarantee of production stability under real load. It is an honest map of
what has been built and tested versus what still needs real-world
infrastructure this sandbox cannot provide.
