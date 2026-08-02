# Phase 3 release: Structured reasoning

## Customer outcome

Teams can now turn a framed decision into a reviewable body of organisational reasoning. Alternatives, evidence, assumptions, and risks are captured as explicit records rather than being buried in chat or free-form documents.

## Included

- decision options with benefits, trade-offs, status-quo designation, and withdrawal;
- evidence with source type, reference, optional URL, stance, and strength;
- assumptions with confidence, verification status, accountable owner, review date, and retirement;
- risks with likelihood, impact, transparent score, response strategy, mitigation, owner, review date, and status;
- structured-review navigation in the React application;
- permission-aware create and edit capabilities;
- append-only audit events for material changes;
- readiness counts and blockers on the decision workspace;
- governed transition from `Under Review` to `Ready for Decision`;
- offboarding safeguards for active assumption and unresolved risk ownership;
- API, service, model, permission, lifecycle, frontend, and end-to-end regression tests;
- a corrective migration that aligns inherited Django account-field metadata without changing user data.

## Deliberately excluded

- automatic option ranking or recommendation;
- AI-generated records or silent AI edits;
- stakeholder positions;
- decision finalisation;
- outcome reviews and lessons learned;
- Elasticsearch, vector databases, or paid infrastructure.

These belong to later vertical slices and are not required to deliver the Phase 3 customer value.

## Upgrade behaviour

The release adds four Django apps and their initial migrations, plus a metadata-only account migration that resolves the warning carried from Phase 2. Existing users, organisations, memberships, workspaces, decisions, participants, and audit history remain in place. Running `python manage.py migrate` creates the new tables; Docker Compose performs this automatically when the backend starts.

A beginner-oriented Linux upgrade sequence is provided in [upgrading-phase-2-to-phase-3.md](../upgrading-phase-2-to-phase-3.md).
