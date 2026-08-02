#!/usr/bin/env bash
set -Eeuo pipefail

DOWNLOADS_DIR="${HOME}/Downloads"
CURRENT_DIR="${DOWNLOADS_DIR}/crowdsmarter"
ARCHIVE="${DOWNLOADS_DIR}/crowdsmarter-phase18a.zip"
CHECKSUM="${DOWNLOADS_DIR}/crowdsmarter-phase18a.zip.sha256"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGING_DIR="$(mktemp -d "${DOWNLOADS_DIR}/crowdsmarter-phase18a-stage-XXXXXX")"
BACKUP_DIR="${DOWNLOADS_DIR}/crowdsmarter-frontend-before-phase18a-${STAMP}"
INVALID_DIR="${DOWNLOADS_DIR}/crowdsmarter-frontend-incomplete-before-phase18a-${STAMP}"
LOCK_FILE="${DOWNLOADS_DIR}/.crowdsmarter-phase18a-upgrade.lock"
VERIFY_IMAGE="crowdsmarter-frontend-phase18a-verify:${STAMP}"
STAGE="preflight"
SWAPPED=0
VALID_BACKUP=0
RESTORE_ATTEMPTED=0

export COMPOSE_PROJECT_NAME=crowdsmarter

say() {
  printf '\n%s\n' "$1"
}

fail() {
  printf '\nUpgrade stopped: %s\n' "$1" >&2
  return 1
}

cleanup() {
  docker image rm -f "${VERIFY_IMAGE}" >/dev/null 2>&1 || true
  rm -rf -- "${STAGING_DIR}" >/dev/null 2>&1 || true
}

frontend_tree_is_complete() {
  local root="$1"
  [[ -f "${root}/Dockerfile" ]] \
    && [[ -f "${root}/package.json" ]] \
    && [[ -f "${root}/src/router.tsx" ]] \
    && [[ -f "${root}/src/components/AppShell.tsx" ]] \
    && [[ -f "${root}/src/features/landing/LandingPage.tsx" ]]
}

remove_frontend_tree_safely() {
  local target="$1"
  [[ -d "${target}" ]] || return 0

  docker run --rm \
    -v "${target}:/target" \
    node:22-alpine \
    sh -c 'find /target -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +' \
    >/dev/null 2>&1 || true

  rm -rf -- "${target}" >/dev/null 2>&1 || true
}

restore_previous_frontend() {
  [[ "${SWAPPED}" -eq 1 ]] || return 0
  [[ "${VALID_BACKUP}" -eq 1 ]] || return 0
  [[ "${RESTORE_ATTEMPTED}" -eq 0 ]] || return 0
  RESTORE_ATTEMPTED=1

  printf '\nRestoring the complete pre-upgrade frontend.\n' >&2
  (
    cd "${CURRENT_DIR}"
    docker compose stop frontend >/dev/null 2>&1 || true
    docker compose rm -f frontend >/dev/null 2>&1 || true
  )

  remove_frontend_tree_safely "${CURRENT_DIR}/frontend"
  mv "${BACKUP_DIR}" "${CURRENT_DIR}/frontend"
  SWAPPED=0

  (
    cd "${CURRENT_DIR}"
    docker compose build frontend >&2 || true
    docker compose up -d --no-deps --force-recreate frontend >&2 || true
  )
}

on_exit() {
  local status="$?"
  trap - EXIT ERR
  if [[ "${status}" -ne 0 ]]; then
    printf '\nPhase 18A failed during: %s.\n' "${STAGE}" >&2
    restore_previous_frontend
    printf 'PostgreSQL was not dumped, migrated, dropped, or restored.\n' >&2
    printf 'The backend source and Docker volumes were not modified.\n' >&2
    if [[ "${VALID_BACKUP}" -eq 0 && -d "${CURRENT_DIR}/frontend" ]]; then
      printf 'The fully prevalidated Phase 18A frontend source remains at: %s\n' "${CURRENT_DIR}/frontend" >&2
    fi
  fi
  cleanup
  exit "${status}"
}
trap on_exit EXIT

command -v docker >/dev/null 2>&1 || fail "Docker is not installed."
docker compose version >/dev/null 2>&1 || fail "Docker Compose is unavailable."
command -v unzip >/dev/null 2>&1 || fail "Install unzip, then rerun: sudo apt install unzip"
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum is unavailable."
command -v curl >/dev/null 2>&1 || fail "Install curl, then rerun: sudo apt install curl"

if command -v flock >/dev/null 2>&1; then
  exec 9>"${LOCK_FILE}"
  flock -n 9 || fail "Another CrowdSmarter Phase 18A upgrade is already running."
fi

if ! docker info >/dev/null 2>&1; then
  cat >&2 <<'MESSAGE'

Docker permission is not active in this terminal.
Run these commands in the same terminal:

  newgrp docker
  bash ~/Downloads/upgrade-crowdsmarter-to-phase18a.sh
MESSAGE
  exit 1
fi

[[ -d "${CURRENT_DIR}" ]] || fail "Current CrowdSmarter project not found at ${CURRENT_DIR}."
[[ -f "${CURRENT_DIR}/docker-compose.yml" ]] || fail "The current project folder is incomplete."
[[ -f "${CURRENT_DIR}/.env" ]] || fail "The current .env file was not found."
[[ -f "${ARCHIVE}" ]] || fail "Download crowdsmarter-phase18a.zip into ${DOWNLOADS_DIR}."
[[ -f "${CHECKSUM}" ]] || fail "Download crowdsmarter-phase18a.zip.sha256 into ${DOWNLOADS_DIR}."

STAGE="archive verification"
say "1/10 Verifying the Phase 18A archive"
(
  cd "${DOWNLOADS_DIR}"
  sha256sum -c "$(basename "${CHECKSUM}")"
)
unzip -tq "${ARCHIVE}" >/dev/null
unzip -q "${ARCHIVE}" -d "${STAGING_DIR}"
STAGED_PROJECT="${STAGING_DIR}/crowdsmarter"
STAGED_FRONTEND="${STAGED_PROJECT}/frontend"
frontend_tree_is_complete "${STAGED_FRONTEND}" \
  || fail "The Phase 18A archive does not contain a complete frontend source tree."

grep -Fq '"version": "0.18.0"' "${STAGED_FRONTEND}/package.json" \
  || fail "The staged frontend is not version 0.18.0."
grep -Fq 'export function RouteAccessibility' "${STAGED_FRONTEND}/src/components/RouteAccessibility.tsx" \
  || fail "Route accessibility management is missing."
grep -Fq 'Skip to main content' "${STAGED_FRONTEND}/src/components/RouteAccessibility.tsx" \
  || fail "The global skip link is missing."
grep -Fq '{ path: "*", element: <NotFoundPage /> }' "${STAGED_FRONTEND}/src/router.tsx" \
  || fail "The not-found route is missing."
grep -Fq 'Phase 18A — accessibility remediation foundation' "${STAGED_FRONTEND}/src/styles.css" \
  || fail "The Phase 18A accessibility styles are missing."
grep -Fq 'role="combobox"' "${STAGED_FRONTEND}/src/components/AppShell.tsx" \
  || fail "Accessible quick navigation is missing."
grep -Fq 'aria-orientation="horizontal"' "${STAGED_FRONTEND}/src/features/landing/LandingPage.tsx" \
  || fail "The complete workflow-tab pattern is missing."
grep -Fq 'role="alert"' "${STAGED_FRONTEND}/src/components/FieldError.tsx" \
  || fail "Field-error announcements are missing."
if grep -R -E '<main[^>]+className="(evaluation-main|contribution-list)' \
  "${STAGED_FRONTEND}/src/features/evaluations" \
  "${STAGED_FRONTEND}/src/features/contributions" >/dev/null; then
  fail "Nested main landmarks remain in authenticated workspaces."
fi

STAGE="candidate image build"
say "2/10 Building an isolated candidate frontend image"
docker build \
  --target development \
  --tag "${VERIFY_IMAGE}" \
  "${STAGED_FRONTEND}"

STAGE="candidate quality gate"
say "3/10 Running TypeScript, accessibility, regression, and production-build checks"
docker run --rm "${VERIFY_IMAGE}" npm run typecheck
docker run --rm "${VERIFY_IMAGE}" npm test -- --run \
  src/components/RouteAccessibility.test.tsx \
  src/components/AppShell.test.tsx \
  src/features/not-found/NotFoundPage.test.tsx \
  src/features/landing/LandingPage.test.tsx \
  src/features/demo-request/RequestDemoPage.test.tsx \
  src/features/auth/LoginPage.test.tsx \
  src/features/auth/ForgotPasswordPage.test.tsx \
  src/features/auth/ResetPasswordPage.test.tsx
docker run --rm "${VERIFY_IMAGE}" npm run build

STAGE="backend verification"
say "4/10 Verifying the existing backend"
curl --silent --fail --output /dev/null http://localhost:8000/health/live/ \
  || fail "The existing backend is not available at http://localhost:8000. Start CrowdSmarter, then rerun."

STAGE="live frontend backup"
say "5/10 Stopping and preserving the current frontend"
cd "${CURRENT_DIR}"
docker compose stop frontend >/dev/null 2>&1 || true
docker compose rm -f frontend >/dev/null 2>&1 || true

if [[ -d "${CURRENT_DIR}/frontend" ]]; then
  if frontend_tree_is_complete "${CURRENT_DIR}/frontend"; then
    mv "${CURRENT_DIR}/frontend" "${BACKUP_DIR}"
    VALID_BACKUP=1
    printf 'Complete frontend backup: %s\n' "${BACKUP_DIR}"
  else
    mv "${CURRENT_DIR}/frontend" "${INVALID_DIR}"
    printf 'The previous frontend tree was incomplete and was preserved for inspection at:\n  %s\n' "${INVALID_DIR}"
  fi
fi

STAGE="atomic frontend installation"
say "6/10 Installing the prevalidated Phase 18A frontend"
mv "${STAGED_FRONTEND}" "${CURRENT_DIR}/frontend"
SWAPPED=1

STAGE="canonical image build"
say "7/10 Building the canonical frontend image"
cd "${CURRENT_DIR}"
docker compose build frontend

STAGE="frontend startup"
say "8/10 Starting the live frontend"
docker compose up -d --no-deps --force-recreate frontend

for _ in {1..45}; do
  if curl --silent --fail --output /dev/null http://localhost:5173/; then
    break
  fi
  sleep 1
done
curl --silent --fail --output /dev/null http://localhost:5173/ \
  || fail "The homepage did not respond after frontend recreation."

STAGE="live source verification"
say "9/10 Verifying the exact source mounted in the running container"
docker compose exec -T frontend sh -c \
  "grep -Fq '\"version\": \"0.18.0\"' /app/package.json" \
  || fail "The running frontend is not Phase 18A."
docker compose exec -T frontend sh -c \
  "grep -Fq 'export function RouteAccessibility' /app/src/components/RouteAccessibility.tsx" \
  || fail "The running frontend does not contain route accessibility management."
docker compose exec -T frontend sh -c \
  "grep -Fq 'Phase 18A — accessibility remediation foundation' /app/src/styles.css" \
  || fail "The running frontend does not contain the Phase 18A accessibility styles."
docker compose exec -T frontend sh -c \
  "grep -Fq '{ path: \"*\", element: <NotFoundPage /> }' /app/src/router.tsx" \
  || fail "The running frontend does not contain the not-found route."
docker compose exec -T frontend sh -c \
  "grep -Fq 'role=\"combobox\"' /app/src/components/AppShell.tsx" \
  || fail "The running frontend does not contain accessible quick navigation."

STAGE="live route verification"
say "10/10 Verifying public and recovery routes"
for route in request-demo login forgot-password missing-destination; do
  curl --silent --fail --output /dev/null "http://localhost:5173/${route}" \
    || fail "The /${route} route did not respond."
done

trap - EXIT ERR
SWAPPED=0
cleanup
cat <<MESSAGE

CrowdSmarter Phase 18A is running successfully.

Open:
  Homepage:       http://localhost:5173/
  Request demo:   http://localhost:5173/request-demo
  Sign in:        http://localhost:5173/login
  Not-found test: http://localhost:5173/missing-destination

The candidate frontend was fully type-checked, accessibility-tested,
regression-tested, and production-built before the live frontend was replaced.

No PostgreSQL command was run. No migration or database restore occurred.
The backend source and Docker volumes were not modified.

$(if [[ "${VALID_BACKUP}" -eq 1 ]]; then printf 'Previous complete frontend backup:\n  %s\n' "${BACKUP_DIR}"; else printf 'No complete prior frontend backup was available; the incomplete tree was preserved at:\n  %s\n' "${INVALID_DIR}"; fi)

After confirming keyboard navigation and the public routes, keep the backup until
Phase 18A has also been synchronized to GitHub.
MESSAGE
