# Domain model

## Identity and tenancy

### User

A human identity authenticated by Django. Email is normalised to lowercase and protected by ordinary and case-insensitive uniqueness constraints.

### Organisation

The top-level customer tenant and data-ownership boundary. Each new organisation receives one default decision workspace.

### Membership

The explicit relationship between one user and one organisation. Roles are owner, administrator, contributor, and viewer. Suspended memberships grant no tenant visibility.

### OrganisationInvitation

A time-limited, revocable request for one email address to join one organisation under an explicit role. The record stores a keyed digest rather than the raw secret, the issuing manager, expiry, delivery metadata, and acceptance or revocation state. Membership is created only after explicit acceptance.

## Decision structure

### Workspace

An organisation-owned container for a coherent set of decisions. It is not a project-management board. Every organisation has one default `Decisions` workspace.

### Decision

The aggregate root for one important organisational choice. It stores framing, lifecycle state, human ownership, dates, urgency, and links to all structured reasoning and governance records.

The lifecycle is:

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

Lifecycle state is changed only through explicit commands. The status field is read-only at the ordinary API boundary.

### DecisionTransition

An immutable, sequenced record of one authorised lifecycle change. It stores from-state, to-state, actor, rationale, acknowledged warnings, and timestamp.

### Participant

A user's explicit responsibility within one decision. Roles are decision owner, decision maker, contributor, reviewer, and observer. Removal is soft so historical participation remains attributable. The decision-owner participant is maintained by the decision ownership workflow.

## Structured reasoning

### DecisionOption

An alternative under consideration. Options capture a title, description, benefits, trade-offs, status-quo marker, proposer, and active/withdrawn state.

### Evidence

An attributable item that supports, contradicts, or contextualises the decision or an option. It records source details, strength, stance, notes, and active/withdrawn state.

### Assumption

An explicit proposition currently treated as true. It records confidence, verification state, accountable owner, review date, notes, and active/retired state.

### Risk

An explicit uncertain event or condition. It records likelihood, impact, response strategy, mitigation, accountable owner, and current status.

## Human governance

### Position

One immutable version of an eligible participant's recommendation. It records:

- the participant, submitter, and participant role at submission;
- support, conditional support, rejection of all options, or abstention;
- an active preferred option when support is expressed;
- rationale and optional conditions;
- confidence;
- a participant-specific version number and timestamp.

A participant revises a position by submitting a new version. Existing rows cannot be updated or deleted through the model or queryset. Current positions are derived from the latest version for each active participant; all versions remain available as history.

Decision owners, decision makers, contributors, and reviewers may submit positions while the decision is open for contribution, under review, or ready for decision. Observers may not submit a formal position.

### DecisionFinalisation

The immutable human-authored record that makes a decision final. It has a one-to-one relationship with the decision and stores:

- the selected active option;
- the human who decided;
- the final rationale;
- conditions or constraints;
- how dissent and alternatives were considered;
- a JSON snapshot of current stakeholder positions;
- the decision timestamp.

Creation is allowed only when the decision is `Ready for Decision`, the caller has finalisation authority, every active decision owner and decision maker has a current position, and the caller confirms those positions were reviewed. A dissent summary is mandatory whenever a current position rejects all options, abstains, or supports another option.

The finalisation record and the transition to `Decision Finalised` are created atomically.

## Audit

### AuditEvent

An append-only attributable record of a material action. It stores tenant, action, object type and identifier, actor, metadata, and timestamp. It complements rather than replaces domain history such as position versions, decision transitions, and finalisation.

## Core invariants

1. Cross-tenant foreign keys must share the same organisation.
2. An organisation must retain at least one active owner.
3. Membership begins only through accepted organisation creation or invitation workflows.
4. Unfinished decision ownership cannot be stranded during offboarding.
5. Active assumption and unresolved risk ownership must be transferred before offboarding.
6. Decision lifecycle status cannot be patched directly.
7. At least two active options, evidence, assumptions, and current risks are required before `Ready for Decision`.
8. Submitted positions are immutable and attributable to the participant who submitted them.
9. Every active decision owner and decision maker must have a current position before finalisation.
10. Finalisation must select an active option from the same decision and cannot be edited or deleted.
11. Later lifecycle states remain blocked until their supporting domain records are implemented.

## DecisionReview

One `DecisionReview` belongs to exactly one finalised decision and holds the accountable post-decision record:

- active implementation owner;
- commitment statement and success measures;
- intended outcome-review date;
- implementation plan and actual implementation summary;
- outcome assessment, evidence, and unintended consequences;
- attributable actors and timestamps for commitment, implementation start, and review completion.

The record is created at `Commitment`, progressively completed through `Outcome Review`, and retained after archival. Ownership transfer is audited and limited to active tenant members.

## Lesson

A decision may have multiple lessons after outcome review. Each lesson records a concise title, detailed insight, category, applicability, recommended organisational change, creator, and active/retired state. At least one active lesson is required before archival. Lessons remain searchable organisational knowledge after the decision is archived.
