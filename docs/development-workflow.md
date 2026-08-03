# Development workflow

## Canonical source

`~/Downloads/crowdsmarter` is the single canonical Git working tree, tracking
`origin/main` at `https://github.com/Azeezhamzat/crowdsmarter.git`. There is no
second independently edited source tree. A previous separate publishing clone
(`~/Downloads/crowdsmarter-github-publish`) is retained only as a historical
backup and must not be edited directly; if you find yourself about to edit it,
edit this tree instead.

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
- Backend dependencies in `backend/pyproject.toml` use range constraints only
  (no committed lockfile yet). See `docs/known-issues.md` for the plan to add
  one (`pip-compile` or `uv lock`).

## Releases

Releases are tagged from `main` after the quality gates pass, with a
changelog entry and migration notes. See `docs/releases/` for the history of
past phase releases and `docs/known-issues.md` for the plan to formalise this
into semantic versioning with a documented backup and rollback checklist.
