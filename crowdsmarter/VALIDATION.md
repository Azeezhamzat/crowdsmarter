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
3. secure debug-only provisioning of `owner@crowdsmarter.local`;
4. `manage.py check`;
5. migration-drift verification;
6. methodology and organisation-administration tests;
7. authentication, invitation, decision, contribution, search, export, and analysis regressions;
8. full frontend TypeScript checking;
9. focused methodology, administration, navigation, authentication, landing, and demo-request tests;
10. the production Vite build;
11. backend, homepage, login, application, methods, and administration route health checks.

## Local login boundary

The upgrader creates or repairs `owner@crowdsmarter.local` only when `DJANGO_DEBUG=true`. It assigns a generated strong password, ensures an active owner membership, and writes the secret to a mode-`0600` file in `~/Downloads`. The requested weak password `a fixed weak password` is not embedded, printed, or placed in shell history.

## Environment limitation

The release-building environment does not include Django, DRF, the complete npm dependency tree, or Docker. Dependency-backed tests and builds cannot be executed during packaging. They remain mandatory in the supplied upgrader, which cannot report Phase 17 success unless they pass.
