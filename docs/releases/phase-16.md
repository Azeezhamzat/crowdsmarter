# Phase 16 release: Contribution orchestration

Phase 16 makes CrowdSmarter operable across distributed decision teams. It introduces named, due-dated contribution requests; private saved drafts; immutable submitted revisions; explicit review and return states; facilitated sessions; reminders and digests; a personal contribution inbox; and participation-coverage indicators.

## Customer value

Decision owners no longer need to coordinate important evidence, risk, assumption, stakeholder, scenario, review, or implementation input through disconnected email and chat. Each request remains attached to the decision and can be traced through assignment, work, review, acceptance, audit, export, and later outcome learning.

## Included capabilities

### Governed requests

- decision-scoped requests with a named assignee;
- optional named reviewer, decision option, and facilitation-session links;
- evidence, assumption, risk, stakeholder, option, question, review, scenario, implementation, and other contribution types;
- low, normal, high, and critical priority;
- optional due dates and controlled pre-submission reassignment;
- draft, open, in-progress, submitted, under-review, accepted, returned, and cancelled states;
- explicit cancellation rationale and audit history.

### Drafts, submissions, and review

- one mutable draft for the assigned contributor;
- immutable, sequenced submitted revisions;
- append-only review records;
- acceptance, return-with-guidance, and review-comment outcomes;
- server-derived work, review, and management capabilities;
- draft content visible only to the assignee, named reviewer, and accountable authorities.

### Facilitation

- bounded decision workshops with an objective, agenda, guidance, facilitator, schedule, and invited participants;
- planned, open, closed, and cancelled states;
- invited, attended, and absent attendance records;
- outputs connected to named contribution requests rather than an ungoverned whiteboard.

### Personal and organisational operation

- cross-organisation contribution inbox for assignee and reviewer work;
- overdue, returned, submitted, and awaiting-review summaries;
- participation coverage and unassigned-participant visibility;
- optional immediate assignment email, daily digest, or weekly digest;
- configurable due reminders;
- Celery beat delivery that does not block the core synchronous workflow.

### Platform integration

- tenant-safe API selectors and strict command serializers;
- in-app notifications and material audit records;
- PostgreSQL full-text search for open requests and facilitation sessions;
- organisation archive and decision dossier export;
- offboarding protection for active assignees, pending reviewers, and live facilitators;
- professional responsive decision and personal-inbox interfaces.

## Deliberate exclusions

Phase 16 does not add general project boards, time sheets, video conferencing, generic team chat, unrestricted documents, employee-performance scoring, or automated allocation of work. Participation coverage is a workflow diagnostic, not a judgement of a person's value or productivity.

## Local access assurance

The Phase 15.1 to Phase 16 upgrader explicitly provisions or repairs the local debug account `owner@example.test`, ensures an active organisation membership, and writes a newly generated temporary password to an owner-readable file in `~/Downloads`. The password is never printed in terminal output and the command is unavailable when `DJANGO_DEBUG=false`.
