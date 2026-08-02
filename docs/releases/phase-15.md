# Phase 15 release — Integrated decision analysis and executive synthesis

Phase 15 turns CrowdSmarter's existing records into one coherent, option-centred decision picture. It is an additive release over Phase 14 and introduces no automatic option selection or lifecycle authority.

## Customer value

Decision teams can now answer, from one workspace:

- What supports or challenges each option?
- Which sources are credible, unassessed, superseded, or withdrawn?
- Which assumptions remain unverified, low-confidence, invalidated, or overdue for review?
- Where is risk concentrated and which mitigations or reviews are missing?
- Which stakeholders support an option and where does material dissent remain?
- How does the option perform across scenario worlds?
- What did closed collective evaluation rounds find?
- Which contradictions, gaps, objections, vulnerabilities, and implementation uncertainties still require action?
- Is the decision process ready, ready with conditions, or not ready?
- What human-approved synthesis should be presented to the accountable authority?

## New backend domain

`apps.decision_analysis` contains:

- a read-only integrated decision-analysis composition;
- `DecisionIssue` for accepted gaps and contradictions;
- `DecisionQualityReview` for versioned human process-quality judgement;
- `ExecutiveDecisionSummary` for versioned human-approved synthesis;
- tenant-safe selectors, named policies, transactional services, strict serializers, thin API views, audit events, and tests.

## Governance boundaries

- The analysis workspace never selects an option or advances the decision lifecycle.
- Decision-quality answers remain explainable categorical judgements; no universal quality score is calculated.
- Contributors may raise issues, but only the assigned owner or an accountable authority may update them.
- Only organisation managers, the decision owner, and active decision makers may author quality reviews or executive summaries.
- Draft reviews and summaries are hidden from non-authorities.
- Published reviews and approved summaries are immutable; later versions supersede them while preserving history.
- AI may later propose draft language through the existing provider abstraction, but this release creates no silent AI-authored record.

## Integration

Phase 15 adds:

- decision navigation and a responsive React workspace;
- PostgreSQL search for analysis issues and non-superseded executive summaries;
- organisation archive and decision-dossier datasets;
- offboarding protection for unresolved issue ownership;
- audit events for every material issue, review, and summary workflow;
- migration `decision_analysis.0001_initial`;
- a rollback-safe Phase 14 to Phase 15 Linux upgrader.

## Explicit exclusions

This release does not add forecasting, automated recommendations, financial modelling, simulation, an unrestricted whiteboard, AI-created official records, or a new paid service.
