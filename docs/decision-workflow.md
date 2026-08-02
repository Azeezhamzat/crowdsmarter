# Decision workflow

## Lifecycle contract

```text
Draft
→ Framing
→ Open for Contribution
→ Under Review
→ Ready for Decision
→ Decision Finalised
→ Commitment
→ Implementation
→ Outcome Review
→ Lessons Learned
→ Archived
```

The complete contract is represented in the model and UI. A transition is enabled only when the records needed to make the destination state truthful exist.

## Implemented transitions

### Draft → Framing

Requires a clear decision question, purpose, and scope.

### Framing → Open for Contribution

Requires contribution guidance, a future contribution deadline, and at least one active stakeholder in addition to the decision owner.

### Open for Contribution → Under Review

Requires an explicit human rationale for closing ordinary contribution.

### Under Review → Ready for Decision

Requires an explicit human rationale and the Phase 3 completeness gate:

1. at least two active options;
2. at least one active evidence item;
3. at least one active assumption;
4. no active assumption marked `invalidated`; and
5. at least one risk that is not closed.

These checks establish review completeness. They do not rank options or make the decision.

### Ready for Decision → Decision Finalised

This step is not an ordinary transition. An authorised human invokes the finalisation command, which requires:

1. an active selected option from the same decision;
2. a current position from every active decision owner and decision maker;
3. confirmation that current stakeholder positions were reviewed;
4. a final human rationale;
5. conditions or constraints when relevant; and
6. an explanation of how dissent and alternative positions were considered whenever they do not support the selected option.

The command snapshots current positions, creates the immutable finalisation record, appends transition history, updates status, and writes audit events atomically.

## Stakeholder positions

Eligible participants may submit a position during Open for Contribution, Under Review, or Ready for Decision. A position can support an option, support it conditionally, reject all options, or abstain. Confidence is explicit but is not converted into an automated vote or score.

Revising a position creates another immutable version. The current view shows the latest version per active participant; the history view preserves all versions.

## Post-decision lifecycle

Phase 5 enables the remaining states through dedicated records and commands:

| Transition | Required record |
|---|---|
| Decision Finalised → Commitment | accountable owner, commitment, success measures, review date, and rationale |
| Commitment → Implementation | implementation plan, accountable actor, and start rationale |
| Implementation → Outcome Review | implementation summary and review-opening rationale |
| Outcome Review → Lessons Learned | evidence-based outcome assessment and unintended consequences |
| Lessons Learned → Archived | at least one active reusable lesson and closure rationale |

These transitions cannot be performed through the generic lifecycle endpoint. Each command locks the decision, verifies the caller's expected status and authority, updates the durable supporting record, appends immutable transition history, and writes an audit event atomically.

## Human authority and AI

AI may later summarise evidence, identify gaps, retrieve similar decisions, or highlight contradictions and risks. AI never:

- submits a stakeholder position;
- chooses an option;
- performs a lifecycle transition;
- acknowledges a warning;
- accepts a risk;
- creates or edits the finalisation record.

Only an authenticated, authorised human command can finalise a decision.

## Optimistic concurrency

Every lifecycle and finalisation command includes `expected_status`. The service locks the decision row and rejects a stale command if another actor changed the decision after the page was loaded.

## Reversals and amendments

The current product does not implement reversal or amendment commands. A correction after finalisation requires explicit rules for authority, notifications, commitments, history, and customer reporting. It will be introduced as a governed workflow rather than arbitrary backward status editing.

## Phase 5 post-decision commands

The final five states are not generic status changes:

- `Decision Finalised → Commitment`: record an active implementation owner, commitment statement, success measures, review date, and rationale.
- `Commitment → Implementation`: record the implementation plan and rationale for beginning execution.
- `Implementation → Outcome Review`: record what was actually implemented and why the work is ready for review.
- `Outcome Review → Lessons Learned`: assess the actual outcome against explicit evidence and record unintended consequences.
- `Lessons Learned → Archived`: capture at least one active, reusable lesson and record why the learning cycle is complete.

The implementation owner may be transferred only by a decision lifecycle authority to another active organisation member. Offboarding is blocked while a person owns an unarchived implementation record.
