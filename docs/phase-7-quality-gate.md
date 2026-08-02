# Phase 7 quality gate

## Customer value

- Users can see accountable work across organisations without visiting every workspace.
- Managers can filter the organisation decision portfolio and see unresolved discussion work.
- Decision participants can preserve questions, concerns, notes, updates, replies, and resolutions.

## Business rules

- Discussion content is append-only.
- Only active non-observer participants or tenant managers may contribute.
- Only decision owners or tenant managers may resolve questions and concerns.
- Mentioned users must be active members of the same organisation.
- Archived decisions are read-only.
- Personal work is derived only from explicit ownership, participation, or implementation responsibility.

## Security

- Every selector establishes tenant access before reading records.
- Cross-tenant entry, activity, and portfolio identifiers return not found.
- Collaboration uses normal session authentication, CSRF protection, validation, and API throttling.
- Notifications are private to their recipient.

## Test requirements

- Model immutability and cross-decision reply validation.
- Service permission, mention, notification, audit, resolution, and archival tests.
- API tenant isolation and strict-input tests.
- Personal-work prioritisation and organisation-portfolio filter tests.
- Frontend dashboard, portfolio, discussion, and resolution rendering tests.
