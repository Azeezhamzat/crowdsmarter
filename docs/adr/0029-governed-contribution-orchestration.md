# ADR 0029: Govern contribution work without becoming a project-management or chat system

- Status: Accepted
- Date: 2026-08-01

## Context

CrowdSmarter already records evidence, assumptions, risks, positions, scenarios, evaluations, decisions, and outcomes. Distributed teams still need a reliable way to ask a named person for a bounded contribution, preserve unfinished work, review the submitted revision, and see whether important participant groups are represented. Informal email and chat cannot preserve this evidence-to-decision chain.

A general task board, document editor, or chat feed would duplicate mature external products and dilute the decision workflow. Contribution orchestration must therefore remain attached to a decision, attributable, status-governed, and auditable.

## Decision

Introduce a dedicated `contributions` Django app with four bounded concepts:

1. `ContributionRequest` records the decision, requested output, assignee, optional reviewer, due date, priority, optional option and facilitation-session links, and an explicit workflow state.
2. `ContributionSubmission` preserves one mutable draft per assigned author and immutable submitted revisions with monotonically increasing sequence numbers.
3. `ContributionReview` is append-only and records acceptance, return-with-guidance, or a review comment against a submitted revision.
4. `FacilitationSession` and `SessionParticipant` organise a structured workshop without introducing general calendars, calls, or chat.

The request state machine is:

`draft → open → in progress → submitted → under review → accepted`

A reviewer may return a submitted revision, producing `returned → in progress → submitted`. Accountable authorities may cancel non-terminal work. Submitted revisions and reviews remain immutable.

Assignments are limited to active, non-observer decision participants. Reviewers must be an authorised organisation manager or an active decision owner, decision maker, or reviewer. Tenant and decision relationships are validated transactionally.

The application provides an organisation-spanning personal inbox, due reminders, optional immediate/daily/weekly email delivery, and representation coverage. Email failure never rolls back a stored assignment. Celery and Redis improve delivery but are not required for synchronous contribution work.

## Consequences

- Decision teams gain explicit accountability without a separate task-management product.
- Draft privacy and submitted-revision history are enforceable server-side.
- Participation gaps become visible without reducing representation to a performance score.
- Existing decision, notification, audit, search, export, and offboarding boundaries remain authoritative.
- The phase does not create arbitrary tasks, recurring projects, time tracking, video meetings, or general-purpose messaging.
