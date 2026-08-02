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
