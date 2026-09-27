# Development workflow

## Canonical source

Use one Git clone as the canonical working tree and publish from that clone.
Archive downloads such as `crowdsmarter-main` may not contain `.git` metadata;
changes made in an archive must be copied into a reviewed Git branch before
they can be committed or published.

Runtime-only files — `.env`, `node_modules/`, `dist/`, `staticfiles/`, `media/`,
caches, and local Claude Code settings (`.claude/`) — remain local and ignored.
They are never committed.

## Branching

Work happens on branches cut from `main`, named after the phase or feature,
for example:

```
claude/phase-19-stabilisation
claude/foresight-studio
```

Keep each branch small enough to review and to recover from if something goes
wrong. Commit in reviewable increments with precise messages. Do not amend or
rewrite history that has already been pushed.

## Required steps for a substantial change

1. Confirm current branch, commit, and status (`git status`, `git log --oneline -5`).
2. Inspect the relevant models, services, selectors, serializers, views, tests,
   frontend routes, and documentation before writing code.
3. Implement in small, reviewable increments.
4. Run the quality gates below and fix failures — do not report a change as
   done while a gate is red.
5. Update documentation and ADRs when architecture or behaviour changes.
6. Commit with a message describing what changed and why.
7. Do not push without confirming the intended branch and remote first.

## Quality gates

Run the real equivalents of:

```bash
docker compose config
docker compose exec backend python manage.py check
docker compose exec backend python manage.py makemigrations --check --dry-run
docker compose exec backend pytest
docker compose run --rm frontend npm run typecheck
docker compose run --rm frontend npm test -- --run
docker compose run --rm frontend npm run build
```

Playwright browsers are intentionally installed by the CI runner rather than
inside the small Alpine development image. To run E2E tests directly on a Mac:

```bash
cd frontend
npm ci
npx playwright install chromium
npm run test:e2e
```

Report exact failures. Do not invent a passing result.

## Local environment

```bash
cp .env.example .env
docker compose up -d --build
```

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Django admin: `http://localhost:8000/admin/`
- Platform administration: `http://localhost:5173/platform-admin`

Redis and Celery are optional for synchronous workflows and run under a
profile:

```bash
docker compose --profile workers up -d worker scheduler
```

## Dependency reproducibility

- Frontend dependencies are pinned via `frontend/package-lock.json`. Install
  with `npm ci` in CI and `npm install` locally; do not delete the lockfile.
- Backend's human-maintained ranges remain in `backend/pyproject.toml`; runtime
  and development installations are reproducible through the committed
  hash-locked `requirements.lock` and `requirements-dev.lock` files.

## Releases

Releases are tagged from `main` after the quality gates pass, with a
changelog entry and migration notes. See `docs/releases/` for the history of
past phase releases and `docs/known-issues.md` for the plan to formalise this
into semantic versioning with a documented backup and rollback checklist.
