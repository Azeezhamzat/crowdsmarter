# Phase 13 quality gate

Phase 13 is complete only when the following behaviour passes in Docker with PostgreSQL.

## Domain behaviour

- scenario axes are two different active critical uncertainties from the same canvas;
- scenario-set owners are active members and linked decisions belong to the same organisation;
- each scenario set supports at most one world per quadrant and unique scenario titles and codes;
- driver states reference only drivers from the scenario canvas;
- each member has at most one review per scenario and every 1–5 score is validated;
- confidence dispersion remains visible in the scenario workspace;
- wind-tunnel assessments reference only active options from the scenario set's linked decision;
- signpost scenario links remain inside one scenario set;
- observations may reference only sources from the same organisation;
- scenario implication links remain inside one canvas;
- archived canvases and scenario sets are read-only;
- active scenario-set and signpost ownership blocks unsafe member offboarding;
- material commands create audit events.

## API behaviour

- every Phase 13 route requires authentication;
- tenant outsiders receive 404 rather than object disclosure;
- unknown command fields fail explicitly;
- serializers remain API contracts while services own transactional workflows;
- workspace responses prefetch bounded scenario, review, assessment, implication, signpost, and observation records;
- scenario-set, scenario, signpost, and observation commands return typed records suitable for immediate UI refresh.

## Frontend behaviour

- the existing foresight canvas gains a Scenarios tab rather than a disconnected product area;
- users can construct and understand a genuine 2×2 scenario matrix on desktop and narrow screens;
- incomplete quadrants have clear creation affordances and completed worlds expose narrative and assumptions;
- collective review shows reviewer count, average criteria, and confidence range;
- wind-tunnel results compare linked decision options across scenario worlds without implying an automated recommendation;
- adaptive signposts show ownership, trigger, cadence, scenario relationship, latest observation, and observation history;
- forms retain labels, explicit errors, empty states, keyboard access, and reduced-motion behaviour.

## Operational behaviour

- migration `foresight.0004_scenario_planning` applies without drift;
- existing Phase 12 records remain intact;
- organisation exports contain every Phase 13 dataset;
- decision dossiers contain all scenario records connected to that decision;
- PostgreSQL search returns scenario sets, scenario worlds, and signposts;
- the upgrade script backs up the database, preserves Phase 12 source, verifies both services, and restores both source and database automatically after a failed validation step.
