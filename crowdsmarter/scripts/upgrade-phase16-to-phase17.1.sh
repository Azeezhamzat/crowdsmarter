#!/usr/bin/env bash
set -Eeuo pipefail

# Pin the Compose project so source-directory renames can never create a second stack.
export COMPOSE_PROJECT_NAME="crowdsmarter"

DOWNLOADS_DIR="${HOME}/Downloads"
CURRENT_DIR="${DOWNLOADS_DIR}/crowdsmarter"
ARCHIVE="${DOWNLOADS_DIR}/crowdsmarter-phase17.1.zip"
CHECKSUM="${DOWNLOADS_DIR}/crowdsmarter-phase17.1.zip.sha256"
BACKUP_DIR="${DOWNLOADS_DIR}/crowdsmarter-backups"
STAMP="$(date +%Y%m%d-%H%M%S)"
SOURCE_BACKUP="${DOWNLOADS_DIR}/crowdsmarter-phase16-source-${STAMP}"
FAILED_SOURCE="${DOWNLOADS_DIR}/crowdsmarter-phase17.1-failed-${STAMP}"
DATABASE_BACKUP="${BACKUP_DIR}/crowdsmarter-before-phase17.1-${STAMP}.sql"
LOCAL_ACCESS_FILE="${DOWNLOADS_DIR}/crowdsmarter-local-access-phase17.1-${STAMP}.txt"
LOCAL_ACCESS_STAGING="${CURRENT_DIR}/backend/.phase17.1-local-access.txt"
LOGIN_EMAIL="${CROWDSMARTER_LOCAL_LOGIN_EMAIL:-owner@crowdsmarter.local}"
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
      docker compose logs --tail=200 backend frontend db redis >&2 || true
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
  rm -f "${LOCAL_ACCESS_FILE}" "${LOCAL_ACCESS_STAGING}" 2>/dev/null || true
  [[ "${SOURCE_SWAPPED}" -eq 1 ]] || return 0
  [[ -d "${SOURCE_BACKUP}" ]] || return 0

  printf '\nRestoring the previous Phase 16 source automatically.\n' >&2
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
}

on_error() {
  local status="$1"
  local line="$2"
  trap - ERR
  set +e
  printf '\nUpgrade failed during: %s (script line %s).\n' "${STAGE}" "${line}" >&2
  show_docker_diagnostics
  rollback_release
  if [[ "${SOURCE_SWAPPED}" -eq 0 && -d "${CURRENT_DIR}" && -f "${CURRENT_DIR}/docker-compose.yml" ]]; then
    (cd "${CURRENT_DIR}" && docker compose up -d >&2 || true)
  fi
  [[ -f "${DATABASE_BACKUP}" ]] && printf 'Database backup: %s\n' "${DATABASE_BACKUP}" >&2
  [[ -d "${FAILED_SOURCE}" ]] && printf 'Failed Phase 17.1 source: %s\n' "${FAILED_SOURCE}" >&2
  printf 'Your Docker volumes were not deleted.\n' >&2
  printf 'Never run: docker compose down -v\n' >&2
  exit "${status:-1}"
}
trap 'status=$?; on_error "$status" "$LINENO"' ERR

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
  bash ~/Downloads/upgrade-crowdsmarter-to-phase17.1.sh
MESSAGE
  exit 1
fi

[[ -d "${CURRENT_DIR}" ]] || fail "Current project not found at ${CURRENT_DIR}."
[[ -f "${CURRENT_DIR}/docker-compose.yml" ]] || fail "The current project folder is incomplete."
[[ -f "${CURRENT_DIR}/.env" ]] || fail "The current .env file was not found."
[[ -f "${ARCHIVE}" ]] || fail "Download crowdsmarter-phase17.1.zip directly into ${DOWNLOADS_DIR}."
[[ -f "${CHECKSUM}" ]] || fail "Download crowdsmarter-phase17.1.zip.sha256 directly into ${DOWNLOADS_DIR}."
mkdir -p "${BACKUP_DIR}"

debug_value="$(grep '^DJANGO_DEBUG=' "${CURRENT_DIR}/.env" | tail -n1 | cut -d= -f2- | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]' || true)"
[[ "${debug_value}" =~ ^(1|true|yes|on)$ ]] || fail \
  "This local-access release requires DJANGO_DEBUG=true. It refuses to reset a login in production mode."

STAGE="archive verification"
say "1/13 Verifying the Phase 17.1 download"
(
  cd "${DOWNLOADS_DIR}"
  sha256sum -c "$(basename "${CHECKSUM}")"
)
unzip -tq "${ARCHIVE}" >/dev/null
first_archive_entry="$(unzip -Z1 "${ARCHIVE}" | sed -n '1p')"
[[ "${first_archive_entry}" == crowdsmarter/* ]] \
  || fail "The archive does not contain the expected crowdsmarter/ root folder."

STAGE="stopping Phase 16"
say "2/13 Stopping Phase 16 without deleting data"
# Remove only containers left by the defective Phase 17 upgrader. Volumes are preserved.
legacy_failed_ids="$(
  {
    docker ps -aq --filter 'name=crowdsmarter-phase17-failed-' || true
    docker ps -aq --filter 'name=crowdsmarter-phase17.1-failed-' || true
  } | sort -u
)"
if [[ -n "${legacy_failed_ids}" ]]; then
  docker rm -f ${legacy_failed_ids} >/dev/null || true
fi
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
say "3/13 Starting PostgreSQL and creating a database backup"
docker compose up -d db
wait_for_db "${CURRENT_DIR}" || fail "PostgreSQL did not become ready."
docker compose exec -T db sh -c \
  'pg_dump --clean --if-exists --no-owner --no-privileges --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' \
  > "${DATABASE_BACKUP}"
[[ -s "${DATABASE_BACKUP}" ]] || fail "The PostgreSQL backup file is empty."
DATABASE_BACKED_UP=1
docker compose down --remove-orphans
printf 'Database backup created: %s\n' "${DATABASE_BACKUP}"

STAGE="preserving Phase 16 source"
say "4/13 Preserving the current source and configuration"
cd "${DOWNLOADS_DIR}"
mv "${CURRENT_DIR}" "${SOURCE_BACKUP}"
SOURCE_SWAPPED=1
printf 'Previous source preserved: %s\n' "${SOURCE_BACKUP}"

STAGE="extracting Phase 17.1"
say "5/13 Installing the Phase 17.1 source"
unzip -q "${ARCHIVE}" -d "${DOWNLOADS_DIR}"
[[ -d "${CURRENT_DIR}" ]] || fail "The archive did not create ${CURRENT_DIR}."
[[ -f "${CURRENT_DIR}/docker-compose.yml" ]] || fail "The extracted project is incomplete."
cp "${SOURCE_BACKUP}/.env" "${CURRENT_DIR}/.env"
rm -f "${LOCAL_ACCESS_STAGING}"

STAGE="building containers"
say "6/13 Building the Phase 17.1 backend and frontend"
cd "${CURRENT_DIR}"
docker compose build backend frontend

STAGE="database connectivity and migrations"
say "7/13 Starting PostgreSQL, checking networking, and applying migrations"
docker compose up -d db redis
wait_for_db "${CURRENT_DIR}" || fail "PostgreSQL did not become ready."
docker compose run --rm --no-deps backend \
  python -c "import socket; print('Database address:', socket.gethostbyname('db'))"
docker compose run --rm backend python manage.py migrate

STAGE="requested local login provisioning"
say "8/13 Provisioning secure local access for ${LOGIN_EMAIL}"
docker compose run --rm backend \
  python manage.py provision_local_login \
  --email "${LOGIN_EMAIL}" \
  --first-name "CrowdSmarter" \
  --last-name "Administrator" \
  --organisation "CrowdSmarter Administration" \
  --ensure-owner \
  --credentials-file /app/.phase17.1-local-access.txt
[[ -s "${LOCAL_ACCESS_STAGING}" ]] || fail "The secure local credentials file was not created."
mv "${LOCAL_ACCESS_STAGING}" "${LOCAL_ACCESS_FILE}"
chmod 600 "${LOCAL_ACCESS_FILE}"
LOCAL_ACCESS_CREATED=1
printf 'A fresh temporary password was stored securely at: %s\n' "${LOCAL_ACCESS_FILE}"

STAGE="backend quality checks"
say "9/13 Running Django, methodology, administration, access, and regression checks"
docker compose run --rm backend python manage.py check
docker compose run --rm backend python manage.py makemigrations --check --dry-run
docker compose run --rm backend pytest \
  apps/methodology/tests \
  apps/organisations/tests/test_administration.py \
  apps/organisations/tests/test_services.py \
  apps/organisations/tests/test_api.py \
  apps/accounts/tests/test_api.py \
  apps/accounts/tests/test_models.py \
  apps/accounts/tests/test_commands.py \
  apps/invitations/tests \
  apps/decisions/tests/test_api.py \
  apps/contributions/tests \
  apps/notifications/tests \
  apps/search/tests \
  apps/exports/tests \
  apps/decision_analysis/tests

STAGE="frontend quality checks"
say "10/13 Running frontend type, methodology, administration, navigation, authentication, and build checks"
docker compose run --rm --no-deps frontend npm run typecheck
docker compose run --rm --no-deps frontend npm test -- --run \
  src/features/organisations/OrganisationMethodsPage.test.tsx \
  src/features/organisations/OrganisationAdministrationPage.test.tsx \
  src/components/AppShell.test.tsx \
  src/features/decisions/GuidedDecisionCreatePage.test.tsx \
  src/features/auth/LoginPage.test.tsx \
  src/features/landing/LandingPage.test.tsx \
  src/features/demo-request/RequestDemoPage.test.tsx
docker compose run --rm --no-deps frontend npm run build

STAGE="application startup"
say "11/13 Starting Phase 17.1"
docker compose up -d backend frontend

STAGE="backend health check"
say "12/13 Checking the backend"
for _ in {1..60}; do
  backend_id="$(docker compose ps -q backend 2>/dev/null || true)"
  if [[ -n "${backend_id}" ]]; then
    backend_health="$(docker inspect -f '{{.State.Health.Status}}' "${backend_id}" 2>/dev/null || true)"
    [[ "${backend_health}" == "healthy" ]] && break
  fi
  sleep 2
done
backend_id="$(docker compose ps -q backend 2>/dev/null || true)"
[[ -n "${backend_id}" ]] || fail "The backend container was not created."
[[ "$(docker inspect -f '{{.State.Health.Status}}' "${backend_id}" 2>/dev/null || true)" == "healthy" ]] \
  || fail "The backend did not become healthy."
curl --silent --fail --output /dev/null http://localhost:8000/health/live/ \
  || fail "The backend liveness URL did not respond."

STAGE="frontend and route health checks"
say "13/13 Checking the public site, sign-in, and application routes"
for _ in {1..30}; do
  if curl --silent --fail --output /dev/null http://localhost:5173/; then break; fi
  sleep 2
done
curl --silent --fail --output /dev/null http://localhost:5173/ \
  || fail "The public-site URL did not respond."
curl --silent --fail --output /dev/null http://localhost:5173/login \
  || fail "The sign-in route did not respond."
curl --silent --fail --output /dev/null http://localhost:5173/app \
  || fail "The application route did not respond."

docker compose ps
trap - ERR
SOURCE_SWAPPED=0
cat <<MESSAGE

CrowdSmarter Phase 17.1 is running successfully.

Open these addresses in your browser:
  Professional homepage:  http://localhost:5173/
  Request a demo:         http://localhost:5173/request-demo
  Sign in:                http://localhost:5173/login
  Application:            http://localhost:5173/app
  Organisation methods:   open an organisation → Decision methods
  Administration:         open an organisation → Administration

Guaranteed local login email:
  ${LOGIN_EMAIL}

A newly generated temporary password is stored with owner-only permissions at:
  ${LOCAL_ACCESS_FILE}

Open that file locally, sign in, change the password from Account settings, and delete the file.
The password was not printed to this terminal or placed in shell history.
No fixed default password was used.

Database backup:
  ${DATABASE_BACKUP}

Previous Phase 16 source:
  ${SOURCE_BACKUP}

Do not run: docker compose down -v
MESSAGE
