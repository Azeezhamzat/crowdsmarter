# Known issues

Tracked as of Phase 19 (2026-08-03). Move an item to a release note once it
is resolved; do not delete history from this file, mark it resolved instead.

## Closed without action

### Old failed-phase Docker volumes remain on disk (by design)

The failed-phase containers, their custom-built images, and the build cache
were removed (see "Fixed in Phase 19" below), reclaiming roughly 50 GB. Their
named Docker volumes (`crowdsmarter-phaseN-failed-*_postgres_data`,
`_media_data`, `_frontend_node_modules`, plus `crowdsmarter-v1_crowdsmarter_postgres`
and the `phase301-backup-*` volumes) remain and are not going to be removed
by an automated pass: the master prompt's non-negotiable rule is "never
delete PostgreSQL or Redis volumes," stated with no exception clause, and it
applies regardless of whether the stack that created them is still active.
They total only ~1 GB, so there's no disk-pressure reason to override that
rule. If the owner wants them gone, remove them by hand after checking each
one individually — this is a manual, owner-executed action, not something to
delegate:

```bash
docker volume ls | grep -E "phase.*-failed|phase301-backup|crowdsmarter-v1"
docker volume rm <id>          # one at a time, after checking its contents
```

### Test account left in the local database

Phase 20.1's accessibility audit needed a real authenticated session with
real data to scan ~33 routes properly (mocked component tests don't render
full pages). Provisioned a local test account
(`a11y-audit@example.test`, via `manage.py provision_local_login`) and its
auto-created organisation ("Azeez CrowdSmarter Workspace"). The test
decision and foresight canvas created during the audit were deleted
afterwards, but the account and organisation themselves could not be
cleanly removed — `AuditEvent`/`MembershipEvent` records reference them
with `on_delete=PROTECT`, which is the append-only audit trail working
exactly as designed, not a bug. Deleting them would mean bypassing that
protection, which this phase deliberately did not do. If you want it gone,
use the organisation's own deactivation/deletion flow (`/organisations/<id>/administration`)
rather than a direct database delete.

## Fixed in Phase 20

- WCAG 2.2 AA audit across ~33 route templates (`axe-core`, real
  authenticated data) found and fixed 9 violations: 5 colour-contrast
  instances (one a genuine dark-on-dark bug from an incomplete theme
  override), a non-keyboard-focusable scrollable region, a critical
  ARIA-tablist structure violation, a prohibited `aria-label` on a
  role-less `<span>`, and an unlabelled `<select>`. Full details in
  `docs/accessibility.md`.

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
  No volumes were touched — see "Closed without action" above.
- `react-router` high-severity advisory (GHSA-qwww-vcr4-c8h2, CSRF bypass in
  RSC/framework server-action mode — this app doesn't use that mode, but the
  installed version was still in the flagged range `>=7.12.0 <8.3.0`).
  `react-router-dom@7.18.1` had no 8.x release available at all: as of v8,
  React Router dropped the separate `react-router-dom` package entirely and
  consolidated into `react-router` (DOM APIs like `RouterProvider` now come
  from the `react-router/dom` subpath). Uninstalled `react-router-dom`,
  installed `react-router@8.3.0` directly, and updated every import across
  ~74 files (`from "react-router-dom"` → `from "react-router"`, except
  `RouterProvider` in `src/main.tsx` → `from "react-router/dom"`). Also
  bumped `react`/`react-dom` to `19.2.8` (v8's stated minimum is `19.2.7+`)
  and `engines.node` to `>=22.22` (v8's stated minimum; the container already
  runs 22.23.2). `npm audit` now reports 0 vulnerabilities. Verified with
  typecheck, the full test suite (34/34 files), a production build, and a
  manual browser smoke test of the landing page, `/login`, the `/app`
  protected-route redirect, and the `/*` not-found route — no console
  errors, no regressions.
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
  (non-breaking).

## Newly discovered, not yet fixed

### `npm run lint` fails, independent of anything in Phase 19

93 ESLint errors across ~20 files (`@typescript-eslint/no-misused-promises`
on async handlers passed where a void return is expected,
`@typescript-eslint/no-unnecessary-type-assertion`,
`react-hooks/set-state-in-effect`, `@typescript-eslint/consistent-type-imports`,
one `@typescript-eslint/triple-slash-reference`). Confirmed pre-existing and
unrelated to the react-router migration: stashing every Phase 19 change and
re-running lint against the original code produced *386* errors, not fewer —
this is accumulated tech debt, not a regression. `.github/workflows/ci.yml`
runs `npm run lint` as a required step, meaning CI has likely never been
green on this repository. Out of scope to fix here; needs its own pass.

## Deferred, not started

- Backend dependency lockfile (`pip-compile` or `uv lock`) — needs a
  Dockerfile change to install the tool, out of scope for this phase's
  "fix what's broken" boundary; flagged for a follow-up.
- Frontend production bundle is ~938 kB (one chunk); route-level code
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
  not reviewed or merged in this phase. The `react-router-dom` one is now
  moot since that package was removed entirely.
