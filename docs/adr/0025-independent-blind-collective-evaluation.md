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
