#!/usr/bin/env bash
set -Eeuo pipefail

DOWNLOADS_DIR="${HOME}/Downloads"
CURRENT_DIR="${DOWNLOADS_DIR}/crowdsmarter"
ARCHIVE="${DOWNLOADS_DIR}/crowdsmarter-phase17.3.zip"
CHECKSUM="${DOWNLOADS_DIR}/crowdsmarter-phase17.3.zip.sha256"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGING_DIR="$(mktemp -d "${DOWNLOADS_DIR}/crowdsmarter-phase17.3-stage-XXXXXX")"
BACKUP_DIR="${DOWNLOADS_DIR}/crowdsmarter-frontend-before-phase17.3-${STAMP}"
INVALID_DIR="${DOWNLOADS_DIR}/crowdsmarter-frontend-incomplete-before-phase17.3-${STAMP}"
LOCK_FILE="${DOWNLOADS_DIR}/.crowdsmarter-phase17.3-upgrade.lock"
VERIFY_IMAGE="crowdsmarter-frontend-phase17.3-verify:${STAMP}"
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
    && [[ -f "${root}/src/features/landing/LandingPage.tsx" ]]
}

remove_frontend_tree_safely() {
  local target="$1"
  [[ -d "${target}" ]] || return 0

  # Docker-created build artefacts may be root-owned. Remove contents through
  # a short-lived container, independently of the project's Dockerfile.
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
    printf '\nPhase 17.3 failed during: %s.\n' "${STAGE}" >&2
    restore_previous_frontend
    printf 'PostgreSQL was not dumped, migrated, dropped, or restored.\n' >&2
    printf 'Docker volumes were not deleted.\n' >&2
    if [[ "${VALID_BACKUP}" -eq 0 && -d "${CURRENT_DIR}/frontend" ]]; then
      printf 'The fully prevalidated Phase 17.3 frontend source remains at: %s\n' "${CURRENT_DIR}/frontend" >&2
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
  flock -n 9 || fail "Another CrowdSmarter Phase 17.3 upgrade is already running."
fi

if ! docker info >/dev/null 2>&1; then
  cat >&2 <<'MESSAGE'

Docker permission is not active in this terminal.
Run these commands in the same terminal:

  newgrp docker
  bash ~/Downloads/upgrade-crowdsmarter-to-phase17.3.sh
MESSAGE
  exit 1
fi

[[ -d "${CURRENT_DIR}" ]] || fail "Current CrowdSmarter project not found at ${CURRENT_DIR}."
[[ -f "${CURRENT_DIR}/docker-compose.yml" ]] || fail "The current project folder is incomplete."
[[ -f "${CURRENT_DIR}/.env" ]] || fail "The current .env file was not found."
[[ -f "${ARCHIVE}" ]] || fail "Download crowdsmarter-phase17.3.zip into ${DOWNLOADS_DIR}."
[[ -f "${CHECKSUM}" ]] || fail "Download crowdsmarter-phase17.3.zip.sha256 into ${DOWNLOADS_DIR}."

STAGE="archive verification"
say "1/9 Verifying the Phase 17.3 archive"
(
  cd "${DOWNLOADS_DIR}"
  sha256sum -c "$(basename "${CHECKSUM}")"
)
unzip -tq "${ARCHIVE}" >/dev/null
unzip -q "${ARCHIVE}" -d "${STAGING_DIR}"
STAGED_PROJECT="${STAGING_DIR}/crowdsmarter"
STAGED_FRONTEND="${STAGED_PROJECT}/frontend"
frontend_tree_is_complete "${STAGED_FRONTEND}" \
  || fail "The Phase 17.3 archive does not contain a complete frontend source tree."

grep -Fq 'Signal sensing workflow' \
  "${STAGED_FRONTEND}/src/features/landing/WorkflowIllustrations.tsx" \
  || fail "The Sense workflow illustration is missing."
grep -Fq 'capability-trace-graphic__flow' \
  "${STAGED_FRONTEND}/src/features/landing/WorkflowIllustrations.tsx" \
  || fail "The readable foresight-to-decision flow is missing."
grep -Fq 'Phase 17.3 — public-site readability and visual hierarchy' \
  "${STAGED_FRONTEND}/src/styles.css" \
  || fail "The Phase 17.3 readability styles are missing."
grep -Fq 'scroll-margin-top: 96px' \
  "${STAGED_FRONTEND}/src/styles.css" \
  || fail "The sticky-header anchor correction is missing."
grep -Fq 'ArrowRight' \
  "${STAGED_FRONTEND}/src/features/landing/LandingPage.tsx" \
  || fail "Keyboard navigation for workflow tabs is missing."
grep -Fq '{ path: "/request-demo", element: <RequestDemoPage /> }' \
  "${STAGED_FRONTEND}/src/router.tsx" \
  || fail "The Request Demo route is missing."

STAGE="candidate image build"
say "2/9 Building an isolated candidate frontend image"
docker build \
  --target development \
  --tag "${VERIFY_IMAGE}" \
  "${STAGED_FRONTEND}"

STAGE="candidate quality gate"
say "3/9 Validating the candidate before touching the live frontend"
docker run --rm "${VERIFY_IMAGE}" npm run typecheck
docker run --rm "${VERIFY_IMAGE}" npm test -- --run \
  src/components/AppShell.test.tsx \
  src/features/landing/LandingPage.test.tsx \
  src/features/demo-request/RequestDemoPage.test.tsx \
  src/features/auth/LoginPage.test.tsx
docker run --rm "${VERIFY_IMAGE}" npm run build

STAGE="backend verification"
say "4/9 Verifying the existing backend"
curl --silent --fail --output /dev/null http://localhost:8000/health/live/ \
  || fail "The existing backend is not available at http://localhost:8000. Start CrowdSmarter, then rerun."

STAGE="live frontend backup"
say "5/9 Stopping and preserving the current frontend"
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
say "6/9 Installing the prevalidated Phase 17.3 frontend"
mv "${STAGED_FRONTEND}" "${CURRENT_DIR}/frontend"
SWAPPED=1

STAGE="compose image build"
say "7/9 Building and starting the canonical frontend"
cd "${CURRENT_DIR}"
docker compose build frontend
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
say "8/9 Verifying the exact source mounted in the running container"
docker compose exec -T frontend sh -c \
  "grep -Fq 'Signal sensing workflow' /app/src/features/landing/WorkflowIllustrations.tsx" \
  || fail "The running frontend does not contain the Sense illustration."
docker compose exec -T frontend sh -c \
  "grep -Fq 'capability-trace-graphic__flow' /app/src/features/landing/WorkflowIllustrations.tsx" \
  || fail "The running frontend does not contain the readable foresight-to-decision flow."
docker compose exec -T frontend sh -c \
  "grep -Fq 'Phase 17.3 — public-site readability and visual hierarchy' /app/src/styles.css" \
  || fail "The running frontend does not contain the Phase 17.3 readability corrections."
docker compose exec -T frontend sh -c \
  "grep -Fq 'scroll-margin-top: 96px' /app/src/styles.css" \
  || fail "The running frontend does not contain the sticky-header anchor correction."
docker compose exec -T frontend sh -c \
  "grep -Fq 'ArrowRight' /app/src/features/landing/LandingPage.tsx" \
  || fail "The running frontend does not contain workflow-tab keyboard navigation."
docker compose exec -T frontend sh -c \
  "grep -Fq '{ path: \"/request-demo\", element: <RequestDemoPage /> }' /app/src/router.tsx" \
  || fail "The running frontend does not contain the Request Demo route."

STAGE="live route verification"
say "9/9 Verifying public routes"
curl --silent --fail --output /dev/null http://localhost:5173/request-demo \
  || fail "The Request Demo route did not respond."
curl --silent --fail --output /dev/null http://localhost:5173/login \
  || fail "The sign-in route did not respond."

trap - EXIT ERR
SWAPPED=0
cleanup
cat <<MESSAGE

CrowdSmarter Phase 17.3 is running successfully.

Open:
  Homepage:      http://localhost:5173/
  Request demo:  http://localhost:5173/request-demo
  Sign in:       http://localhost:5173/login

The candidate frontend was fully type-checked, tested, and production-built
before the live frontend was replaced.

No PostgreSQL command was run. No migration or database restore occurred.
No Docker volume was deleted.

$(if [[ "${VALID_BACKUP}" -eq 1 ]]; then printf 'Previous complete frontend backup:\n  %s\n' "${BACKUP_DIR}"; else printf 'No complete prior frontend backup was available; the incomplete tree was preserved at:\n  %s\n' "${INVALID_DIR}"; fi)

After visually confirming the homepage, you may remove the preserved frontend folder.
MESSAGE
