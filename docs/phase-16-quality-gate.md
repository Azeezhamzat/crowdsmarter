# Phase 16 quality gate

Phase 16 is complete only when all requirements below pass on the upgrade target.

## Behaviour

- Accountable authorities can create draft or open contribution requests only for active non-observer decision participants.
- Assignees can save private drafts and submit immutable revisions.
- Named reviewers or accountable authorities can start review, comment, return, or accept submitted work.
- Returned work can be revised and resubmitted without rewriting earlier submitted revisions or reviews.
- Archived or otherwise non-writable decisions reject new contribution workflow commands.
- Facilitation sessions follow valid forward-only state transitions.
- Personal work includes both assigned contributions and explicitly assigned reviews.
- Participation coverage is descriptive and never changes decision authority.
- Reminder and email failures cannot corrupt or roll back stored work.

## Security and privacy

- Every selector establishes tenant-visible decisions before returning records.
- Cross-tenant assignees, reviewers, options, sessions, and participants are rejected.
- Draft request records are hidden from ordinary participants until opened.
- Draft submission content is hidden from unrelated participants.
- Submitted revisions and reviews are immutable.
- Unknown API command fields are rejected.
- Offboarding refuses removal while active contribution ownership, pending review responsibility, or facilitation responsibility remains.
- Local login provisioning is blocked outside debug mode and writes credentials with mode `0600`.

## Integration

- Contribution records appear in customer-owned organisation archives and decision dossiers.
- Open requests and facilitation sessions are searchable only within the active tenant.
- Material commands append audit events and appropriate private notifications.
- Decision and application navigation expose the workspace and personal inbox.
- Existing decision, evaluation, foresight, analysis, authentication, export, and public-demo regressions remain green.

## Engineering validation

- `python manage.py check` passes.
- `python manage.py makemigrations --check --dry-run` reports no drift.
- Focused backend service, API, permission, authentication-command, offboarding, notification, search, and export tests pass.
- Frontend TypeScript checking passes.
- Focused contribution, authentication, navigation, and decision-workspace Vitest tests pass.
- The Vite production build succeeds.
- Backend and frontend health checks pass after upgrade.
- A failed upgrade restores both Phase 15.1 source and the pre-upgrade PostgreSQL backup.
