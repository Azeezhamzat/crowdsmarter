# Known issues

Tracked as of Phase 19 (2026-08-03). Move an item to a release note once it
is resolved; do not delete history from this file, mark it resolved instead.

## Needs an explicit owner decision

### A personal email address needs pushing out of published Git history

`backend/apps/accounts/tests/test_commands.py` contained the repository
owner's real personal email address as test input, committed at `3cc6459`
and already pushed to `origin/main` on GitHub. The working copy is fixed
(reverted to a placeholder `owner@example.test`).

History has been rewritten locally with `git filter-repo` to strip the
address from every commit that ever contained it (verified: zero matches
remain anywhere in the rewritten history, and a full-tree diff against the
original confirms only that one line changed, nothing else). The rewritten
history has **not** been pushed yet — this sandboxed environment has no
GitHub credentials configured, so the force-push has to be run from a
machine that does. A full backup of the pre-rewrite repository (both this
tree and the publishing clone) was taken first. Once pushed, note that the
13 open Dependabot PRs on `origin` will be based on now-superseded commits
and will need to be recreated by Dependabot's next run.

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

### Docker disk usage from historical failed-phase stacks

`docker system df` reports roughly 36 GB reclaimable in images and 15 GB in
build cache, plus several `crowdsmarter-phaseN-failed-*` containers (some
still running Postgres) left over from past upgrade attempts. The master
prompt's non-negotiable rule against deleting PostgreSQL/Redis volumes means
this phase left them untouched. Recommended cleanup, once approved:

```bash
docker ps -a --filter "name=crowdsmarter-phase" --filter "name=failed"
docker container rm <ids>
docker volume rm <ids>          # only after confirming none are needed
docker builder prune
```

Confirm with the owner which (if any) of the failed-phase volumes contain
data worth keeping before removing them.

## Fixed in Phase 19

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
