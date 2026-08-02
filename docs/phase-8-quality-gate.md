# Phase 8 quality gate

Phase 8 is complete only when the following behaviour is verified.

## Guided creation

- The template catalogue requires authentication.
- Every template has a stable key, explicit version, human-readable purpose, prompts, and checklist.
- Unknown template keys are rejected.
- Guided creation persists only fields explicitly submitted by the user.
- The created record remains in Draft.
- The selected template key is attributable through the decision and audit event.
- Existing API clients can still create a minimal blank draft.

## Decision overview

- A user cannot retrieve another tenant's overview.
- The next action reflects the current lifecycle and visible blockers.
- Framing completeness is derived from persisted records.
- Participant, unresolved-discussion, option, and risk summaries are accurate.
- The overview endpoint performs no writes.
- Detailed workflow commands continue to enforce all transitions and permissions.

## Frontend

- A creator can move through all five guided steps using keyboard controls.
- Validation prevents an incomplete guided frame from being submitted.
- Templates are described as prompts rather than answers.
- The decision workspace presents one primary next action.
- Detailed controls remain accessible without overwhelming the first view.
- Mobile layouts preserve reading order and usable controls.

## Operations

- The Phase 7 database is backed up before source replacement.
- The existing `.env` and PostgreSQL volume are preserved.
- Migration drift checks pass.
- Focused backend and frontend tests pass.
- Production frontend build passes.
- The upgrade automatically restores Phase 7 source if validation fails.
