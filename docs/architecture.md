# Architecture

## Purpose

The CrowdSmarter is a governed organisational decision workflow. The architecture optimises for customer trust, explicit business rules, tenant safety, and long-lived maintainability. AI remains an optional, replaceable supporting capability; it is not the organising abstraction of the product and it has no pathway to make or finalise an organisational decision.

## System shape

The product is a **modular monolith**:

- one Django deployment unit;
- one PostgreSQL database;
- business domains expressed as Django apps;
- one React application that serves both the public CrowdSmarter site and authenticated product routes;
- Redis and Celery only for optional asynchronous work;
- no microservices, paid identity provider, external search engine, or mandatory cloud service.

This remains the preferred shape until measured operational constraints justify something more complex.

## Implemented domain boundaries

| App | Responsibility |
|---|---|
| `accounts` | Human identity and Django authentication |
| `organisations` | Tenant boundary, accepted memberships, roles, and tenant-safe reads |
| `invitations` | Organisation-controlled onboarding, delivery, expiry, revocation, rotation, and acceptance |
| `workspaces` | Organisation-owned containers for coherent groups of decisions |
| `decisions` | Framing, lifecycle policy, state, immutable transitions, and immutable human finalisation |
| `participants` | Explicit stakeholder roles and participation history |
| `positions` | Immutable, versioned stakeholder recommendations and authority coverage |
| `decision_options` | Alternatives and their lifecycle |
| `foresight` | Source intelligence, systems mapping, scenarios, wind-tunnelling, signposts, and decision relevance links |
| `evaluations` | Blind collective evaluation, minority reports, constrained portfolio assessment, and authority selections |
| `evidence` | Attributable supporting and contradicting evidence linked to structured sources |
| `assumptions` | Explicit assumptions, verification state, ownership, and retirement |
| `risks` | Risk assessment, response, ownership, and status |
| `reviews` | Commitment, implementation, outcome assessment, and accountable ownership |
| `lessons` | Reusable organisational learning and the archive gate |
| `search` | Tenant-safe PostgreSQL full-text retrieval across decision knowledge |
| `audit` | Append-only attributable records and manager-visible tenant audit reads |
| `core` | Cross-domain infrastructure primitives and API exception translation |

Notifications, analytics, and AI assistance are added only when their vertical slice begins.


## Integrated public site

The public website is not a separate system. React Router serves `/` as the public landing page and `/app` as the authenticated product entry point. Both surfaces share the same frontend build, deployment, domain, security headers, accessibility baseline, and design tokens. Public content is source-controlled and static by design; a CMS is not introduced before content-editing frequency demonstrates a need.

This choice avoids duplicated hosting, branding drift, cross-domain session complexity, extra recurring cost, and another deployment pipeline. It can later move behind a CDN or static host without changing the Django domain architecture.

## Write request flow

A material write follows an explicit path:

1. Django authenticates the server-side session and validates CSRF.
2. DRF rejects obvious unauthorised access.
3. A tenant-safe selector retrieves only records visible through an active membership.
4. A strict input serializer validates the API contract and rejects unknown fields.
5. A transactional service repeats material authorisation and enforces business rules.
6. Focused models persist domain state.
7. The same transaction appends domain history and audit events.
8. The view serialises the resulting state.

Serializers do not contain workflows. Views do not contain business rules. React consumes server-derived capabilities rather than inventing authoritative permission rules.

## Tenant isolation

Tenant isolation is layered:

- organisation and workspace querysets expose `for_user`;
- selectors scope every read through active organisation membership;
- cross-tenant resources return `404` to avoid existence disclosure;
- security-sensitive child records contain a direct organisation foreign key;
- model validation protects parent/tenant consistency;
- services repeat material authorisation for commands and future non-HTTP interfaces;
- tests exercise outsiders, suspended users, viewers, contributors, administrators, owners, decision owners, and designated decision makers.

PostgreSQL row-level security is not introduced yet. The current application-layer isolation is explicit, testable, and simpler to operate. RLS remains a future defence-in-depth option if regulation or operating scale justifies it.

## Decision aggregate

A decision is not a generic document with a mutable status. It consists of:

- an organisation and workspace boundary;
- a human owner and creator;
- explicit framing fields;
- the complete eleven-state lifecycle;
- participants with explicit responsibilities;
- structured options, evidence, assumptions, and risks;
- immutable, versioned stakeholder positions;
- one immutable human finalisation record;
- one accountable commitment, implementation, and outcome-review record;
- reusable lessons learned;
- immutable, sequenced transition history;
- append-only audit events.

Status is excluded from ordinary update serializers. Generic lifecycle transitions lock the decision row, check the caller's expected state, validate the next state, create an immutable transition record, update status, and append audit history atomically.

Finalisation is deliberately a separate command. It selects an active option, verifies required authority positions, requires a rationale and review confirmation, requires treatment of dissent when present, snapshots current positions, creates an immutable finalisation, and transitions the decision to `Decision Finalised` in one transaction. The generic transition endpoint cannot bypass this command.

## Stakeholder position design

A position is a participant's attributable recommendation at a point in time. It snapshots the participant role held at submission. Revisions create a new version; earlier versions are never overwritten. The current-position selector returns only the latest version for each active eligible participant, while the history endpoint preserves all versions.

This design avoids hidden edits, supports later outcome review, and preserves disagreement without converting judgement into an automatic score. See [ADR 0010](adr/0010-versioned-positions-and-human-finalisation.md).

## Governed lifecycle delivery

All required lifecycle states have existed since Phase 2, and Phase 5 now provides truthful supporting records for the complete lifecycle:

```text
Draft → Framing → Open for Contribution → Under Review
      → Ready for Decision → Decision Finalised → Commitment
      → Implementation → Outcome Review → Lessons Learned → Archived
```

`Under Review → Ready for Decision` uses the Phase 3 structured-reasoning gate. `Ready for Decision → Decision Finalised` uses the Phase 4 human-finalisation command. Phase 5 uses dedicated transactional commands for commitment, implementation, outcome review, lessons, and archival. The generic transition endpoint cannot bypass any governed stage.

## Authentication and browser security

The React client uses Django session authentication. The browser never stores bearer authentication tokens. Mutating requests send Django's CSRF token and credentials. Production exposes the frontend and API through one origin to preserve simple cookie and CSRF semantics.

Invitation secrets are different from authentication credentials. They are short-lived bearer secrets stored only as keyed digests and placed in the browser URL fragment so normal server and proxy logs do not receive them.

## Audit and history

Audit events are append-only at model and queryset levels. Decision transitions, stakeholder position versions, and the finalisation record are independently immutable because they form part of the customer-owned decision aggregate.

Organisation owners and administrators may read the newest 100 tenant audit events through a tenant-isolated API. Application immutability is not a substitute for database access control; production database users should not receive broad ad-hoc write access.

## Background work and graceful degradation

No synchronous Phase 1–6 workflow requires Redis or Celery. Email delivery and future asynchronous work must be best-effort after durable PostgreSQL state is committed. A temporarily unavailable worker cannot invalidate a completed human workflow.

## Storage and search

Development uses local filesystem storage through Django's storage abstraction. Production may select any S3-compatible provider by configuration. PostgreSQL remains the initial search engine. A separate search or vector system requires demonstrated relevance, latency, or scale limitations and an ADR.

## Observability

The application provides structured logs plus independent liveness and readiness endpoints. Initial production can use container logs and host metrics without licence cost. Future tracing or error aggregation must remain replaceable.

## Upgrade paths

| Initial operation | Upgrade without domain rewrite |
|---|---|
| Single Docker host | Multiple application containers behind a load balancer |
| Container PostgreSQL | Any managed PostgreSQL service via `DATABASE_URL` |
| Local media | S3-compatible object storage via `STORAGES` |
| No worker | Redis plus one or more Celery workers |
| PostgreSQL search | Dedicated index fed from durable domain state/events |
| One configured AI adapter | Multiple adapters selected by policy |
| Static Nginx frontend | Any static host or CDN |

Kubernetes is not a planned milestone. It becomes relevant only if evidence justifies its operating cost.

## Search architecture

Phase 5 uses PostgreSQL full-text search with weighted vectors and web-style queries. Search is scoped only after active organisation membership is established and returns decisions, options, evidence, assumptions, risks, outcome records, and active lessons. No Elasticsearch, vector database, embedding provider, or external indexing service is introduced. The upgrade path is an indexed `SearchVectorField` maintained inside PostgreSQL if measured volume makes on-query vectors insufficient.

## Phase 6 advisory intelligence

Phase 6 adds three bounded domains without changing the modular-monolith shape:

| App | Responsibility |
|---|---|
| `notifications` | Private, recipient-scoped workflow messages and due-review delivery |
| `ai_assistance` | Provider-neutral advisory reviews, snapshots, provenance, and human disposition |
| `analytics` | Explainable tenant decision-flow and learning read models |

The configured AI provider is loaded behind an internal protocol. The default rules provider is synchronous, deterministic, local, and zero-cost. Provider execution produces a separate `AIReview`; it has no reference to mutation services and cannot alter customer decision records. A provider failure marks only the review as failed and does not invalidate the human workflow.

Notifications are durable PostgreSQL records. Workflow commands remain authoritative; notifications are a communication consequence, not a source of truth. The optional Celery Beat process creates due-review notifications daily, while the management command provides a worker-free operational path.

Analytics are calculated from existing PostgreSQL records and include definitions in the API response. They are descriptive measures, not automated judgements of decision quality or employee performance.

## Phase 7 operational read and collaboration boundaries

The `collaboration` app owns append-only decision discussion and resolution commands. It uses notification and audit services through explicit calls but does not alter the structured reasoning or lifecycle aggregates.

The `portfolio` app contains no models. It is a read-side composition layer over tenant-safe domain records. Its outputs may evolve for usability without changing lifecycle commands or creating a second source of truth.

## Phase 8 product-experience boundaries

Built-in decision templates live in `apps.decisions.templates` as versioned code-owned prompt sets. They are not customer data, AI output, or hidden workflow automation. The create command validates a stable template key and persists only the fields explicitly submitted by the human creator. The key is retained for provenance.

The decision overview lives in `apps.decisions.overview` as a read-side composition over existing tenant-scoped records. It derives next-action guidance, framing coverage, stakeholder coverage, unresolved discussion, option counts, evidence/risk relationships, material risks, and target-date state. It does not call workflow mutation services and is not a second source of truth.

The React decision workspace consumes that overview to prioritise one next action and progressively disclose detailed controls. Business rules remain in Django services; the client cannot infer or bypass lifecycle gates.

## Phase 10 account and export boundaries

Account recovery remains inside `accounts` because it is an identity workflow using Django's password-validation and token primitives. The browser never receives authority beyond setting the password for the token-bound user.

`exports` is a read-and-package domain. It imports tenant-scoped records from existing apps, serialises them into a documented versioned schema, and returns private ZIP responses. It does not own customer records, mutate decision state, or introduce a repository abstraction. Synchronous generation is replaceable behind the service boundary when real archive size justifies streaming or background delivery.


## Phase 11 foresight and source-intelligence boundaries

The `foresight` app owns source records, private source attachments, manually synchronised RSS/Atom subscriptions, signals, watchlists, and explicit signal-to-decision relevance. It does not own decisions, evidence judgements, scenarios, or lifecycle transitions.

A source is an attributable observation input. A signal is a human interpretation of potential future significance. Feed synchronisation creates unassessed source records only; it never creates signals or claims strategic meaning automatically.

Private files use Django's storage abstraction. Development uses the local media volume; production can use any private S3-compatible backend without changing the domain model. File names are generated from tenant, source, and attachment identifiers. Downloads always pass tenant membership checks and use private, no-store responses.

Feed retrieval is deliberately manual and bounded. It rejects credentials, redirects, private and local IP ranges, oversized responses, and unsafe XML entities. Production retrieval is disabled unless `FORESIGHT_FEED_ALLOWED_DOMAINS` is configured. Core workflows remain available when a feed or the network is unavailable.

Foresight remains evidence about possible change rather than prediction. Impact, uncertainty, maturity, horizon, polarity, and credibility are explicit human assessments. Linking a signal to a decision records relevance; it does not alter options, advance lifecycle state, or grant decision authority.

## Phase 12 systems-foresight boundaries

The `foresight` app also owns structured systems canvases and their interpretation records. Visual maps are read models over governed relational records; browser coordinates and free-form shapes are not the source of truth. Strategic implications may reference decisions, but only the `decisions` app controls decision status, authority, and finalisation.


## Phase 13 scenario-intelligence boundaries

Scenario sets, scenario worlds, driver states, reviews, wind-tunnel assessments, signposts, and observations remain in `foresight` because they transform the same canvas evidence into governed strategic interpretations. The app may reference a decision and its active options but cannot mutate options, select an outcome, or advance the decision lifecycle.

## Phase 14 collective-evaluation boundaries

The `evaluations` app owns decision-linked evaluation exercises and organisation-level prioritisation portfolios. It reads decisions, options, participants, memberships, and organisation boundaries through explicit relations and selectors. It does not own decision authority, lifecycle state, budgets, implementation commitments, or forecasts.

Blind and peer-anonymous behaviour is enforced in selectors and serializers as well as the React interface. Aggregates and recommendations are derived read models. A separate `PortfolioSelection` record captures accountable human authority so the analytical recommendation can never be mistaken for an organisational decision.

## Phase 15 integrated analysis boundary

The `decision_analysis` app is a bounded synthesis domain. Its workspace read model composes active options, evidence, assumptions, risks, current positions, linked signals and implications, scenario wind-tunnel assessments, closed collective-evaluation results, and published minority reports. It does not copy those records, become their owner, or expose mutation commands for them.

Only three records are authoritative inside the app: governed analysis issues, versioned decision-quality reviews, and versioned executive summaries. Issue workflows are transactional and attributable. Review publication and summary approval supersede earlier published or approved versions without erasing them. Draft synthesis is authority-scoped and cannot leak through list endpoints or the integrated read model.

The read model intentionally uses explainable descriptive calculations. It does not infer the preferred option, calculate a universal decision-quality score, or call lifecycle services. See [ADR 0027](adr/0027-integrated-analysis-remains-read-only-and-human-governed.md).

## Phase 15.1 public acquisition boundary

The public site remains part of the same React build and security envelope as the application. The `demo_requests` app is intentionally separate from organisations: a prospect is not a tenant, and submitting a form cannot create an account or membership. Django admin provides the initial zero-cost operational review surface. A CRM integration requires demonstrated volume and a new ADR.

Authentication uses a dedicated case-insensitive email backend. First-run and repair commands are operational tooling, not web endpoints, and are disabled outside local debug settings.

## Phase 16 contribution-orchestration boundary

The `contributions` app owns decision-scoped requests, saved and submitted revisions, review records, facilitation sessions, participant attendance, and per-organisation delivery preferences. It depends on decisions, participants, organisations, notifications, and audit through explicit selectors and services. Decision lifecycle policy remains in `decisions`; contribution services cannot finalise or transition a decision.

Read access begins with a tenant-visible decision. Write capabilities are derived server-side from current membership, participant role, request ownership, reviewer assignment, and decision status. Celery invokes reminder and digest services, but assignment, drafting, submission, and review are synchronous and remain available when workers or Redis are unavailable.

## Phase 17 organisation-methodology and administration boundary

`methodology` owns organisation-defined method identity, version governance, approval, retirement, and immutable decision usage. It does not own decision outcomes or lifecycle transitions. `organisations` owns customer profile, branding, invitation policy, membership history, ownership transfer, deactivation, and delayed deletion requests. Cross-domain writes occur through explicit services; APIs remain thin and tenant selectors return 404 for inaccessible objects.
