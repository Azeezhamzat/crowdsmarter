#!/usr/bin/env bash
set -Eeuo pipefail

DOWNLOADS_DIR="${HOME}/Downloads"
CURRENT_DIR="${DOWNLOADS_DIR}/crowdsmarter"
ARCHIVE="${DOWNLOADS_DIR}/crowdsmarter-phase13.zip"
CHECKSUM="${DOWNLOADS_DIR}/crowdsmarter-phase13.zip.sha256"
BACKUP_DIR="${DOWNLOADS_DIR}/crowdsmarter-backups"
STAMP="$(date +%Y%m%d-%H%M%S)"
SOURCE_BACKUP="${DOWNLOADS_DIR}/crowdsmarter-phase12-source-${STAMP}"
FAILED_SOURCE="${DOWNLOADS_DIR}/crowdsmarter-phase13-failed-${STAMP}"
DATABASE_BACKUP="${BACKUP_DIR}/crowdsmarter-before-phase13-${STAMP}.sql"
STAGE="preflight"
SOURCE_SWAPPED=0
DATABASE_BACKED_UP=0
ROLLBACK_STARTED=0

say() {
  printf '\n%s\n' "$1"
}

fail() {
  printf '\nUpgrade stopped: %s\n' "$1" >&2
  return 1
}

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

  printf '\nRestoring the previous Phase 12 source automatically.\n' >&2
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
  local line="$1"
  set +e
  printf '\nUpgrade failed during: %s (script line %s).\n' "${STAGE}" "${line}" >&2
  show_docker_diagnostics
  rollback_release
  [[ -f "${DATABASE_BACKUP}" ]] && printf 'Database backup: %s\n' "${DATABASE_BACKUP}" >&2
  [[ -d "${FAILED_SOURCE}" ]] && printf 'Failed Phase 13 source: %s\n' "${FAILED_SOURCE}" >&2
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
  bash ~/Downloads/upgrade-crowdsmarter-to-phase13.sh
MESSAGE
  exit 1
fi

[[ -d "${CURRENT_DIR}" ]] || fail "Current project not found at ${CURRENT_DIR}."
[[ -f "${CURRENT_DIR}/docker-compose.yml" ]] || fail "The current project folder is incomplete."
[[ -f "${CURRENT_DIR}/.env" ]] || fail "The current .env file was not found."
[[ -f "${ARCHIVE}" ]] || fail "Download crowdsmarter-phase13.zip directly into ${DOWNLOADS_DIR}."
[[ -f "${CHECKSUM}" ]] || fail "Download crowdsmarter-phase13.zip.sha256 directly into ${DOWNLOADS_DIR}."
mkdir -p "${BACKUP_DIR}"

STAGE="archive verification"
say "1/11 Verifying the Phase 13 download"
(
  cd "${DOWNLOADS_DIR}"
  sha256sum -c "$(basename "${CHECKSUM}")"
)
unzip -tq "${ARCHIVE}" >/dev/null
first_archive_entry="$(unzip -Z1 "${ARCHIVE}" | sed -n '1p')"
[[ "${first_archive_entry}" == crowdsmarter/* ]] \
  || fail "The archive does not contain the expected crowdsmarter/ root folder."

STAGE="stopping Phase 12"
say "2/11 Stopping Phase 12 without deleting data"
cd "${CURRENT_DIR}"
docker compose down --remove-orphans
stale_ids="$(docker ps -aq --filter 'label=com.docker.compose.project=crowdsmarter')"
if [[ -n "${stale_ids}" ]]; then
  docker rm -f ${stale_ids} >/dev/null
fi
for port in 8000 5173; do
  if command -v fuser >/dev/null 2>&1 && fuser "${port}/tcp" >/dev/null 2>&1; then
    cat >&2 <<MESSAGE

Port ${port} is still in use by a non-CrowdSmarter process.
Run this command exactly, then rerun the upgrade script:

  sudo fuser -k 8000/tcp 5173/tcp
MESSAGE
    exit 1
  fi
done

STAGE="database backup"
say "3/11 Starting PostgreSQL and creating a database backup"
docker compose up -d db
wait_for_db "${CURRENT_DIR}" || fail "PostgreSQL did not become ready."
docker compose exec -T db sh -c \
  'pg_dump --clean --if-exists --no-owner --no-privileges --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' \
  > "${DATABASE_BACKUP}"
[[ -s "${DATABASE_BACKUP}" ]] || fail "The PostgreSQL backup file is empty."
DATABASE_BACKED_UP=1
docker compose down --remove-orphans
printf 'Database backup created: %s\n' "${DATABASE_BACKUP}"

STAGE="preserving Phase 12 source"
say "4/11 Preserving the current source and configuration"
cd "${DOWNLOADS_DIR}"
mv "${CURRENT_DIR}" "${SOURCE_BACKUP}"
SOURCE_SWAPPED=1
printf 'Previous source preserved: %s\n' "${SOURCE_BACKUP}"

STAGE="extracting Phase 13"
say "5/11 Installing the Phase 13 source"
unzip -q "${ARCHIVE}" -d "${DOWNLOADS_DIR}"
[[ -d "${CURRENT_DIR}" ]] || fail "The archive did not create ${CURRENT_DIR}."
[[ -f "${CURRENT_DIR}/docker-compose.yml" ]] || fail "The extracted project is incomplete."
cp "${SOURCE_BACKUP}/.env" "${CURRENT_DIR}/.env"

STAGE="building containers"
say "6/11 Building the Phase 13 backend and frontend"
cd "${CURRENT_DIR}"
docker compose build backend frontend

STAGE="database connectivity and migrations"
say "7/11 Starting PostgreSQL, checking networking, and applying migrations"
docker compose up -d db redis
wait_for_db "${CURRENT_DIR}" || fail "PostgreSQL did not become ready."
docker compose run --rm --no-deps backend \
  python -c "import socket; print('Database address:', socket.gethostbyname('db'))"
docker compose run --rm backend python manage.py migrate

STAGE="backend quality checks"
say "8/11 Running Django and Phase 13 backend checks"
docker compose run --rm backend python manage.py check
docker compose run --rm backend python manage.py makemigrations --check --dry-run
docker compose run --rm backend pytest \
  apps/foresight/tests/test_scenario_services.py \
  apps/foresight/tests/test_scenario_api.py \
  apps/foresight/tests/test_mapping_services.py \
  apps/foresight/tests/test_mapping_api.py \
  apps/exports/tests/test_api.py \
  apps/search/tests/test_api.py \
  apps/organisations/tests/test_api.py \
  apps/decisions/tests/test_api.py

STAGE="frontend quality checks"
say "9/11 Running frontend type, foresight, navigation, and build checks"
docker compose run --rm --no-deps frontend npm run typecheck
docker compose run --rm --no-deps frontend npm test -- --run \
  src/features/foresight/api.test.ts \
  src/features/foresight/ForesightCanvasesPage.test.tsx \
  src/components/AppShell.test.tsx \
  src/features/decisions/DecisionLifecycle.test.tsx \
  src/features/landing/LandingPage.test.tsx
docker compose run --rm --no-deps frontend npm run build

STAGE="application startup"
say "10/11 Starting Phase 13"
docker compose up -d backend frontend

STAGE="health checks"
say "11/11 Checking both application services"
for _ in {1..60}; do
  backend_health="$(docker inspect -f '{{.State.Health.Status}}' "$(docker compose ps -q backend)" 2>/dev/null || true)"
  [[ "${backend_health}" == "healthy" ]] && break
  sleep 2
done
[[ "$(docker inspect -f '{{.State.Health.Status}}' "$(docker compose ps -q backend)")" == "healthy" ]] \
  || fail "The backend did not become healthy."
for _ in {1..30}; do
  if curl --silent --fail --output /dev/null http://localhost:5173/; then
    break
  fi
  sleep 2
done
curl --silent --fail --output /dev/null http://localhost:8000/health/live/ \
  || fail "The backend liveness URL did not respond."
curl --silent --fail --output /dev/null http://localhost:5173/ \
  || fail "The frontend URL did not respond."

docker compose ps
trap - ERR
SOURCE_SWAPPED=0
cat <<MESSAGE

CrowdSmarter Phase 13 is running successfully.

Open these addresses in your browser:
  Public site:       http://localhost:5173/
  Application:       http://localhost:5173/app
  Foresight:         open an organisation, then select Foresight
  Scenario planning: open a systems canvas, then select Scenarios

Use your existing email address and password.

Database backup:
  ${DATABASE_BACKUP}

Previous Phase 12 source:
  ${SOURCE_BACKUP}

Do not run: docker compose down -v
MESSAGE
