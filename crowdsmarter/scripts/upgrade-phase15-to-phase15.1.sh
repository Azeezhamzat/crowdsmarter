#!/usr/bin/env bash
set -Eeuo pipefail

DOWNLOADS_DIR="${HOME}/Downloads"
CURRENT_DIR="${DOWNLOADS_DIR}/crowdsmarter"
ARCHIVE="${DOWNLOADS_DIR}/crowdsmarter-phase15.1.zip"
CHECKSUM="${DOWNLOADS_DIR}/crowdsmarter-phase15.1.zip.sha256"
BACKUP_DIR="${DOWNLOADS_DIR}/crowdsmarter-backups"
STAMP="$(date +%Y%m%d-%H%M%S)"
SOURCE_BACKUP="${DOWNLOADS_DIR}/crowdsmarter-phase15-source-${STAMP}"
FAILED_SOURCE="${DOWNLOADS_DIR}/crowdsmarter-phase15.1-failed-${STAMP}"
DATABASE_BACKUP="${BACKUP_DIR}/crowdsmarter-before-phase15.1-${STAMP}.sql"
LOCAL_ACCESS_FILE="${DOWNLOADS_DIR}/crowdsmarter-local-access-${STAMP}.txt"
STAGE="preflight"
SOURCE_SWAPPED=0
DATABASE_BACKED_UP=0
ROLLBACK_STARTED=0
LOCAL_ACCESS_CREATED=0

say() { printf '\n%s\n' "$1"; }
fail() { printf '\nUpgrade stopped: %s\n' "$1" >&2; return 1; }

wait_for_db() {
  local project_dir="$1"
  (
    cd "${project_dir}"
    for _ in {1..60}; do
      if docker compose exec -T db sh -c \
        'pg_isready --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' \
        >/dev/null 2>&1; then
        return 0
      fi
      sleep 1
    done
    return 1
  )
}

show_docker_diagnostics() {
  if [[ -d "${CURRENT_DIR}" && -f "${CURRENT_DIR}/docker-compose.yml" ]]; then
    (
      cd "${CURRENT_DIR}"
      docker compose ps -a >&2 || true
      docker compose logs --tail=180 backend frontend db >&2 || true
    )
  fi
}

restore_database() {
  [[ "${DATABASE_BACKED_UP}" -eq 1 ]] || return 0
  [[ -s "${DATABASE_BACKUP}" ]] || return 0
  [[ -d "${CURRENT_DIR}" && -f "${CURRENT_DIR}/docker-compose.yml" ]] || return 0

  printf '\nRestoring the pre-upgrade PostgreSQL backup.\n' >&2
  (
    cd "${CURRENT_DIR}"
    docker compose up -d db >&2
    wait_for_db "${CURRENT_DIR}" || return 1
    docker compose exec -T db sh -c \
      'psql --set=ON_ERROR_STOP=1 --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" --command="DROP SCHEMA public CASCADE; CREATE SCHEMA public;"' \
      >&2
    docker compose exec -T db sh -c \
      'psql --set=ON_ERROR_STOP=1 --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' \
      < "${DATABASE_BACKUP}" >&2
  )
}

rollback_release() {
  [[ "${ROLLBACK_STARTED}" -eq 0 ]] || return 0
  ROLLBACK_STARTED=1
  [[ "${SOURCE_SWAPPED}" -eq 1 ]] || return 0
  [[ -d "${SOURCE_BACKUP}" ]] || return 0

  printf '\nRestoring the previous Phase 15 source automatically.\n' >&2
  if [[ -d "${CURRENT_DIR}" ]]; then
    (
      cd "${CURRENT_DIR}"
      docker compose down --remove-orphans >&2 || true
    )
    mv "${CURRENT_DIR}" "${FAILED_SOURCE}" || true
  fi
  mv "${SOURCE_BACKUP}" "${CURRENT_DIR}"
  restore_database || printf 'Warning: automatic database restore failed; use the backup shown below.\n' >&2
  (
    cd "${CURRENT_DIR}"
    docker compose up -d >&2 || true
  )
  if [[ "${LOCAL_ACCESS_CREATED}" -eq 1 ]]; then
    rm -f "${LOCAL_ACCESS_FILE}"
  fi
}

on_error() {
  local line="$1"
  set +e
  printf '\nUpgrade failed during: %s (script line %s).\n' "${STAGE}" "${line}" >&2
  show_docker_diagnostics
  rollback_release
  if [[ "${SOURCE_SWAPPED}" -eq 0 && -d "${CURRENT_DIR}" && -f "${CURRENT_DIR}/docker-compose.yml" ]]; then
    (cd "${CURRENT_DIR}" && docker compose up -d >&2 || true)
  fi
  [[ -f "${DATABASE_BACKUP}" ]] && printf 'Database backup: %s\n' "${DATABASE_BACKUP}" >&2
  [[ -d "${FAILED_SOURCE}" ]] && printf 'Failed Phase 15.1 source: %s\n' "${FAILED_SOURCE}" >&2
  printf 'Your Docker volumes were not deleted.\n' >&2
  printf 'Never run: docker compose down -v\n' >&2
}
trap 'on_error "$LINENO"' ERR

command -v docker >/dev/null 2>&1 || fail "Docker is not installed."
docker compose version >/dev/null 2>&1 || fail "Docker Compose is unavailable."
command -v unzip >/dev/null 2>&1 || fail "Install unzip, then rerun: sudo apt install unzip"
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum is unavailable."
command -v curl >/dev/null 2>&1 || fail "Install curl, then rerun: sudo apt install curl"

if ! docker info >/dev/null 2>&1; then
  cat >&2 <<'MESSAGE'

Docker permission is not active in this terminal.
Run these two commands exactly in the same terminal:

  newgrp docker
  bash ~/Downloads/upgrade-crowdsmarter-to-phase15.1.sh
MESSAGE
  exit 1
fi

[[ -d "${CURRENT_DIR}" ]] || fail "Current project not found at ${CURRENT_DIR}."
[[ -f "${CURRENT_DIR}/docker-compose.yml" ]] || fail "The current project folder is incomplete."
[[ -f "${CURRENT_DIR}/.env" ]] || fail "The current .env file was not found."
[[ -f "${ARCHIVE}" ]] || fail "Download crowdsmarter-phase15.1.zip directly into ${DOWNLOADS_DIR}."
[[ -f "${CHECKSUM}" ]] || fail "Download crowdsmarter-phase15.1.zip.sha256 directly into ${DOWNLOADS_DIR}."
mkdir -p "${BACKUP_DIR}"

STAGE="archive verification"
say "1/12 Verifying the Phase 15.1 download"
(
  cd "${DOWNLOADS_DIR}"
  sha256sum -c "$(basename "${CHECKSUM}")"
)
unzip -tq "${ARCHIVE}" >/dev/null
first_archive_entry="$(unzip -Z1 "${ARCHIVE}" | sed -n '1p')"
[[ "${first_archive_entry}" == crowdsmarter/* ]] \
  || fail "The archive does not contain the expected crowdsmarter/ root folder."

STAGE="stopping Phase 15"
say "2/12 Stopping Phase 15 without deleting data"
cd "${CURRENT_DIR}"
docker compose down --remove-orphans
stale_ids="$(docker ps -aq --filter 'label=com.docker.compose.project=crowdsmarter')"
if [[ -n "${stale_ids}" ]]; then docker rm -f ${stale_ids} >/dev/null; fi
for port in 8000 5173; do
  if command -v fuser >/dev/null 2>&1 && fuser "${port}/tcp" >/dev/null 2>&1; then
    cat >&2 <<MESSAGE

Port ${port} is still in use by a non-CrowdSmarter process.
Run this command exactly, then rerun the upgrade script:

  sudo fuser -k 8000/tcp 5173/tcp
MESSAGE
    fail "Port ${port} remains in use."
  fi
done

STAGE="database backup"
say "3/12 Starting PostgreSQL and creating a database backup"
docker compose up -d db
wait_for_db "${CURRENT_DIR}" || fail "PostgreSQL did not become ready."
docker compose exec -T db sh -c \
  'pg_dump --clean --if-exists --no-owner --no-privileges --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' \
  > "${DATABASE_BACKUP}"
[[ -s "${DATABASE_BACKUP}" ]] || fail "The PostgreSQL backup file is empty."
DATABASE_BACKED_UP=1
docker compose down --remove-orphans
printf 'Database backup created: %s\n' "${DATABASE_BACKUP}"

STAGE="preserving Phase 15 source"
say "4/12 Preserving the current source and configuration"
cd "${DOWNLOADS_DIR}"
mv "${CURRENT_DIR}" "${SOURCE_BACKUP}"
SOURCE_SWAPPED=1
printf 'Previous source preserved: %s\n' "${SOURCE_BACKUP}"

STAGE="extracting Phase 15.1"
say "5/12 Installing the Phase 15.1 source"
unzip -q "${ARCHIVE}" -d "${DOWNLOADS_DIR}"
[[ -d "${CURRENT_DIR}" ]] || fail "The archive did not create ${CURRENT_DIR}."
[[ -f "${CURRENT_DIR}/docker-compose.yml" ]] || fail "The extracted project is incomplete."
cp "${SOURCE_BACKUP}/.env" "${CURRENT_DIR}/.env"

ensure_env_value() {
  local key="$1"
  local value="$2"
  if ! grep -q "^${key}=" "${CURRENT_DIR}/.env"; then
    printf '\n%s=%s\n' "${key}" "${value}" >> "${CURRENT_DIR}/.env"
  fi
}
ensure_env_value "API_DEMO_REQUEST_THROTTLE_RATE" "5/hour"
ensure_env_value "DEMO_REQUEST_RECIPIENT" ""
ensure_env_value "LOCAL_BOOTSTRAP_EMAIL" "owner@crowdsmarter.local"
ensure_env_value "LOCAL_BOOTSTRAP_PASSWORD" ""

STAGE="building containers"
say "6/12 Building the Phase 15.1 backend and frontend"
cd "${CURRENT_DIR}"
docker compose build backend frontend

STAGE="database connectivity and migrations"
say "7/12 Starting PostgreSQL, checking networking, and applying migrations"
docker compose up -d db redis
wait_for_db "${CURRENT_DIR}" || fail "PostgreSQL did not become ready."
docker compose run --rm --no-deps backend \
  python -c "import socket; print('Database address:', socket.gethostbyname('db'))"
docker compose run --rm backend python manage.py migrate

STAGE="local access assurance"
say "8/12 Verifying local first-run access without changing existing accounts"
debug_value="$(grep '^DJANGO_DEBUG=' "${CURRENT_DIR}/.env" | tail -n1 | cut -d= -f2- | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')"
if [[ "${debug_value}" =~ ^(1|true|yes|on)$ ]]; then
  local_access_output="$(docker compose run --rm backend python manage.py ensure_local_owner)"
  if grep -q '^LOCAL_ACCESS_CREATED$' <<<"${local_access_output}"; then
    umask 077
    {
      printf 'CrowdSmarter local access created during the Phase 15.1 upgrade.\n\n'
      printf '%s\n' "${local_access_output}"
      printf '\nSign in: http://localhost:5173/login\n'
    } > "${LOCAL_ACCESS_FILE}"
    chmod 600 "${LOCAL_ACCESS_FILE}"
    LOCAL_ACCESS_CREATED=1
    printf 'A first local owner was created; credentials were written to %s\n' "${LOCAL_ACCESS_FILE}"
  else
    printf '%s\n' "${local_access_output}"
  fi
else
  printf 'DJANGO_DEBUG is not enabled; no local bootstrap account was created.\n'
fi

STAGE="backend quality checks"
say "9/12 Running Django, authentication, demo-request, and regression checks"
docker compose run --rm backend python manage.py check
docker compose run --rm backend python manage.py makemigrations --check --dry-run
docker compose run --rm backend pytest \
  apps/demo_requests/tests \
  apps/accounts/tests/test_api.py \
  apps/accounts/tests/test_models.py \
  apps/accounts/tests/test_commands.py \
  apps/invitations/tests/test_api.py \
  apps/decision_analysis/tests \
  apps/organisations/tests/test_api.py \
  apps/decisions/tests/test_api.py

STAGE="frontend quality checks"
say "10/12 Running frontend type, public-site, authentication, and build checks"
docker compose run --rm --no-deps frontend npm run typecheck
docker compose run --rm --no-deps frontend npm test -- --run \
  src/features/landing/LandingPage.test.tsx \
  src/features/demo-request/RequestDemoPage.test.tsx \
  src/features/auth/LoginPage.test.tsx \
  src/features/auth/ForgotPasswordPage.test.tsx \
  src/features/auth/ResetPasswordPage.test.tsx \
  src/components/AppShell.test.tsx \
  src/features/decision-analysis/DecisionAnalysisPage.test.tsx
docker compose run --rm --no-deps frontend npm run build

STAGE="application startup"
say "11/12 Starting Phase 15.1"
docker compose up -d backend frontend

STAGE="health checks"
say "12/12 Checking the public site, demo page, and application services"
for _ in {1..60}; do
  backend_health="$(docker inspect -f '{{.State.Health.Status}}' "$(docker compose ps -q backend)" 2>/dev/null || true)"
  [[ "${backend_health}" == "healthy" ]] && break
  sleep 2
done
[[ "$(docker inspect -f '{{.State.Health.Status}}' "$(docker compose ps -q backend)")" == "healthy" ]] \
  || fail "The backend did not become healthy."
for _ in {1..30}; do
  if curl --silent --fail --output /dev/null http://localhost:5173/; then break; fi
  sleep 2
done
curl --silent --fail --output /dev/null http://localhost:8000/health/live/ \
  || fail "The backend liveness URL did not respond."
curl --silent --fail --output /dev/null http://localhost:5173/ \
  || fail "The public-site URL did not respond."
curl --silent --fail --output /dev/null http://localhost:5173/request-demo \
  || fail "The request-demo page did not respond."

docker compose ps
trap - ERR
SOURCE_SWAPPED=0
cat <<MESSAGE

CrowdSmarter Phase 15.1 is running successfully.

Open these addresses in your browser:
  Professional homepage: http://localhost:5173/
  Request a demo:        http://localhost:5173/request-demo
  Sign in:               http://localhost:5173/login
  Application:           http://localhost:5173/app

If an existing local password is unknown, run:
  bash ~/Downloads/crowdsmarter/scripts/reset-local-password.sh

Database backup:
  ${DATABASE_BACKUP}

Previous Phase 15 source:
  ${SOURCE_BACKUP}
MESSAGE
if [[ "${LOCAL_ACCESS_CREATED}" -eq 1 ]]; then
  cat <<MESSAGE

A first local owner was created because no active account existed.
Credentials were written with owner-only permissions to:
  ${LOCAL_ACCESS_FILE}

Delete that file after signing in and changing the password.
MESSAGE
fi
cat <<'MESSAGE'

Do not run: docker compose down -v
MESSAGE
