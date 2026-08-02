# The CrowdSmarter

The CrowdSmarter is an AI-assisted organisational decision-intelligence platform. The product is the governed workflow; AI remains optional, replaceable, reviewable, and unable to make organisational decisions.

This repository contains the completed Phase 1 foundation, Phase 2 decision workflow, Phase 3 structured reasoning, Phase 3.1 invitation onboarding, Phase 4 human finalisation, and Phase 5 outcomes-and-learning vertical slices. It also contains the integrated public CrowdSmarter landing site, so the product and its public presence ship as one provider-neutral application.

## Implemented customer workflow

1. Visit the public site at `/` or sign in at `/login`.
2. Create an organisation and use its default Decisions workspace.
3. Invite people through secure, expiring, revocable links.
4. Frame a decision with clear ownership, scope, purpose, dates, and participant roles.
5. Compare options and record evidence, assumptions, and risks.
6. Collect immutable, versioned stakeholder positions.
7. Have an authorised human select the final option, explain the judgement, and address dissent.
8. Record the implementation commitment, accountable owner, success measures, and review date.
9. Document implementation and assess the actual outcome against evidence.
10. Capture reusable lessons, archive the completed learning cycle, and retrieve organisational knowledge through PostgreSQL full-text search.

Every material lifecycle command is attributable, transactionally validated, protected against stale pages, represented in immutable history, and appended to the tenant audit log.

## Implemented domains

- `accounts`: human identity and Django authentication;
- `organisations`: tenant boundary, memberships, roles, owner continuity, and safe offboarding;
- `invitations`: organisation-controlled onboarding, token rotation, expiry, revocation, and acceptance;
- `workspaces`: organisation-owned decision areas;
- `decisions`: framing, lifecycle policy, readiness, finalisation, and immutable transitions;
- `participants`: stakeholder roles with preserved history;
- `positions`: immutable, versioned stakeholder recommendations;
- `decision_options`: alternatives, benefits, trade-offs, and withdrawal;
- `evidence`: attributable sources, stance, and strength;
- `assumptions`: confidence, verification state, ownership, and retirement;
- `risks`: likelihood, impact, response, mitigation, ownership, and status;
- `reviews`: commitment, implementation, outcome assessment, evidence, and accountability;
- `lessons`: reusable organisational learning and archival gate;
- `search`: tenant-safe PostgreSQL full-text search across decision knowledge;
- `audit`: append-only material-change records;
- `core`: shared infrastructure and API exception translation.

## One integrated product and public site

The React application serves both surfaces:

- `/` — public CrowdSmarter landing page;
- `/app` — authenticated organisation list;
- authenticated decision, governance, outcomes, search, and audit routes.

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
docker compose --profile workers up -d worker
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

Upgrading an existing Phase 4 installation is documented in [the Phase 4 to Phase 5 Linux guide](docs/upgrading-phase-4-to-phase-5.md).

Start with [architecture](docs/architecture.md), [domain model](docs/domain-model.md), [permissions](docs/permissions.md), [decision workflow](docs/decision-workflow.md), [API](docs/api.md), [security](docs/security.md), [testing](docs/testing.md), and [developer onboarding](docs/developer-onboarding.md).
