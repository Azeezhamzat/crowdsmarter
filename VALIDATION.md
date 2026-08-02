# Phase 17 validation report

## Static validation completed on the exact release tree

The Phase 17 source is checked for:

- Python syntax across the complete backend and migration tree;
- TypeScript/TSX structural parsing and relative-import resolution;
- model-to-migration field coverage for organisation, methodology, and decision additions;
- Django app and route registration;
- method visibility, approval, decision-provenance, search, export, and navigation wiring;
- JSON, TOML, YAML, CSS, Markdown-link, and shell-script structure;
- absence of `.env`, credentials, dependency directories, caches, and generated build output;
- independent ZIP integrity and SHA-256 verification.

## Runtime gates enforced by the upgrader

Before reporting success, `upgrade-crowdsmarter-to-phase17.sh` runs inside the built containers:

1. PostgreSQL readiness and container DNS checks;
2. Django migrations;
3. secure debug-only provisioning of `hello@crowdsmarter.com`;
4. `manage.py check`;
5. migration-drift verification;
6. methodology and organisation-administration tests;
7. authentication, invitation, decision, contribution, search, export, and analysis regressions;
8. full frontend TypeScript checking;
9. focused methodology, administration, navigation, authentication, landing, and demo-request tests;
10. the production Vite build;
11. backend, homepage, login, application, methods, and administration route health checks.

## Local login boundary

The upgrader creates or repairs `hello@crowdsmarter.com` only when `DJANGO_DEBUG=true`. It assigns a generated strong password, ensures an active owner membership, and writes the secret to a mode-`0600` file in `~/Downloads`. The requested weak password `Admin1` is not embedded, printed, or placed in shell history.

## Environment limitation

The release-building environment does not include Django, DRF, the complete npm dependency tree, or Docker. Dependency-backed tests and builds cannot be executed during packaging. They remain mandatory in the supplied upgrader, which cannot report Phase 17 success unless they pass.


## Phase 17.2 release validation

Phase 17.2 adds a frontend-only gate covering TypeScript, focused Vitest regression tests, the Vite production build, the working Request Demo route, five semantically labelled workflow illustrations, and the foresight-to-decision trace. The downloadable installer does not run database commands.
## Phase 17.3 release validation

Phase 17.3 adds a frontend-only readability gate covering sticky-header anchor clearance, minimum supporting-copy font sizes, stronger text contrast, keyboard-operable workflow tabs, enlarged workflow diagrams, and a responsive semantic foresight-to-decision trace. The installer prevalidates the complete candidate before replacing the live frontend and runs no database commands.

## Phase 18A release validation

Phase 18A adds frontend-only accessibility gates covering route-aware document titles, polite route announcements, working skip navigation, one main landmark per public route, nested-main removal in authenticated workspaces, keyboard-complete workflow tabs, command-palette focus containment and restoration, labelled public forms, a named not-found recovery page, minimum target sizing, focus visibility, reduced motion, increased contrast, and forced-colours behaviour. The atomic installer prevalidates TypeScript, focused Vitest suites, and the production build before replacing the live frontend. It runs no migration or PostgreSQL command.

## Phase 18B platform-governance validation

The release packaging gate verifies Python and TypeScript syntax, relative imports, configuration parsing, documentation links, migration numbering, archive integrity, repository hygiene, and absence of private environment files. The upgrade installer is the authoritative runtime gate: it builds the exact candidate images, runs Django migration-drift and governance tests, runs TypeScript and Vitest regression checks, and completes a production frontend build before touching the live source.

Post-installation checks verify both platform-admin migrations, the explicit capability for the named operator, public contact configuration, application health, and the rule that only marked simulated organisations receive automatic owner membership.
