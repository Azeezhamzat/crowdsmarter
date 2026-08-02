# Phase 2 quality gate

## Customer value

- A customer can create a governed decision rather than an unstructured document.
- Decision purpose, boundaries, ownership, timing, and stakeholder responsibilities are explicit.
- The workflow prevents premature progression and preserves attributable history.

## Architecture

- Workspaces, decisions, and participants are separate Django domains in the modular monolith.
- Views and serializers remain thin; workflows live in transactional services.
- Lifecycle status cannot be patched directly, and unexpected command fields are rejected.
- Later lifecycle states are represented but not falsely enabled.

## Security

- Every selector scopes through active tenant membership.
- Cross-tenant reads return `404`.
- Every material write repeats service-level authority checks.
- Direct organisation foreign keys and parent-consistency validation protect tenant ownership.
- Browser writes retain session authentication and CSRF protection.

## Data integrity

- One default workspace per organisation.
- Workspace slugs are tenant-unique.
- Decision owners and participants are active organisation members when assigned.
- Offboarding blocks unfinished decision owners and soft-removes ordinary assignments with audit history.
- One active owner participant exists per decision.
- Transition history is immutable and sequential.
- Participant removal is soft and attributable.

## Testing

- Every Phase 2 endpoint has API coverage.
- Workspace, decision, and participant permissions have role-matrix coverage.
- Business-rule tests cover framing, deadlines, stakeholders, stale commands, blocked later transitions, ownership, and soft removal.
- Frontend tests cover lifecycle visibility and domain-error presentation.
- An opt-in browser test covers organisation-to-decision creation and framing.

## Documentation

Architecture, domain model, permissions, API, workflow, testing, and the staged lifecycle rationale are documented.

## Remaining verification

The artifact environment must not be treated as a substitute for CI. The complete networked verification command is `./scripts/verify.sh`.
