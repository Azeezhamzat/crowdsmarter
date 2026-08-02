# Phase 2 release notes

## Delivered

- organisation-owned decision workspaces, including one default workspace per tenant;
- governed decision creation and framing;
- explicit decision ownership and transactional ownership transfer;
- named participant roles with soft removal and restoration;
- the full eleven-state decision lifecycle contract;
- enabled progression from Draft through Under Review;
- immutable, sequenced, human-authorised transition history;
- optimistic stale-state protection and attributable audit events;
- strict command payload validation;
- tenant-safe member offboarding across decisions and participants;
- React workspaces, decision framing, participants, lifecycle, and history interfaces;
- same-origin, configurable Nginx production routing;
- backend, API, permission, frontend component, and opt-in browser tests;
- architecture, API, permission, workflow, security, deployment, testing, and ADR documentation.

## Deliberately deferred

Phase 3 will introduce decision options, evidence, assumptions, and risks. The transition from Under Review to Ready for Decision remains blocked until those records and their business rules exist. No AI, notifications, external search engine, vector database, paid identity provider, or mandatory worker dependency has been introduced.

## Upgrade notes

1. Install backend and frontend dependencies.
2. Run `python manage.py migrate` before starting the updated application.
3. Run `./scripts/verify.sh`.
4. Commit the generated frontend lockfile after the first successful install.
5. For the production frontend image, set `BACKEND_UPSTREAM` when the backend is not reachable as `backend:8000`.
