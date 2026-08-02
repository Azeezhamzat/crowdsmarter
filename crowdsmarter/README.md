# The CrowdSmarter

The CrowdSmarter is a foresight-to-decision-to-learning platform for organisations facing uncertainty. The product is the governed workflow; foresight broadens attention, collective intelligence strengthens reasoning, and AI remains optional, replaceable, reviewable, and unable to make organisational decisions.

This repository contains the Phase 1 foundation, Phase 2 decision workflow, Phase 3 structured reasoning, Phase 3.1 invitation onboarding, Phase 4 human finalisation, Phase 5 outcomes and learning, Phase 6 advisory intelligence, Phase 7 portfolio and collaboration, Phase 8 guided product-experience, Phase 9 professional-interface, Phase 10 account-trust and data-ownership, Phase 11 evidence-source and signal-intelligence, Phase 12 systems-foresight, Phase 13 scenario-intelligence, and Phase 14 collective-evaluation and prioritisation, Phase 15 integrated decision-analysis and executive-synthesis, Phase 15.1 public-experience and access-reliability, Phase 16 contribution-orchestration, and Phase 17 organisation-methodology and administration vertical slices. It also contains the integrated public CrowdSmarter landing site, so the product and its public presence ship as one provider-neutral application.

> **Corrective release:** Phase 17.1 supersedes the original Phase 17 package. It repairs frontend strict-mode/test regressions and a rollback controller that could continue after failure and print a false success message.
> **Public-route hotfix:** The repository also includes the validated Request Demo R4 frontend correction, including the `/request-demo` route, homepage conversion buttons, branded not-found experience, and compatible command-palette test.


## Implemented customer workflow

1. Visit the professional public site at `/`, request a tailored demonstration at `/request-demo`, or sign in at `/login`.
2. Create an organisation and use its default Decisions workspace.
3. Invite people through secure, expiring, revocable links.
4. Start from a guided, human-editable decision template and frame clear ownership, scope, purpose, dates, and participant roles.
5. Compare options and record evidence, assumptions, and risks.
6. Collect immutable, versioned stakeholder positions.
7. Have an authorised human select the final option, explain the judgement, and address dissent.
8. Record the implementation commitment, accountable owner, success measures, and review date.
9. Document implementation and assess the actual outcome against evidence.
10. Capture reusable lessons, archive the completed learning cycle, and retrieve organisational knowledge through PostgreSQL full-text search.
11. Use attributable advisory reviews to challenge gaps without changing records, receive in-app workflow notifications, and examine a small set of explainable decision-system metrics.
12. Work from a personal accountability dashboard, manage the organisation decision portfolio, and preserve questions, concerns, notes, replies, resolutions, and decision activity.
13. Use the coherent decision overview to see the next required action, framing gaps, stakeholder coverage, alternatives, material risks, deadlines, and readiness without losing access to the full record.
14. Work through a professional application shell with quick navigation, focused dashboards, responsive portfolio controls, and a consistent public and authenticated product identity.
15. Maintain profile and password security, recover account access, and download customer-owned organisation archives or portable decision dossiers.
16. Capture attributable sources and private attachments, interpret them as STEEP signals, organise strategic watchlists, monitor horizons and uncertainty, and link emerging change explicitly to decisions.
17. Build structured systems canvases with drivers, stakeholders, causal relationships, feedback loops, Futures Wheels, Three Horizons, and strategic implications linked to decisions.
18. Construct governed scenario worlds from critical uncertainties, collect structured reviews, wind-tunnel live decision options, and monitor adaptive signposts with sourced observations.
19. Run independent blind evaluation rounds, preserve minority reports, and prioritise candidate decisions transparently under budget and capacity constraints.
20. Compare each option through one traceable analysis workspace, govern contradictions and gaps, publish decision-quality reviews, and approve versioned executive summaries without automating the final judgement.
21. Convert prospective-customer interest through a privacy-conscious demo-request workflow and recover local access without introducing a production default credential.
22. Orchestrate named contribution requests, private drafts, immutable submissions, explicit review, facilitated sessions, reminders, digests, and participation coverage across distributed teams.
23. Govern organisation-owned decision methods, preserve exact version usage, administer tenant identity and invitation policy, transfer ownership, and use controlled deactivation and deletion safeguards.

Every material lifecycle command is attributable, transactionally validated, protected against stale pages, represented in immutable history, and appended to the tenant audit log.

## Implemented domains

- `accounts`: human identity, explicit case-insensitive email authentication, profile self-service, password changes, secure recovery, and debug-only local access repair;
- `organisations`: tenant boundary, profile and branding, invitation policy, memberships, append-only membership history, ownership transfer, deactivation, deletion safeguards, and safe offboarding;
- `invitations`: organisation-controlled onboarding, token rotation, expiry, revocation, and acceptance;
- `workspaces`: organisation-owned decision areas;
- `decisions`: guided templates, framing, overview read models, lifecycle policy, readiness, finalisation, and immutable transitions;
- `participants`: stakeholder roles with preserved history;
- `positions`: immutable, versioned stakeholder recommendations;
- `decision_options`: alternatives, benefits, trade-offs, and withdrawal;
- `foresight`: source intelligence, private attachments, safe RSS/Atom imports, STEEP signals, watchlists, systems canvases, drivers, stakeholders, causal relationships, feedback loops, Futures Wheels, Three Horizons, strategic implications, governed scenarios, wind-tunnel assessments, adaptive signposts, and decision links;
- `evaluations`: blind and optionally peer-anonymous decision evaluation, Delphi rounds, weighted criteria, minority reports, constrained portfolio assessment, recommendations, and authority selections;
- `decision_analysis`: option-centred read models, governed contradiction and gap registers, versioned decision-quality reviews, and human-approved executive synthesis;
- `contributions`: named decision contributions, private drafts, immutable submissions, append-only reviews, facilitation sessions, personal work, reminders, digests, and participation coverage;
- `methodology`: organisation-owned decision methods, governed versions, approval and retirement, and immutable decision usage provenance;
- `evidence`: attributable evidence linked to structured sources, stance, and strength;
- `assumptions`: confidence, verification state, ownership, and retirement;
- `risks`: likelihood, impact, response, mitigation, ownership, and status;
- `reviews`: commitment, implementation, outcome assessment, evidence, and accountability;
- `lessons`: reusable organisational learning and archival gate;
- `search`: tenant-safe PostgreSQL full-text search across decision knowledge;
- `notifications`: private in-app assignments, lifecycle changes, due reviews, and advisory-review updates;
- `ai_assistance`: provider-neutral, attributable, reviewable, and dismissible advisory reviews;
- `analytics`: small, explainable organisational decision-flow and learning metrics;
- `collaboration`: append-only decision discussion, mentions, replies, and explicit resolution;
- `portfolio`: personal work and organisation decision-portfolio read models;
- `exports`: versioned organisation archives and portable decision dossiers;
- `demo_requests`: rate-limited public demonstration requests, optional email notification, and administrative review;
- `audit`: append-only material-change records;
- `core`: shared infrastructure and API exception translation.

## One integrated product and public site

The React application serves both surfaces:

- `/` — public CrowdSmarter landing page;
- `/app` — authenticated organisation list;
- authenticated foresight, portfolio, decision, collaboration, governance, outcomes, search, notifications, analytics, advisory review, export, and audit routes.

The same build, Nginx container, domain, security headers, and deployment configuration serve both. No separate website, CMS, repository, or hosting account is required. Public content remains deliberately static and dependency-free until a demonstrated need justifies content management.

## Zero-cost local operation

```bash
cp .env.example .env
docker compose up -d --build
```

Open `http://localhost:5173`.

Create an administrator:

```bash
docker compose exec backend python manage.py createsuperuser
```

Redis and Celery remain optional for synchronous workflows:

```bash
docker compose --profile workers up -d worker scheduler
```

## Quality commands

```bash
make test
make lint
./scripts/verify.sh
```

## Repository layout

```text
backend/      Django modular monolith and REST API
frontend/     Integrated public site and authenticated React application
docs/         Architecture, permissions, workflow, API, security, and ADRs
.github/      Continuous integration and dependency updates
```

## Production path

The backend and frontend are provider-neutral OCI containers. PostgreSQL, SMTP, Redis, and S3-compatible object storage are configured through environment variables. Moving from a free or self-hosted server to managed infrastructure changes deployment configuration rather than domain code.

Upgrading an existing Phase 16 installation is documented in [the corrected Phase 16 to Phase 17.1 Linux guide](docs/upgrading-phase-16-to-phase-17.1.md). The remaining product-maturity gates are explicit in [the product maturity roadmap](docs/product-maturity-roadmap.md).

Start with [architecture](docs/architecture.md), [domain model](docs/domain-model.md), [permissions](docs/permissions.md), [decision workflow](docs/decision-workflow.md), [API](docs/api.md), [security](docs/security.md), [testing](docs/testing.md), and [developer onboarding](docs/developer-onboarding.md).

For GitHub publishing and repository-hygiene guidance, see [docs/github-publishing.md](docs/github-publishing.md).
