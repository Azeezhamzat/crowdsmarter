# ADR 0025: independent and blind collective evaluation

## Status

Accepted for Phase 14.

## Context

CrowdSmarter already preserves evidence, reasoning, dissent, foresight, scenario review, and human finalisation. Teams still need a governed way to evaluate decision options without anchoring later contributors on early responses or erasing minority positions. A single generic poll would not support the different logics of weighted scorecards, approval, consent, and iterative Delphi inquiry.

## Decision

Introduce a bounded `evaluations` domain linked to one decision. An evaluation exercise declares one method, identity mode, blind-results rule, quorum, and applicable thresholds. Contributions are recorded per participant and round. While a blind round is open, contributors can see only their own submission. Peer-anonymous contributions remain attributable to the system and authorised audit processes but are represented to peers by stable neutral labels.

Scorecards use explicit criteria, weights, bounded scales, confidence, and criterion-weight sensitivity ranges. Approval and consent use method-specific ballots. Delphi exercises may create successive rounds and publish a facilitator-authored feedback summary between rounds. Minority reports remain first-class records rather than comments hidden beneath an aggregate.

Only active decision participants with a contribution-capable role may submit. Managers configure and close rounds but cannot submit on another participant's behalf. Aggregate results advise the accountable authority; they never finalise or transition the decision automatically.

## Consequences

- independent judgement is protected before aggregate influence appears;
- anonymity does not remove system accountability or tenant auditability;
- disagreement, confidence, quorum, and threshold status remain visible;
- method-specific validation prevents ambiguous ballot semantics;
- later forecasting and calibration can reuse the contribution-governance patterns without conflating forecasts with preferences.

## Follow-up: applicant-blind identity and ranked-choice (2026-08)

Two extensions close gaps identified against comparable participatory-grantmaking tools:

- `EvaluationExercise.blind_applicant_identity` hides *which option* is being scored, not just
  *who is scoring it*. When set, a new `GET /evaluations/{exercise_id}/scoring-options/`
  endpoint (`apps.evaluations.services.scoring_options_for_exercise`) returns each active
  option as a stable `"Application A"`, `"Application B"`, … label instead of its real title,
  for any non-manager while the exercise remains open. A manager (`can_manage_exercise`)
  always sees the real title, and the real title is restored for everyone once the exercise
  reaches `closed`/`archived` — blinding protects the scoring moment, not the audit trail.
- A fourth method, `EvaluationExercise.Method.RANKED_CHOICE`, adds a strict-preference ballot:
  `EvaluationResponse.rank` (1..N, no repeats, no criterion/score/vote) replaces the
  score/vote fields for that method. `apps.evaluations.services._instant_runoff` tabulates a
  single-winner instant-runoff (round-by-round elimination of the lowest first-preference
  option, ballots transferring to the next standing preference) rather than full multi-winner
  STV with quota-based surplus transfer — the single-winner case is what a "pick one grant"
  round needs, and the elimination/tally trail is returned in full
  (`EvaluationResults.ranked_choice_rounds`) so the outcome is replayable, not a black box.

Both reuse the existing conflict-of-interest exclusion and quorum/hidden-until-close machinery
unchanged; neither introduces a new identity or anonymity concept beyond what this ADR already
established.
