# CrowdSmarter

Created by Azeez Adewale Hamzat.

CrowdSmarter is a free platform for a group to make decisions together in the
open: gather evidence, weigh options, and keep a record of who decided what
and why. Anyone can start a commons in minutes, with no invitation, no card,
and no sales call. The same platform runs participatory, evidence-linked
grant rounds for funders, from open call through judged review to a recorded
funding decision.

The approach draws on commons governance, participatory grantmaking, and
collective-intelligence research. AI assistance is optional, provider-neutral,
reviewable, and never makes the decision itself; a human always does.

## Two ways in

- **Start a commons, free.** Sign up, invite your group with one link, and
  run a decision from open contribution through to a recorded outcome. No
  institution or sales conversation required.
- **Run a guided grant round.** Funders and institutions can bring a funded
  round to run as a charter programme: eligibility, judged or blind review,
  disbursement, and a reusable template for the next round.

## What it does

- Guided decision templates (general decisions, grant rounds, idea
  competitions and hackathons, and open-ended "anticipatory commons" rounds),
  each with framing, ownership, scope, and participant roles set up front.
- Public Open Sessions where anyone can submit an idea, vote, and track their
  own application across rounds, without needing an account.
- Structured contribution: evidence, assumptions, risks, and immutable
  versioned stakeholder positions.
- Independent, optionally blind or anonymous evaluation rounds (scorecards,
  Delphi, approval, consent, ranked-choice), with minority reports preserved
  and reviewer conflicts of interest excluded transparently.
- Human-authorised final decisions: the platform structures evidence and
  deliberation, but never automates the judgement itself.
- Implementation tracking, outcome review, and reusable lessons feeding into
  the next decision.
- Systems and futures foresight: sourced signals, watchlists, systems
  canvases, scenario worlds, and adaptive signposts linked to real decisions.
- Grant-round specifics: eligibility screening, applicant-blind review,
  conflict-of-interest exclusion, budget rollups, disbursement (manual by
  default, Stripe-ready), and organisation verification (manual by default,
  Candid-ready).
- A personal work dashboard, an organisation decision portfolio, in-app
  notifications, and a small set of explainable decision-flow analytics.
- Organisation administration: invitations, membership history, ownership
  transfer, governed decision methods, and platform-wide tenant support.
- Available in English, French, and Portuguese.

Every material lifecycle action is attributable, transactionally validated,
recorded in immutable history, and appended to the tenant audit log.

## Domains

- `accounts`: identity, authentication, MFA, profile self-service, and
  self-serve signup;
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
- `foresight`: sources, STEEP signals, watchlists, systems canvases,
  scenarios, and adaptive signposts;
- `evaluations`: blind and peer-anonymous evaluation, Delphi rounds,
  ranked-choice voting, and constrained portfolio assessment;
- `decision_analysis`: comparative read models, contradiction and gap
  registers, and human-approved executive synthesis;
- `contributions`: named contributions, private drafts, review, and
  facilitation;
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
- `demo_requests`: rate-limited demonstration requests for funders and
  institutions;
- `audit`: append-only material-change records;
- `platform_admin`: service-wide oversight and governed tenant support;
- `core`: shared infrastructure and API exception translation.

## One integrated product and public site

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
