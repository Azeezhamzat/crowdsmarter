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
| `evidence` | Attributable supporting and contradicting evidence |
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

No synchronous Phase 1–5 workflow requires Redis or Celery. Email delivery and future asynchronous work must be best-effort after durable PostgreSQL state is committed. A temporarily unavailable worker cannot invalidate a completed human workflow.

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
