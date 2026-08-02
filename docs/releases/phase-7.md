# Phase 7 release notes

## Purpose

Phase 7 makes The CrowdSmarter usable as a daily organisational work system rather than only a sequence of structured forms. It adds accountable collaboration and portfolio-level visibility without introducing chat-style decision making, hidden automation, or paid infrastructure.

## Delivered

- A personal **My work** dashboard across all organisations.
- Explainable next actions based on lifecycle state and the user's accountable role.
- Due-date and overdue indicators covering contribution, target-decision, and outcome-review dates.
- An organisation decision portfolio with lifecycle, urgency, text, personal-work, and overdue filters.
- Portfolio measures for active decisions, overdue work, and unresolved questions or concerns.
- Append-only decision notes, questions, concerns, updates, and replies.
- Focused mentions limited to active organisation members.
- Explicit resolution records for questions and concerns without rewriting the original contribution.
- Collaboration notifications for mentions, replies, material questions, concerns, and resolutions.
- A combined decision activity view sourced from discussion and material audit events.
- Tenant-isolation, observer restrictions, archived-decision read-only behaviour, permission tests, and migration checks.

## Governance guarantees

- Discussion is not a substitute for the structured decision record.
- Contributions are attributable and cannot be silently edited or deleted.
- Only active non-observer participants or organisation managers may contribute.
- Only the decision owner or organisation managers may resolve questions and concerns.
- Resolution adds an attributable record; it never alters the original wording.
- Archived decisions remain readable and cannot receive new contributions or resolutions.
- Portfolio information never crosses an organisation membership boundary.

## Zero-cost operation

Portfolio views are PostgreSQL queries over existing records. Collaboration uses the existing database, audit log, and in-app notification infrastructure. No chat service, search cluster, realtime broker, hosted analytics platform, or paid integration is required.

## Deliberately not claimed as complete

Phase 7 does not make the platform commercially complete. Account recovery, customer-controlled exports, secure evidence attachments, reusable decision templates, optional email digests, accessibility certification, and public-production operations remain explicit subsequent gates.
