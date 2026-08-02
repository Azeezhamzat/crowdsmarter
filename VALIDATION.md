# Validation status

## Completed in this release environment

- Python AST parsing and bytecode compilation across 274 backend source and migration files.
- Local absolute-import resolution for the `apps` and `crowdsmarter` packages.
- Python line-length checks for all 242 non-migration backend files, with no lines over 100 characters.
- JSON, TOML, and YAML parsing across repository configuration.
- Shell syntax validation for all repository scripts, including the Phase 5 one-terminal upgrade script.
- TypeScript compiler parsing across 55 TypeScript and TSX files, including frontend source, tests, configuration, and Playwright specifications, with zero syntax errors. Full type resolution requires the project dependency tree.
- CSS structural-balance checks.
- Source scans for merge markers, unresolved implementation markers, and packaged private-key indicators.
- Manual model/migration consistency review for `reviews.DecisionReview` and `lessons.Lesson`.
- Manual review of tenant isolation, post-finalisation authority, optimistic concurrency, implementation-owner transfer, offboarding protection, archive immutability, lesson retirement, search scoping, and generic-transition bypass prevention.
- Public-route review confirming that `/` performs no authenticated API call and `/app` remains protected by Django session verification.
- Documentation consistency review for the complete eleven-state lifecycle and the single-deployment public/product architecture.
- Test inventory review: 181 backend test functions across 55 backend test files; eight focused review tests, six lesson tests, three PostgreSQL search tests; nine frontend unit-test files; and two Playwright specifications.

## Supplied but not executable in this release environment

The release-building environment does not contain Django/DRF or the project npm dependency tree. Docker is also unavailable. Runtime claims are therefore deliberately limited. The following checks are supplied but are not claimed as executed here:

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
ruff check .
ruff format --check .
mypy crowdsmarter apps
pytest --cov=apps --cov-report=term-missing --cov-fail-under=85

cd ../frontend
npm run lint
npm run typecheck
npm test -- --run
npm run build
npm run test:e2e
```

## Checks performed by the one-terminal upgrade script

The supplied Linux upgrade script verifies the archive checksum, preserves the existing database and Phase 4 source, builds the Docker images, applies migrations, and uses the installed container dependencies to run:

```bash
docker compose exec backend python manage.py check
docker compose exec backend python manage.py makemigrations --check --dry-run
docker compose exec backend python manage.py showmigrations reviews lessons decisions
docker compose exec backend pytest \
  apps/reviews \
  apps/lessons \
  apps/search \
  apps/organisations/tests/test_services.py::test_remove_member_requires_active_implementation_transfer \
  apps/decisions/tests/test_services.py::test_post_decision_transition_uses_dedicated_outcome_workflow

docker compose exec frontend npm run typecheck
docker compose exec frontend npm test -- --run \
  src/features/landing/LandingPage.test.tsx \
  src/features/outcomes/DecisionOutcomesPage.test.tsx \
  src/features/search/OrganisationSearchPage.test.tsx
docker compose exec frontend npm run build
```

The script stops on the first failed check, prints backend diagnostics, and preserves both a PostgreSQL dump and the previous Phase 4 source directory. A successful migration-drift check must report `No changes detected`.

## Production gate still required

Before public deployment, run the complete PostgreSQL-backed backend suite, frontend lint/typecheck/unit/build suite, and Playwright tests against the production same-origin container. Rehearse database backup and restoration, complete an independent accessibility review of both public and authenticated routes, and perform an independent security review before storing customer data.
