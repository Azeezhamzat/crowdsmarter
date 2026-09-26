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
11. Every lifecycle transition through archival requires its supporting domain record and an attributable authorised command.

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

## Phase 6 models and read models

### Notification

A `Notification` belongs to one organisation and recipient, may reference a decision, and records kind, title, message, internal URL, metadata, deduplication key, and read time. Recipient plus non-empty deduplication key is unique. Notification reads never grant access to the referenced domain object; ordinary tenant permissions still apply when the user opens its URL.

### AIReview

An `AIReview` belongs to one organisation and decision and records the requesting human, provider identity, prompt/schema version, input fingerprint, private input snapshot, structured output or safe failure, and mutually exclusive human acknowledgement or dismissal. The review is append-only advisory context and is not part of the decision-authority state machine.

### Organisation analytics

Analytics have no write model in Phase 6. They are tenant-scoped read models computed from decisions, transitions, active participants, decision reviews, and active lessons. This avoids duplicated truth and a premature analytics warehouse.

## Collaboration

`DiscussionEntry` belongs directly to an organisation and decision. It records an author, kind, immutable body, optional parent entry, mentioned users, and optional resolution record. Only questions and concerns may be resolved. Resolution fields are additive and attributable.

## Portfolio read models

Portfolio services do not own persisted domain state. They derive personal accountability, due dates, unresolved discussion counts, and organisation-level decision lists from decisions, participants, reviews, positions, notifications, and collaboration records.

## Phase 10 derived export artefacts

Exports are generated artefacts, not authoritative database entities. The organisation archive and decision dossier contain stable identifiers from the authoritative domain records plus a manifest with schema version and generation time. No export model is persisted, avoiding duplicate customer state and storage cost. Audit events record the human download action.


## Foresight and source intelligence

### FeedSubscription

A manually synchronised RSS or Atom feed belonging to one organisation. It records a public feed URL, accountable owner, conditional-request metadata, and the latest success or safe failure. Feed entries become unassessed `Source` records only.

### Source

An attributable input for foresight and decision evidence. It records source
type, author, publisher, publication/access/review dates, jurisdiction, live
and archived URLs or reference, verification time, credibility assessment and
rationale, lifecycle status, optional supersession, feed provenance, and
creator. A source can support multiple signals, evidence records, and research
claims.

### SourceAttachment

A private file linked to one source. It preserves the original file name, verified MIME type, size, SHA-256 digest, uploader, and storage reference. Storage paths use generated identifiers rather than customer-supplied names. Files are tenant-authorised at download time and included in customer exports when available.

### ResearchClaim and ResearchClaimSource

`ResearchClaim` is a reviewable proposition that can change the product,
facilitation, operations, or a linked decision. It preserves the evidence
state, build/integrate/defer/avoid/monitor recommendation, evidence summary,
limitations, assumptions, reversal condition, expected outcome, accountable
owner, review date, and lifecycle. Its evidence score is the explicit sum of
authority (0–3), directness (0–3), recency (0–2), and triangulation (0–2).

`ResearchClaimSource` is the through record connecting a claim and source. It
states whether the source supports, contradicts, or only contextualises the
claim, preserves the analyst's relationship note and actor, rejects
cross-tenant linkage, and allows only one current relationship per claim/source
pair. It never rewrites the source itself or automatically changes the claim's
state.

### Signal

A human interpretation of an observed change and its potential future implication. It records one STEEP category, strategic time horizon, maturity, opportunity/threat polarity, geography, domain, impact, uncertainty, accountable owner, review state, and optional source. `impact × uncertainty` is an attention aid, not an automated priority decision.

### Watchlist

An organisation-owned, accountable collection of signals for one continuing strategic concern. Watchlists preserve attention over time without changing the underlying signal records.

### SignalDecisionLink

An explicit, attributable explanation of why a signal matters to one decision. The signal and decision must belong to the same organisation. The link informs human reasoning but never mutates the decision lifecycle.

## Phase 12 systems-foresight model

- **ForesightCanvas** bounds a focal question, scope, horizon year, status, and accountable owner.
- **Driver** represents a trend, force, critical uncertainty, predetermined element, or wild card and may be grounded in multiple signals.
- **SystemStakeholder** records an actor's role, interests, influence, exposure, and stance.
- **CausalRelationship** records one directed mechanism with polarity, strength, delay, and rationale.
- **FeedbackLoop** records a human-interpreted reinforcing, balancing, mixed, or uncertain loop across at least two drivers.
- **FuturesWheelConsequence** records first-, second-, or third-order consequences.
- **ThreeHorizonItem** places current pressures, transition activity, or emerging futures in a time-oriented view.
- **StrategicImplication** converts analysis into an owned opportunity, threat, capability need, policy implication, or decision requirement and may link to a decision.

## Phase 13 scenario-intelligence model

- **ScenarioSet** is a governed 2×2 exercise on one foresight canvas, defined by two different active critical uncertainties, meaningful endpoint labels, an accountable owner, and an optional same-tenant decision.
- **Scenario** is one human-authored world in a unique quadrant with an explicit code, headline, narrative, assumptions, opportunities, threats, and review state.
- **ScenarioDriverState** records how a canvas driver behaves and how salient it is within one scenario.
- **ScenarioReview** preserves one attributable structured review per member and exposes aggregate criteria plus confidence dispersion.
- **WindTunnelAssessment** tests one active option from the linked decision against one scenario without changing option or decision state.
- **ScenarioImplicationLink** explains how an existing strategic implication is amplified, reduced, changed, or triggered in a scenario.
- **Signpost** is an owned observable indicator with a threshold, direction, cadence, status, and explicit scenario relationships.
- **SignpostObservation** is a dated human assessment of a signpost and may reference an existing same-tenant source.

## Phase 14 collective-evaluation model

- **EvaluationExercise** binds one decision to a scorecard, approval, consent, or Delphi method and records ownership, identity treatment, sealed-result policy, quorum, and applicable thresholds.
- **EvaluationCriterion** defines a weighted bounded scale for scorecard exercises.
- **EvaluationRound** creates a controlled contribution period and, for Delphi, a facilitator-authored feedback bridge to the next round.
- **EvaluationSubmission** preserves one participant's confidence-rated contribution in one round.
- **EvaluationResponse** records an option score or method-specific ballot with rationale.
- **MinorityReport** preserves an attributable dissenting analysis and alternative recommendation linked to an exercise and optional round.
- **PrioritisationPortfolio** defines an organisation-level comparison, resource envelope, ownership, identity mode, and blind-result policy.
- **PortfolioCriterion** defines a positive-weight value dimension.
- **PortfolioCandidate** links one same-tenant decision with resource requirements, mandatory status, and inclusion rationale.
- **PortfolioAssessment** preserves one contributor's criterion score, confidence, and rationale.
- **PortfolioSelection** records the accountable authority's actual inclusion or exclusion, ordering, approved resources, and rationale independently of the recommendation.

Aggregated evaluation results and constrained recommendations are derived read models. They are not authoritative decisions and are not persisted as organisational truth.

## Phase 15 decision-analysis records

### DecisionIssue

A human-accepted gap or contradiction associated with one decision and optionally one option, evidence item, assumption, risk, evaluation exercise, or scenario set. Types cover evidence contradiction, missing evidence, unsupported assumption, stakeholder gap, unresolved objection, scenario vulnerability, resource uncertainty, implementation uncertainty, and other.

Each issue has severity, status, an active-member owner, optional due date, creation attribution, and resolution attribution. Linked records must share the same decision and organisation. Resolved issues require resolution text, resolver, and timestamp.

### DecisionQualityReview

A versioned human judgement over a bounded checklist. Answers are `yes`, `partly`, `no`, or `not_applicable`; overall judgement is `not_ready`, `ready_with_conditions`, or `ready`. A decision may have one draft and one current published review. Publishing supersedes the earlier published version. Published and superseded reviews are immutable.

### ExecutiveDecisionSummary

A structured versioned synthesis containing context, options, evidence, uncertainty, stakeholder, scenario, evaluation, risk, unresolved-issue, proposed-judgement, condition, and implementation sections. A decision may have one draft and one current approved summary. Approval requires a proposed judgement plus human approval attribution. Approved and superseded summaries are immutable.

## Phase 15.1 public decision enquiries

`DemoRequest` is the compatibility name for a decision enquiry and is deliberately outside the organisation aggregate. It records a prospective contact's name, work email, organisation, role, organisation-size band, decision difficulty, decision context, contact consent, operational status, and timestamps. The current public form requires a short decision context; the API retains its compatible optional field. The record has no membership, decision, or tenant relationship and cannot create any of them. Status changes are limited to protected administration.

## Contribution orchestration

- `FacilitationSession`: one bounded workshop attached to one decision, with an attributable facilitator, explicit accessibility and consent/attribution arrangements, and forward-only state.
- `FacilitationAgendaItem`: one ordered, timed activity with a purpose, method, facilitator prompt, expected output, and immutable execution timestamps. A database constraint permits only one active item per session.
- `SessionParticipant`: an invited organisation member, workshop role, and attendance state.
- `FacilitationRecord`: an append-only, provenance-aware output that may be linked to the agenda item that produced it without changing the source participant record.
- `FacilitationQualityReview`: the facilitator's post-closure one-to-one review across inclusion, boundary clarity, neutrality, meaningful participation, and follow-through, plus what worked, what must improve, and unresolved risks.
- `ContributionRequest`: the bounded requested output, assignee, optional reviewer, optional option/session links, priority, due date, and governed workflow state.
- `ContributionSubmission`: one mutable assignee draft or an immutable submitted revision with a per-request sequence.
- `ContributionReview`: an append-only review outcome and guidance linked to a submitted revision.
- `ContributionPreference`: one user's reminder and email-delivery settings inside one organisation.

Tenant and decision duplication on child records is intentional: it supports direct tenant filtering, export, audit, and invariant validation.

## Phase 17 domain additions

- `DecisionMethod`: stable organisation-owned method identity and lifecycle.
- `DecisionMethodVersion`: draft or human-approved prompt set; immutable after approval.
- `DecisionMethodUsage`: permanent link between one decision and the exact approved version used.
- `MembershipEvent`: append-only record of access, role, removal, and ownership changes.
- `OrganisationDeletionRequest`: delayed owner request; no automatic hard deletion.
- `Organisation` administrative fields: profile, branding, invitation policy, default role, retention wait, and deactivation state.
