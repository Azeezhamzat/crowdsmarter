# CrowdSmarter

Created by Azeez Adewale Hamzat.

CrowdSmarter is a facilitation-led practice for groups making consequential
decisions together. It helps people frame the decision, bring the right
participants and evidence into the room, work through disagreement, and reach
an accountable outcome.

A supporting platform is one part of that work. It keeps evidence,
participation, judgement, commitments, and outcomes connected, and can support
participatory grant rounds from open call through review to a recorded funding
decision. The platform serves the facilitated process; it is not the whole of
CrowdSmarter.

The approach draws on commons governance, participatory grantmaking, and
collective-intelligence research. AI assistance is optional, provider-neutral,
reviewable, and never makes the decision itself; a human always does.

## How CrowdSmarter can help

- **Facilitate a collective decision.** Shape a process around the decision,
  the people affected, the available evidence, and where authority sits.
- **Run a facilitated grant round.** Apply the approach to eligibility,
  judged or blind review, funding decisions, and learning for the next round.
- **Use the supporting platform where it adds value.** Keep contributions,
  evidence, disagreement, decisions, and follow-through connected without
  allowing the software to dictate the process.

The working service definition is in
[`docs/facilitation-offer.md`](docs/facilitation-offer.md). The evidence plan
for testing its need and usefulness is in
[`docs/facilitation-validation-plan.md`](docs/facilitation-validation-plan.md).
The current internet-research method and dated product baseline are in
[`docs/research/`](docs/research/).
The capability maturity bar and ordered upgrade workstreams are in the
[`global competition programme`](docs/global-competition-programme.md).
Reusable discovery and pilot records are in
[`docs/facilitation-field-kit/`](docs/facilitation-field-kit/README.md).

## What the facilitation and platform support together

- Guided decision templates (general decisions, grant rounds, idea
  competitions and hackathons, and open-ended "anticipatory commons" rounds),
  each with framing, ownership, scope, and participant roles set up front.
- Public Open Sessions where anyone can submit an idea, vote, and track their
  own application across rounds, without needing an account.
- Structured contribution: evidence, assumptions, risks, and immutable
  versioned stakeholder positions.
- Hybrid facilitation delivery: explicit influence boundaries, timed
  run-of-show activities, live facilitator prompts, agenda-linked outputs,
  accessibility and consent preparation, in-person and remote capture
  channels, participant-input provenance, missing perspectives, confidential
  or anonymous attribution, post-session quality review, authority responses,
  and print-ready session reports.
- Independent, optionally blind or anonymous evaluation rounds (scorecards,
  Delphi, approval, consent, ranked-choice), with minority reports preserved
  and reviewer conflicts of interest excluded transparently.
- Human-authorised final decisions: the platform structures evidence and
  deliberation, but never automates the judgement itself.
- Implementation tracking, outcome review, and reusable lessons feeding into
  the next decision.
- Systems and futures foresight: sourced signals, watchlists, systems
  canvases, scenario worlds, and adaptive signposts linked to real decisions.
- Decision-grade internet research: scored claims, supporting and contrary
  sources, limitations, reversal conditions, review dates, and explicit
  build/integrate/defer/avoid/monitor recommendations.
- Grant-round specifics: eligibility screening, applicant-blind review,
  conflict-of-interest exclusion, budget rollups, disbursement (manual by
  default, Stripe-ready), and organisation verification (manual by default,
  Candid-ready).
- A personal work dashboard, an organisation decision portfolio, in-app
  notifications, and a small set of explainable decision-flow analytics.
- Organisation administration: invitations, membership history, ownership
  transfer, governed decision methods, and platform-wide tenant support.
- English is the current product language. French and Arabic localisation
  infrastructure is retained but not exposed while its need and complete scope
  are evaluated.

Every material lifecycle action is attributable, transactionally validated,
recorded in immutable history, and appended to the tenant audit log.

## Domains

- `accounts`: identity, authentication, MFA, verified email changes, profile
  self-service, and self-serve signup;
- `organisations`: tenant boundary, invitations, memberships, ownership, and
  deactivation/deletion safeguards;
- `invitations`: organisation-controlled onboarding with expiring, revocable
  links;
- `workspaces`: organisation-owned decision areas;
- `decisions`: guided templates, framing, lifecycle policy, and immutable
  transitions;
- `criteria`: standalone decision criteria, weighting, and rationale;
- `participants` / `positions`: stakeholder roles and immutable, versioned
  recommendations;
- `decision_options`: alternatives, eligibility, outcomes, and budget;
- `ideation`: public Open Sessions for idea submission, voting, and
  competition/hackathon entries, including guardian consent and team
  submissions;
- `applicants`: a persistent, passwordless identity for people applying
  across multiple rounds, and their cross-round application history;
- `foresight`: source provenance, research claims, STEEP signals, watchlists,
  systems canvases, scenarios, and adaptive signposts;
- `evaluations`: blind and peer-anonymous evaluation, Delphi rounds,
  ranked-choice voting, and constrained portfolio assessment;
- `decision_analysis`: comparative read models, contradiction and gap
  registers, and human-approved executive synthesis;
- `contributions`: named contributions, private drafts, review, live hybrid
  facilitation run-of-show, attributable records, and authority feedback loops;
- `disbursements`: pluggable payout providers for funded grant options;
- `org_enrichment`: pluggable organisation lookup and verification;
- `billing`: packaging tiers and per-organisation subscription limits;
- `methodology`: organisation-owned decision methods and version provenance;
- `evidence` / `assumptions` / `risks`: attributable supporting material;
- `reviews` / `lessons`: implementation, outcome assessment, and reusable
  learning;
- `search`: tenant-safe PostgreSQL full-text search;
- `notifications`: private in-app assignments and lifecycle updates;
- `ai_assistance`: provider-neutral, dismissible advisory reviews;
- `analytics`: explainable decision-flow and learning metrics;
- `collaboration`: append-only discussion, mentions, and resolution;
- `portfolio`: personal work and organisation portfolio read models;
- `exports`: organisation archives and portable decision dossiers;
- `demo_requests`: rate-limited decision and facilitation enquiries from
  prospective partners (the internal name is retained for compatibility);
- `audit`: append-only material-change records;
- `platform_admin`: service-wide oversight and governed tenant support;
- `core`: shared infrastructure and API exception translation.

## One supporting application and public site

The React application serves both surfaces:

- `/` - public CrowdSmarter landing page, with self-serve signup;
- `/app` - authenticated organisation list;
- authenticated foresight, portfolio, decision, collaboration, governance,
  outcomes, search, notifications, analytics, advisory review, export, and
  audit routes.

The same build, container, domain, and security headers serve both. A
separate static marketing site also lives in this repository, at
`standalone-site/`, for deployments that want the public page decoupled from
the application build.

## Zero-cost local operation

```bash
cp .env.example .env
docker compose up -d --build
```

Open `http://localhost:5173`.

Configure the existing official administrator account:

```bash
docker compose exec backend python manage.py ensure_platform_admin \
  --email hello@crowdsmarter.com \
  --technical-admin \
  --demo-organisations
```

Set or change its password separately:

```bash
docker compose exec backend python manage.py changepassword hello@crowdsmarter.com
```

Redis and Celery remain optional for synchronous workflows:

```bash
docker compose --profile workers up -d worker scheduler
```

Optional local monitoring (Grafana at `http://localhost:3000`) is started with:

```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml \
  --profile observability up -d
```

Operational and security drills:

```bash
./scripts/backup-restore-drill.sh
docker compose exec backend python manage.py retention_report --json
docker compose exec backend python manage.py scan_source_attachments
docker compose exec backend python manage.py check_malware_scanner
docker compose exec backend python manage.py check_email_configuration
```

See `docs/operations/` for the monitoring, malware, restore, and email
runbooks. `docs/internal-security-privacy-review-2026-08-30.md` records the
remaining external review and production-evidence requirements.

## Quality commands

```bash
make test
make lint
./scripts/verify.sh
```

## Repository layout

```text
backend/          Django modular monolith and REST API
frontend/         Integrated public site and authenticated React application
standalone-site/  Decoupled static marketing page (no build step)
docs/             Architecture, permissions, workflow, API, security, and ADRs
.github/          Continuous integration and dependency updates
```

## Production path

The backend and frontend are provider-neutral OCI containers. PostgreSQL,
SMTP, Redis, and S3-compatible object storage are configured through
environment variables. Moving from a free or self-hosted server to managed
infrastructure changes deployment configuration rather than domain code.

New to the product itself, not the code? Read the
[master manual](docs/master-manual.md) first - it walks through using
CrowdSmarter as an organisation member and as a platform administrator, in
plain language.

For implementation detail, start with [architecture](docs/architecture.md),
[domain model](docs/domain-model.md), [permissions](docs/permissions.md),
[decision workflow](docs/decision-workflow.md), [API](docs/api.md),
[security](docs/security.md), [testing](docs/testing.md), and
[developer onboarding](docs/developer-onboarding.md). Release-by-release
upgrade notes and quality gates live in `docs/`.

## License

All rights reserved. See [LICENSE](LICENSE). This code is not open source;
being able to view this repository does not grant permission to use, copy,
modify, or distribute it. Contact hello@crowdsmarter.com for licensing
inquiries.
