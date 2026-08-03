# Known issues

Tracked as of Phase 19 (2026-08-03). Move an item to a release note once it
is resolved; do not delete history from this file, mark it resolved instead.

## Needs an explicit owner decision

### `react-router` high-severity advisory (GHSA-qwww-vcr4-c8h2)

`npm audit` flags `react-router` (pulled in by `react-router-dom@7.18.1`) for
a CSRF bypass in its RSC/framework server-action mode. This app uses
`createBrowserRouter` as a plain client-side SPA with no loaders, actions, or
server mode, so the advisory does not appear to be exploitable here — but the
installed version is still in the flagged range (`>=7.12.0 <8.3.0`). The only
fix is a major-version upgrade (7.x → 8.3.0+), which is a real breaking
change for routing across the whole app and needs deliberate testing, not a
blind `npm audit fix --force`. Recommended: schedule this as its own small
branch with full route-by-route manual verification before merging.

### Old failed-phase Docker volumes remain on disk

The failed-phase containers, their custom-built images, and the build cache
were removed (see "Fixed in Phase 19" below), reclaiming roughly 50 GB. Their
named Docker volumes (`crowdsmarter-phaseN-failed-*_postgres_data`,
`_media_data`, `_frontend_node_modules`, plus `crowdsmarter-v1_crowdsmarter_postgres`
and the `phase301-backup-*` volumes) were deliberately left untouched — the
master prompt's non-negotiable rule against deleting PostgreSQL/Redis volumes
applies regardless of whether the stack is still active. They account for
only ~1 GB combined, so reclaiming them isn't necessary for disk pressure;
remove them only if the owner explicitly confirms none contain data worth
keeping:

```bash
docker volume ls | grep -E "phase.*-failed|phase301-backup|crowdsmarter-v1"
docker volume rm <ids>          # only after explicit confirmation
```

## Fixed in Phase 19

- A real personal email address (the repository owner's) was committed as
  test input in `backend/apps/accounts/tests/test_commands.py` at `3cc6459`
  and published to `origin/main` on GitHub. Rewrote history with
  `git filter-repo` (verified zero matches remain anywhere in history on any
  branch, and that the rewrite changed only that one line, nothing else),
  backed up both trees first, and force-pushed the cleaned history to
  `origin/main` and `origin/claude/phase-19-stabilisation`. The 13 open
  Dependabot PRs are now based on superseded commits and will be recreated
  automatically by Dependabot's next run.
- Removed 34 stopped/idle containers and their images from ten abandoned
  upgrade attempts (`crowdsmarter-phase6-failed-*` through
  `crowdsmarter-phase17-failed-*`, `crowdsmarter-phase301-backup-*`,
  `crowdsmarter-v1-*`), then cleared the build cache. Reclaimed ~24 GB of
  build cache and ~35 GB of images; the live stack was unaffected throughout.
  No volumes were touched — see above.

- DRF `min_value should be an integer or Decimal instance` warning — two
  `DecimalField(min_value=0.01)` float literals in
  `backend/apps/evaluations/serializers.py` changed to `Decimal("0.01")`.
- `apps/contributions/views.py` calling `create_request()` with a missing
  required `reviewer_id` keyword-only argument whenever a client omitted an
  optional reviewer — the service now defaults it to `None`.
- `apps/contributions/services.py` `update_request`/`submit_request` using
  `select_for_update()` combined with `select_related("reviewer")` (a
  nullable FK), which PostgreSQL rejects (`FOR UPDATE cannot be applied to
  the nullable side of an outer join`) — fixed with
  `select_for_update(of=("self",))`.
- `DecisionQualityReview.answers` (`JSONField(default=dict)`, no
  `blank=True`) rejected its own default value on `full_clean()` — added
  `blank=True` plus migration `decision_analysis.0002_...`.
- `DecisionMethodVersionDetailView` had no `GET` handler at all (405 instead
  of a tenant-safe 404 for invisible drafts) — added, reusing the existing
  `version_for_user` selector.
- `OrganisationInvitation.clean()` normalised the email *after* Django's
  `full_clean()` had already validated the raw, unstripped value — moved
  normalisation into an overridden `full_clean()` so it runs first.
- ~15 backend permission tests (`organisations`, `participants`,
  `invitations`, `workspaces`, `decisions`) passed a raw `WSGIRequest` into
  `has_object_permission()` instead of wrapping it in DRF's `Request`, so
  `force_authenticate`'s `.user` never resolved — not a production defect,
  DRF's own `dispatch()` always wraps requests correctly; test-only fix.
- `test_demo_request_is_rate_limited` replaced the whole `REST_FRAMEWORK`
  settings dict via `override_settings`, but DRF binds
  `SimpleRateThrottle.THROTTLE_RATES` as a class attribute at import time —
  `override_settings` never reaches it. Fixed by monkeypatching the throttle
  class's `.rate` directly, matching the existing pattern already used for
  `LoginRateThrottle` in `apps/accounts/tests/test_api.py`.
- Several isolated test bugs: a stale `create_request` email mismatch, a
  duplicate `organisation=` kwarg passed to the `decision_factory` fixture, a
  `pytest.raises(match=...)` regex not matching the actual error text (two
  instances), a `logger.exception` mock asserted outside its `patch(...)`
  context, and two stale in-memory `candidate.portfolio` FK caches read
  before a portfolio status transition landed in the database.
- Frontend: `vite.config.ts` had no `test.exclude` for `e2e/`, so `npm test`
  (Vitest) tried to execute Playwright specs and failed on all four with
  "Playwright Test did not expect test() to be called here."
- Frontend: Testing Library's default 1000ms `findBy`/`waitFor` timeout and
  Vitest's default 5000ms per-test timeout were both too tight for full-suite
  parallel execution in this environment, causing correctly-rendering
  components to fail non-deterministically. Raised both globally
  (`asyncUtilTimeout: 5000`, `testTimeout: 15000`).
- Four component tests used synchronous `getByRole`/`getByText` immediately
  after an unrelated `findByRole` resolved, racing a second, separately
  async-resolving query; one used an exact-string `getByText` against text
  split across a compound JSX expression; one `getByText` was ambiguous
  because the same name legitimately appears twice in the rendered page (a
  canvas summary and an owner-select dropdown option).
- Frontend `npm audit`: `brace-expansion` DoS fixed via `npm audit fix`
  (non-breaking). `react-router` left open — see above.

## Deferred, not started

- Backend dependency lockfile (`pip-compile` or `uv lock`) — needs a
  Dockerfile change to install the tool, out of scope for this phase's
  "fix what's broken" boundary; flagged for a follow-up.
- Frontend production bundle is 939.71 kB (one chunk); route-level code
  splitting was not attempted this phase — it's a performance concern, not a
  correctness one.
- ADR duplicate numbering (0014, 0015, 0016 each shared by two unrelated
  ADRs) — content is fine, only numbering collides; needs a renumbering pass
  with a documented mapping.
- `docs/product-capability-matrix.md` and `docs/roadmap.md` — not yet
  written; need a full feature-by-app audit pass, deferred from this phase.
- 13 open Dependabot PRs on `origin` (pip: Django, DRF, dj-database-url,
  gunicorn, pytest-cov; npm: eslint-plugin-react-hooks, eslint/js,
  hookform/resolvers, prettier, react-router-dom; GitHub Actions bumps) —
  not reviewed or merged in this phase.
