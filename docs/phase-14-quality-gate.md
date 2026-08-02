# Phase 14 quality gate

Phase 14 is complete only when the following behaviour passes in Docker with PostgreSQL.

## Decision-evaluation behaviour

- every exercise belongs to one organisation and one decision from that organisation;
- owners are active organisation members and only contribution-capable active participants may submit;
- scorecard responses reference active options and exercise criteria, stay inside configured scales, and include bounded confidence;
- approval ballots accept only approve or abstain; consent ballots accept only consent, concern, object, or abstain;
- each contributor has one editable submission per round and cannot submit for another person;
- blind open rounds reveal only the viewer's submission and no aggregate result;
- peer-anonymous records remain system-attributable while peer responses use neutral labels;
- quorum, approval, objection, confidence dispersion, and criterion-weight sensitivity remain explicit;
- Delphi exercises support successive numbered rounds and facilitator-authored feedback summaries;
- minority reports remain attributable, exportable, searchable, and linked to the relevant exercise and optional round;
- no aggregate result finalises a decision or advances its lifecycle automatically.

## Portfolio-prioritisation behaviour

- portfolios, criteria, candidates, assessments, and selections remain within one organisation;
- candidate decisions are unique within a portfolio and belong to the portfolio organisation;
- criteria have positive weights and assessments use scores from 0 to 100 with confidence from 1 to 5;
- active contributors assess only for themselves;
- blind open portfolios hide aggregate candidate scores and recommendations;
- peer-anonymous assessments do not disclose assessor identity to peers;
- budget and capacity constraints are non-negative and optional;
- mandatory candidates, score order, resource use, and exclusion reasons are visible after closure;
- the recommendation is deterministic, explainable, and stored separately from authority selections;
- managers record selections, approved resources, ordering, and rationale without altering source decisions.

## Platform integration

- every Phase 14 route requires authentication and tenant outsiders receive 404;
- strict serializers reject unknown command fields;
- service functions own transactional commands and create audit events;
- opening and closing evaluation rounds creates bounded in-app notifications;
- organisation search covers evaluation exercises, minority reports, and prioritisation portfolios;
- organisation exports contain all Phase 14 datasets and decision dossiers include linked evaluation and prioritisation records;
- active evaluation and portfolio ownership blocks unsafe member offboarding;
- frontend routes are reachable from the decision and organisation workspaces and from quick navigation;
- narrow-screen, keyboard, loading, error, empty, and sealed-result states remain usable.

## Operational behaviour

- migration `evaluations.0001_initial` applies without drift and preserves all Phase 13 records;
- focused backend tests, TypeScript checks, Vitest tests, and the production Vite build pass;
- both backend and frontend health checks pass after migration;
- the upgrade script verifies the archive, backs up PostgreSQL, preserves Phase 13 source, and restores both source and database after any failed validation step;
- Docker volumes are never deleted by the upgrader.
