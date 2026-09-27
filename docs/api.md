# API

Base path: `/api/v1`

Authentication uses a Django session cookie and CSRF token. JSON is the default representation. Strict command serializers reject unexpected fields rather than silently discarding them.

## Authentication

| Method | Path | Purpose | Access |
|---|---|---|---|
| GET | `/auth/csrf/` | Set CSRF cookie | Public |
| POST | `/auth/session/` | Create session from email/password | Public, rate-limited |
| DELETE | `/auth/session/logout/` | Destroy session | Authenticated |
| GET | `/auth/me/` | Read current user | Authenticated |

## Organisations, memberships, and invitations

| Method | Path | Purpose |
|---|---|---|
| GET, POST | `/organisations/` | List tenants or create one |
| GET, PATCH | `/organisations/{organisation_id}/` | Read or rename a visible tenant |
| GET | `/organisations/{organisation_id}/memberships/` | List accepted members |
| PATCH, DELETE | `/organisations/memberships/{membership_id}/` | Change role or remove membership |
| GET, POST | `/organisations/{organisation_id}/invitations/` | List or issue invitations |
| POST | `/organisation-invitations/{invitation_id}/resend/` | Rotate and resend a pending invitation |
| POST | `/organisation-invitations/{invitation_id}/revoke/` | Revoke a pending invitation |
| GET, POST | `/invitations/accept/` | Inspect or accept an invitation |

The raw invitation secret is sent in `X-Invitation-Token`. The browser stores it after `#token=` so it does not appear in normal request paths or referrer headers.

## Workspaces

| Method | Path | Purpose |
|---|---|---|
| GET, POST | `/organisations/{organisation_id}/workspaces/` | List or create workspaces |
| GET, PATCH | `/workspaces/{workspace_id}/` | Read or update a workspace |

## Decisions and transitions

| Method | Path | Purpose |
|---|---|---|
| GET, POST | `/workspaces/{workspace_id}/decisions/` | List or create decisions |
| GET, PATCH | `/decisions/{decision_id}/` | Read or update permitted framing fields |
| GET, POST | `/decisions/{decision_id}/transitions/` | Read history or execute one ordinary next transition |

Decision detail includes server-derived capabilities and summaries:

- `can_edit`;
- `can_transition`;
- `can_manage_participants`;
- `can_contribute_reasoning`;
- `can_submit_position`;
- `can_finalise`;
- `next_transition`, including `action`, `enabled`, and `blocked_reason`;
- `reasoning_summary`;
- `position_summary`.

`next_transition.action` is `finalise` at `Ready for Decision` and `outcome_workflow` from `Decision Finalised` through `Lessons Learned`. The ordinary transition endpoint rejects those governed steps; clients must use the dedicated finalisation or outcomes-and-learning commands.

Ordinary transition command:

```json
{
  "expected_status": "under_review",
  "rationale": "The structured review is complete.",
  "warnings_acknowledged": []
}
```

`expected_status` provides optimistic stale-page protection.

## Participants

| Method | Path | Purpose |
|---|---|---|
| GET, POST | `/decisions/{decision_id}/participants/` | List or add participants |
| PATCH, DELETE | `/participants/{participant_id}/` | Change role or soft-remove a participant |

Assignable roles are `decision_maker`, `contributor`, `reviewer`, and `observer`. Decision ownership is managed through the decision aggregate.

## Structured reasoning

| Method | Path | Purpose |
|---|---|---|
| GET, POST | `/decisions/{decision_id}/options/` | List or create decision options |
| GET, PATCH | `/decision-options/{option_id}/` | Read or update an option |
| GET, POST | `/decisions/{decision_id}/evidence/` | List or create evidence |
| GET, PATCH | `/evidence/{evidence_id}/` | Read or update evidence |
| GET, POST | `/decisions/{decision_id}/assumptions/` | List or create assumptions |
| GET, PATCH | `/assumptions/{assumption_id}/` | Read or update an assumption |
| GET, POST | `/decisions/{decision_id}/risks/` | List or create risks |
| GET, PATCH | `/risks/{risk_id}/` | Read or update a risk |

## Stakeholder positions

| Method | Path | Purpose |
|---|---|---|
| GET | `/decisions/{decision_id}/positions/` | Read the current latest position for each active participant |
| POST | `/decisions/{decision_id}/positions/` | Append a new version of the caller's own position |
| GET | `/decisions/{decision_id}/positions/history/` | Read all immutable position versions |

Position command:

```json
{
  "preferred_option_id": "option-uuid-or-null",
  "recommendation": "support",
  "rationale": "A limited pilot preserves learning while controlling exposure.",
  "conditions": "Review performance after three months.",
  "confidence": "high"
}
```

Recommendations are `support`, `support_with_conditions`, `do_not_support_any`, and `abstain`. Support requires an active option from the same decision. Abstention and rejection must not identify an option. Conditional support requires conditions.

## Human finalisation

| Method | Path | Purpose |
|---|---|---|
| GET | `/decisions/{decision_id}/finalisation/` | Read the immutable final decision record, or `null` |
| POST | `/decisions/{decision_id}/finalisation/` | Select an option and finalise the decision |

Finalisation command:

```json
{
  "expected_status": "ready_for_decision",
  "selected_option_id": "active-option-uuid",
  "rationale": "This option provides the best learning-to-risk balance.",
  "conditions": "Review after three months.",
  "dissent_summary": "The lower-risk alternative was considered but would not test the key assumption.",
  "positions_reviewed": true
}
```

The command is transactional. It verifies authority, active option ownership, required position coverage, stale state, and dissent treatment; then creates the finalisation, transition, and audit records atomically.

## Audit events

| Method | Path | Purpose | Access |
|---|---|---|---|
| GET | `/organisations/{organisation_id}/audit-events/` | Read the newest 100 tenant audit events | Owner/admin |

Optional query parameters are `action` and `object_type`.

## Errors

- `400`: invalid input, stale command, or domain invariant violation;
- `403`: visible resource but insufficient authority;
- `404`: resource absent or outside tenant visibility;
- `429`: rate limit exceeded.

Domain validation is translated at the API boundary; services remain independent of DRF.

## Commitment, implementation, and outcome review

| Method | Path | Purpose |
|---|---|---|
| GET, PATCH | `/decisions/{decision_id}/review/` | Read the execution record or transfer implementation ownership |
| POST | `/decisions/{decision_id}/commitment/` | Record commitment and enter `Commitment` |
| POST | `/decisions/{decision_id}/implementation/start/` | Record the implementation plan and enter `Implementation` |
| POST | `/decisions/{decision_id}/outcome-review/open/` | Summarise implementation and enter `Outcome Review` |
| POST | `/decisions/{decision_id}/outcome-review/complete/` | Record the evidence-based outcome and enter `Lessons Learned` |

These are dedicated human commands. The generic transition endpoint cannot bypass them. Every command checks lifecycle authority, expected state, active tenant ownership, required fields, and stale-page conflicts, then updates the review, transition history, and audit log transactionally.

Commitment command:

```json
{
  "expected_status": "decision_finalised",
  "implementation_owner_id": "active-member-uuid",
  "commitment_statement": "Run the approved pilot on three sites.",
  "success_measures": "Compare lead time, accuracy, adoption, and cost.",
  "review_due_date": "2026-11-01",
  "rationale": "The commitment faithfully implements the selected option."
}
```

Outcome-review completion command:

```json
{
  "expected_status": "outcome_review",
  "outcome_summary": "Detection improved on two sites and was unchanged on one.",
  "outcome_assessment": "partially_met",
  "review_evidence": "Inspection logs, baseline comparison, and staff interviews.",
  "unintended_consequences": "Field staff required additional training.",
  "rationale": "The available evidence is sufficient to complete the review."
}
```

## Lessons learned and archival

| Method | Path | Purpose |
|---|---|---|
| GET, POST | `/decisions/{decision_id}/lessons/` | List or capture lessons during `Lessons Learned` |
| PATCH, DELETE | `/lessons/{lesson_id}/` | Revise or retire a lesson before archival |
| POST | `/decisions/{decision_id}/archive/` | Archive after at least one active lesson exists |

Lessons record an insight, category, applicability, and optional recommended organisational change. Archived decision learning is read-only.

## Organisational search

| Method | Path | Purpose |
|---|---|---|
| GET | `/organisations/{organisation_id}/search/?q={query}` | Search tenant decision knowledge |

The query must contain at least two characters. Results are ranked by PostgreSQL full-text search and can include decisions, options, evidence, assumptions, risks, outcome reviews, and active lessons. A caller must first hold active membership in the organisation; inaccessible organisations return `404`.

## Notifications

| Method | Path | Purpose |
|---|---|---|
| GET | `/notifications/` | Read the newest 100 notifications for the authenticated user |
| POST | `/notifications/{notification_id}/read/` | Mark one owned notification as read |
| POST | `/notifications/read-all/` | Mark the authenticated user's unread notifications as read |

`GET /notifications/?unread=true` limits the returned items to unread notifications. Notification visibility is recipient-private; another authenticated user receives `404` for an inaccessible notification.

## Advisory AI reviews

| Method | Path | Purpose |
|---|---|---|
| GET | `/decisions/{decision_id}/ai-reviews/` | Read attributable advisory reviews and request capability |
| POST | `/decisions/{decision_id}/ai-reviews/` | Run one review through the configured provider |
| GET | `/ai-reviews/{review_id}/` | Read one tenant-visible review |
| POST | `/ai-reviews/{review_id}/acknowledge/` | Record immutable human review notes |
| POST | `/ai-reviews/{review_id}/dismiss/` | Dismiss output with an immutable reason |

The create command accepts an empty JSON object. Provider selection is deployment configuration, not client input. The response includes provider provenance, fingerprint, structured findings, limitations, and human disposition, but never returns the private decision snapshot. Requests are throttled. Advisory reviews cannot change the decision or execute lifecycle commands.

## Organisation analytics

| Method | Path | Purpose |
|---|---|---|
| GET | `/organisations/{organisation_id}/analytics/` | Read defined decision-flow and learning measures |

The endpoint is available to active organisation members and returns totals, lifecycle counts, 90-day flow measures, median time to human finalisation, overdue target dates, participant coverage, outcome assessment distribution, due reviews, active lessons, and the definitions used to calculate the principal measures.

## Phase 7 portfolio and collaboration

### Personal work

`GET /api/v1/me/work/`

Returns active decisions where the current user is an owner, active participant, or implementation owner. Each item contains its lifecycle state, due date, overdue state, unresolved-discussion count, and an explainable next action.

### Organisation decision portfolio

`GET /api/v1/organisations/{organisation_id}/portfolio/`

Optional query parameters:

- `q`
- `status`
- `urgency`
- `workspace_id`
- `owner_id`
- `my_work=true`
- `overdue=true`

### Decision discussion

`GET /api/v1/decisions/{decision_id}/discussion/`

`POST /api/v1/decisions/{decision_id}/discussion/`

```json
{
  "kind": "question",
  "body": "Which evidence validates this assumption?",
  "mentioned_user_ids": ["user-uuid"],
  "reply_to_id": null
}
```

### Resolve a question or concern

`POST /api/v1/discussion-entries/{entry_id}/resolve/`

```json
{
  "resolution_note": "The baseline dataset was added as evidence item E-14."
}
```

### Decision activity

`GET /api/v1/decisions/{decision_id}/activity/`

Returns up to 200 recent discussion and material audit items in reverse chronological order.

## Phase 8 guided creation and decision overview

### Decision-template catalogue

`GET /api/v1/decision-templates/`

Returns the authenticated catalogue of built-in, versioned framing templates. Each item contains prompts, a suggested urgency, and a checklist. The response contains no organisation data and does not create records.

### Guided draft creation

`POST /api/v1/workspaces/{workspace_id}/decisions/`

The existing create endpoint now also accepts complete draft framing:

```json
{
  "template_key": "technology_adoption",
  "title": "Pilot a field monitoring platform",
  "decision_question": "Should we run a controlled pilot before wider adoption?",
  "purpose": "Reduce uncertainty before committing organisational resources.",
  "context": "Current local performance is unknown.",
  "scope": "Three sites for three months; no wider rollout.",
  "contribution_guidance": "Provide security, usability, cost, and outcome evidence.",
  "urgency": "high",
  "target_decision_date": "2026-09-30",
  "contribution_deadline": "2026-09-15T17:00:00Z",
  "owner_id": "user-uuid"
}
```

All fields are user-submitted. The endpoint creates a Draft and never transitions the lifecycle automatically. `template_key` defaults to `blank` for compatible existing clients.

### Decision overview

`GET /api/v1/decisions/{decision_id}/overview/`

Returns a tenant-scoped read model containing lifecycle progress, next action, framing completeness, participant roles, unresolved discussion, active options, material risks, the transparent reasoning summary, and target-date state. It performs no writes and grants no additional capabilities.

## Phase 10 account self-service

| Method | Path | Purpose |
|---|---|---|
| PATCH | `/auth/me/` | Update the authenticated user's first and last name |
| POST | `/auth/password/change/` | Change the password after checking the current password |
| POST | `/auth/email/change/` | Send a verification link to a replacement email after checking the current password |
| POST | `/auth/email/change/confirm/` | Consume a short-lived, single-use email verification token |
| POST | `/auth/password/reset/` | Request a generic, non-enumerating recovery response |
| POST | `/auth/password/reset/confirm/` | Validate a time-limited token and set a new password |

The reset-request response is deliberately identical for registered and unregistered email addresses. In local debug mode it may include `development_reset_url` so console-email installations remain usable without external infrastructure.

Email changes do not take effect at request time. The proposed address receives a URL-fragment token, the old address receives a security notice, and the recipient must explicitly press the confirmation button so automated link scanners cannot consume the token. A newer request invalidates every earlier pending link. Local debug responses may include `development_verification_url`.

## Phase 10 customer exports

| Method | Path | Purpose |
|---|---|---|
| GET | `/organisations/{organisation_id}/exports/complete/` | Download the complete tenant archive as an owner or administrator |
| GET | `/decisions/{decision_id}/export/` | Download a portable dossier for one visible decision |

Both endpoints return `application/zip`, use `Cache-Control: private, no-store`, are rate limited, and append audit events. The archive manifest records export type, schema version, generation time, record counts, and stable customer identifiers.

## Phase 11 foresight and source intelligence

All endpoints require an authenticated Django session and active organisation membership. Write endpoints also enforce organisation role and record ownership in services.

### Organisation overview

- `GET /api/v1/organisations/{organisation_id}/foresight/overview/`

Returns active signal, source, research-claim, watchlist, high-attention,
evidence-gap, review-due, STEEP, and horizon counts plus the caller's
contribution capability.

### RSS and Atom feeds

- `GET|POST /api/v1/organisations/{organisation_id}/foresight/feeds/`
- `POST /api/v1/foresight/feeds/{feed_id}/sync/`

Synchronisation is manual and throttled. Feed entries create unassessed sources only. The endpoint never creates or interprets signals.

### Sources and private attachments

- `GET|POST /api/v1/organisations/{organisation_id}/foresight/sources/`
- `GET|PATCH /api/v1/foresight/sources/{source_id}/`
- `POST /api/v1/foresight/sources/{source_id}/attachments/`
- `GET /api/v1/foresight/attachments/{attachment_id}/download/`

Attachment uploads use multipart form data with a `file` field. Downloads are tenant-authorised, audited, and returned with private no-store headers.

Sources also preserve optional access date, jurisdiction, archived URL,
verification time, and freshness-review date. A non-unassessed credibility
assessment records the verification time; updating reference or credibility
fields refreshes it.

### Research claims

- `GET|POST /api/v1/organisations/{organisation_id}/foresight/research-claims/`
- `GET|PATCH /api/v1/foresight/research-claims/{claim_id}/`
- `POST /api/v1/foresight/research-claims/{claim_id}/sources/`
- `DELETE /api/v1/foresight/research-claims/{claim_id}/sources/{source_id}/`

A claim records one neutral proposition, evidence state, product
recommendation, relevance, claim-level evidence score, limitations,
assumptions, reversal condition, expected observable result, owner, review
date, lifecycle, and optional same-tenant decision. Source links explicitly
state `supports`, `contradicts`, or `context`; posting the same source again
updates that relationship. Scores are transparent inputs—authority 0–3,
directness 0–3, recency 0–2, and triangulation 0–2—and do not assert legal
compliance, effectiveness, or product-market fit.

### Signals

- `GET|POST /api/v1/organisations/{organisation_id}/foresight/signals/`
- `GET|PATCH /api/v1/foresight/signals/{signal_id}/`
- `POST /api/v1/foresight/signals/{signal_id}/decisions/`

Signal list filters include `q`, `steep_category`, `time_horizon`, `maturity`, and `status`. A decision link requires a same-tenant decision identifier and an explicit relevance explanation.

### Watchlists

- `GET|POST /api/v1/organisations/{organisation_id}/foresight/watchlists/`
- `GET|PATCH /api/v1/foresight/watchlists/{watchlist_id}/`
- `POST /api/v1/foresight/watchlists/{watchlist_id}/signals/`
- `DELETE /api/v1/foresight/watchlists/{watchlist_id}/signals/{signal_id}/`

### Evidence integration

Evidence create and update contracts accept an optional `source_id`. When a structured source is selected, it must belong to the same organisation as the decision. Manual source references remain supported for backwards compatibility.

## Phase 12 systems foresight

- `GET|POST /api/v1/organisations/{organisation_id}/foresight/canvases/`
- `GET|PATCH /api/v1/foresight/canvases/{canvas_id}/`
- `POST /api/v1/foresight/canvases/{canvas_id}/drivers/`
- `PATCH /api/v1/foresight/drivers/{driver_id}/`
- `POST /api/v1/foresight/drivers/{driver_id}/signals/`
- `POST /api/v1/foresight/canvases/{canvas_id}/stakeholders/`
- `POST /api/v1/foresight/canvases/{canvas_id}/relationships/`
- `POST /api/v1/foresight/canvases/{canvas_id}/feedback-loops/`
- `POST /api/v1/foresight/canvases/{canvas_id}/consequences/`
- `POST /api/v1/foresight/canvases/{canvas_id}/horizons/`
- `POST /api/v1/foresight/canvases/{canvas_id}/implications/`
- `PATCH /api/v1/foresight/implications/{implication_id}/`

All commands use strict serializers and service-layer permission, tenant, and archival checks.

## Phase 13 scenario intelligence

All endpoints require authentication and tenant membership. Write commands require contribution capability; governed update commands also enforce creator, owner, or organisation-manager authority.

### Scenario sets and worlds

- `GET|POST /api/v1/foresight/canvases/{canvas_id}/scenario-sets/`
- `GET|PATCH /api/v1/foresight/scenario-sets/{scenario_set_id}/`
- `POST /api/v1/foresight/scenario-sets/{scenario_set_id}/scenarios/`
- `PATCH /api/v1/foresight/scenarios/{scenario_id}/`
- `POST /api/v1/foresight/scenarios/{scenario_id}/driver-states/`
- `POST /api/v1/foresight/scenarios/{scenario_id}/implications/`

The scenario-set workspace returns the four worlds, review summaries, driver states, linked implications, wind-tunnel assessments, signposts, observations, and active options from the linked decision.

### Collective review and wind-tunnelling

- `POST /api/v1/foresight/scenarios/{scenario_id}/reviews/`
- `POST /api/v1/foresight/scenarios/{scenario_id}/wind-tunnel/`

Posting again updates the caller's review or the scenario–option assessment. Wind-tunnelling accepts only an active option from the scenario set's linked decision.

### Adaptive signposts

- `POST /api/v1/foresight/scenario-sets/{scenario_set_id}/signposts/`
- `POST /api/v1/foresight/signposts/{signpost_id}/observations/`

A signpost may contain explicit relationships to scenarios in the same set. An observation may reference an existing source from the same organisation. Neither endpoint automatically changes scenario or decision status.

## Phase 14 collective evaluation and prioritisation

All routes require authentication. Tenant outsiders receive `404`. Strict command serializers reject unknown fields.

### Decision evaluation

- `GET|POST /api/v1/decisions/{decision_id}/evaluations/`
- `GET|PATCH /api/v1/evaluations/{exercise_id}/`
- `POST /api/v1/evaluations/{exercise_id}/criteria/`
- `POST /api/v1/evaluations/{exercise_id}/rounds/`
- `PATCH /api/v1/evaluation-rounds/{round_id}/`
- `PUT /api/v1/evaluation-rounds/{round_id}/submission/`
- `GET /api/v1/evaluation-rounds/{round_id}/results/`
- `POST /api/v1/evaluations/{exercise_id}/minority-reports/`

The exercise contract identifies one method: `scorecard`, `approval`, `consent`, or `delphi`. A blind open round returns only the caller's submission and a sealed result object. Closing the round exposes quorum, method-specific aggregates, confidence dispersion, and scorecard sensitivity. Peer-anonymous responses use neutral labels but remain attributable in the database and audit layer.

### Organisation prioritisation

- `GET|POST /api/v1/organisations/{organisation_id}/prioritisations/`
- `GET|PATCH /api/v1/prioritisations/{portfolio_id}/`
- `POST /api/v1/prioritisations/{portfolio_id}/criteria/`
- `POST /api/v1/prioritisations/{portfolio_id}/candidates/`
- `PUT /api/v1/prioritisation-candidates/{candidate_id}/assessments/`
- `PUT /api/v1/prioritisation-candidates/{candidate_id}/selection/`

An open blind portfolio hides aggregate scores and the constrained recommendation. After closure, the response shows candidate score, assessor count, confidence, resource requirements, mandatory status, recommendation status, and a human-readable constraint reason. Authority selections are separate records and never mutate the candidate decision.

## Integrated decision analysis

| Method | Path | Purpose |
|---|---|---|
| GET | `/decisions/{decision_id}/analysis/` | Read the option-centred integrated analysis workspace |
| GET, POST | `/decisions/{decision_id}/analysis/issues/` | List or create governed contradictions and gaps |
| PATCH | `/decision-analysis/issues/{issue_id}/` | Update an issue as its owner or an accountable authority |
| GET, POST | `/decisions/{decision_id}/analysis/quality-reviews/` | Read visible versions or create one authority-scoped draft |
| PATCH | `/decision-analysis/quality-reviews/{review_id}/` | Edit or publish a draft quality review |
| GET, POST | `/decisions/{decision_id}/analysis/executive-summaries/` | Read visible versions or create one authority-scoped draft |
| PATCH | `/decision-analysis/executive-summaries/{summary_id}/` | Edit or approve a draft executive summary |

The workspace response contains server-derived `can_manage` and `can_contribute` capabilities and a principle statement confirming that analysis does not select an option or advance the decision lifecycle.

Issue creation accepts a bounded issue type, title, description, severity, active-member owner, optional due date, and optional same-decision links. Resolution requires `status: "resolved"` plus non-empty `resolution` text.

Quality-review answer keys are limited to the published checklist contract. A draft may only transition to `published`. An executive-summary draft may only transition to `approved`. Published, approved, and superseded records reject mutation.

## Public decision enquiries

| Method | Path | Purpose | Access |
|---|---|---|---|
| POST | `/public/demo-requests/` | Store a prospective-client decision enquiry for facilitation discovery | Public, CSRF protected, rate limited |

Accepted fields are `full_name`, `work_email`, `organisation_name`, `job_title`, `organisation_size`, `primary_need`, `message`, `consent_to_contact`, and the blank anti-spam field `website`. The public form asks for a problem area and a short description of the real decision so the first conversation can be prepared; the API retains its compatible field contract. Unknown fields are rejected. A successful response is `202 Accepted` with a reference identifier. The endpoint does not create an account, organisation, membership, or marketing subscription.

## Phase 16 contribution-orchestration API

All routes require the normal session-authenticated, CSRF-protected API boundary. Unknown command fields are rejected.

- `GET|POST /api/v1/decisions/{decision_id}/contribution-requests/` — read the decision workspace or create a governed request.
- `GET /api/v1/contribution-requests/{request_id}/` — read one visible request; `PATCH` revises an editable assignment without rewriting submitted history.
- `POST /api/v1/contribution-requests/{request_id}/actions/` — open, start, start review, or cancel under state and capability rules.
- `PUT /api/v1/contribution-requests/{request_id}/draft/` — create or replace the assignee's mutable draft.
- `POST /api/v1/contribution-requests/{request_id}/submit/` — create an immutable submitted revision.
- `POST /api/v1/contribution-requests/{request_id}/review/` — append an accepted, returned, or comment review.
- `GET|POST /api/v1/decisions/{decision_id}/facilitation-sessions/` — list or schedule structured sessions. Creation accepts an objective, agenda, participation guidance, facilitator, schedule, `participants: [{"user_id": "...", "role": "participant" | "observer"}]`, and ordered `agenda_items` containing an activity, purpose, method, timebox, facilitator prompt, and expected output. The older `participant_ids` list remains accepted as participant-role invitations for compatible clients.
- `POST /api/v1/facilitation-sessions/{session_id}/status/` — perform a valid forward session transition.
- `POST /api/v1/facilitation-sessions/{session_id}/agenda-items/` — append a timed activity to a planned or open run-of-show.
- `POST /api/v1/facilitation-agenda-items/{item_id}/actions/` — start, complete, skip, or return an item to the queue. Only one agenda item may be live in a session, and a session cannot close while one remains live.
- `POST /api/v1/facilitation-sessions/{session_id}/records/` — append a provenance-aware agreement, disagreement, action, evidence gap, next question, or participant statement. `agenda_item_id` optionally ties the output to the run-of-show activity that produced it.
- `PUT /api/v1/facilitation-sessions/{session_id}/quality-review/` — create or update the facilitator's post-session inclusion, boundary-clarity, neutrality, meaningful-participation, and follow-through review. The session must be closed; scores are bounded from one to five and accompanied by qualitative learning.
- `POST /api/v1/facilitation-participants/{participant_id}/attendance/` — record workshop attendance.
- `GET /api/v1/contributions/my-work/` — return current assignee and explicit reviewer work across visible organisations.
- `GET|PATCH /api/v1/organisations/{organisation_id}/contribution-preferences/` — read or update the current user's delivery settings.

## Phase 17 organisation methodology and administration API

Method routes:

- `GET|POST /api/v1/organisations/{organisation_id}/decision-methods/`
- `POST /api/v1/organisations/{organisation_id}/decision-methods/clone/`
- `GET /api/v1/organisations/{organisation_id}/decision-method-usage/`
- `GET /api/v1/decision-methods/{method_id}/`
- `POST /api/v1/decision-methods/{method_id}/versions/`
- `POST /api/v1/decision-methods/{method_id}/retire/`
- `PATCH /api/v1/decision-method-versions/{version_id}/`
- `POST /api/v1/decision-method-versions/{version_id}/approve/`

Organisation-administration routes:

- `GET|PATCH /api/v1/organisations/{organisation_id}/administration/`
- `GET /api/v1/organisations/{organisation_id}/membership-history/`
- `POST /api/v1/organisations/{organisation_id}/transfer-ownership/`
- `POST /api/v1/organisations/{organisation_id}/deactivate/`
- `POST /api/v1/organisations/{organisation_id}/reactivate/`
- `GET|POST /api/v1/organisations/{organisation_id}/deletion-requests/`
- `POST /api/v1/organisations/deletion-requests/{request_id}/cancel/`

Decision creation accepts either `template_key` or `method_version_id`, never both as active choices. Only an approved same-tenant organisation method is accepted.

## Platform administration (Phase 18B)

Public contact configuration is available at `GET /api/v1/public/configuration/`.

Authenticated users with an active platform-administrator capability may use:

- `GET /api/v1/platform-admin/overview/`
- `GET /api/v1/platform-admin/organisations/`
- `POST /api/v1/platform-admin/organisations/{id}/support-access/`
- `GET /api/v1/platform-admin/organisations/{id}/`
- `POST /api/v1/platform-admin/organisations/{id}/ownership/`
- `POST /api/v1/platform-admin/organisations/{id}/state/`
- `GET /api/v1/platform-admin/users/`
- `GET/PATCH /api/v1/platform-admin/configuration/`
- demo-request, administrator-capability, invitation-action, and audit endpoints under the same prefix.

Tenant detail and operational endpoints enforce an active, unexpired support-access grant and append audit records. Platform authority does not imply organisation membership.
