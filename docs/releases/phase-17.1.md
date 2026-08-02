# Phase 17.1 corrective release

Phase 17.1 repairs the Phase 17 frontend quality gate and the upgrade rollback controller. It does not change the Phase 17 business scope or database schema.

## Corrections

- fixes all TypeScript strict-mode regressions reported by the Phase 17 upgrader;
- keeps decision-template provenance fields present in legacy test fixtures;
- narrows optional indexed values before mutations;
- aligns the demo-request schema input and form type;
- exposes membership-history notes in the administration table;
- updates guided-decision and command-palette tests for Phase 17 dependencies and navigation;
- pins Docker Compose to the `crowdsmarter` project;
- exits immediately after any failed validation and completed rollback;
- prevents false success messages, secondary failed-project stacks, port collisions, empty health-check container IDs, and lost credentials paths.

The local login remains `hello@crowdsmarter.com`. A strong temporary password is generated only after migrations and is retained only when every quality and health check succeeds.
