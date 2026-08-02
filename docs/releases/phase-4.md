# Phase 4 release: Human decision governance

## Customer outcome

The CrowdSmarter now carries a governed decision from structured review through an explicit human final decision. Stakeholders can record attributable positions without overwriting earlier reasoning, decision authorities can see whether required positions are missing, and a final option cannot be selected without a reviewable rationale and treatment of dissent.

## Included

- immutable, versioned stakeholder position submissions with the participant role preserved at submission;
- support, conditional support, rejection of all options, and abstention;
- optional conditions and explicit confidence;
- current-position and complete-history APIs;
- position submission limited to active, eligible decision participants;
- mandatory current positions from every active decision owner and decision maker;
- human-only finalisation authority for the decision owner, designated decision makers, and organisation managers;
- active-option selection with optimistic status checking;
- mandatory final rationale and confirmation that stakeholder positions were reviewed;
- mandatory treatment-of-dissent record whenever current positions do not support the selected option;
- immutable finalisation record with a snapshot of the current stakeholder positions;
- atomic progression from `Ready for Decision` to `Decision Finalised`;
- append-only audit events for position submission, lifecycle progression, and finalisation;
- manager-only organisation audit log showing the newest 100 material actions;
- React governance and audit interfaces;
- backend model, service, API, permission, regression, component, and migration tests.

## Human judgement safeguards

- AI cannot create a position, select an option, or finalise a decision through any special pathway.
- The final option is selected only through a human-authenticated command.
- Position revisions append a new immutable version instead of silently rewriting the earlier record.
- The finalisation snapshot preserves what stakeholders said at the time of the decision.
- Dissent is not converted into a score or automatically resolved.
- Generic lifecycle transitions cannot bypass the finalisation command.

## Deliberately excluded

- commitment planning;
- implementation tracking;
- outcome reviews;
- lessons learned;
- search;
- AI review;
- notifications and analytics.

Those workflows remain visible in the lifecycle but are blocked until their own complete vertical slices are implemented.

## Upgrade behaviour

Phase 4 adds the `positions_position` and `decisions_decisionfinalisation` tables. Existing accounts, organisations, invitations, memberships, workspaces, decisions, participants, options, evidence, assumptions, risks, transition history, and audit events remain unchanged.

No external service, paid provider, worker dependency, vector database, or hosted search component is introduced.
