# Phase 3 quality gate

## Customer value

- [x] Alternatives are explicit and comparable.
- [x] Evidence is attributable and can support, contradict, or remain neutral.
- [x] Assumptions expose uncertainty and verification state.
- [x] Risks expose likelihood, impact, response, mitigation, and accountability.
- [x] Readiness blockers are visible rather than hidden.

## Architecture

- [x] Each new business domain is a separate Django app.
- [x] Views remain thin and delegate workflows to services.
- [x] Serializers handle API validation rather than business workflows.
- [x] PostgreSQL remains the system of record.
- [x] No microservice or paid service was introduced.

## Human control and audit

- [x] AI is not required for any Phase 3 workflow.
- [x] Records are created and changed by attributable humans.
- [x] Lifecycle movement remains an explicit human command with rationale.
- [x] The platform never selects an option automatically.
- [x] Material writes generate audit events.

## Security and permissions

- [x] Tenant-isolated selectors scope every object lookup.
- [x] Managers and decision owners retain accountable control.
- [x] Participant roles govern contribution during the correct lifecycle stages.
- [x] Non-managers may edit only records they created or assumption/risk records they are explicitly accountable for, subject to participant role and lifecycle state.
- [x] Offboarding cannot strand active assumption or unresolved risk ownership.

## Test coverage supplied

- [x] Model-rule tests.
- [x] Service-workflow tests.
- [x] API tests.
- [x] Permission and tenant-isolation tests.
- [x] Lifecycle readiness tests.
- [x] Frontend component tests.
- [x] End-to-end structured-review coverage.

## Verification status

Static source validation was completed in the release environment. Full dependency-backed Django, PostgreSQL, TypeScript, browser, and migration-drift checks must run in the supplied CI or the user's Docker environment; see `VALIDATION.md`.
