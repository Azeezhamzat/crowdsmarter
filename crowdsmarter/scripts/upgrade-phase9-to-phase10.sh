#!/usr/bin/env bash
set -Eeuo pipefail

DOWNLOADS_DIR="${HOME}/Downloads"
CURRENT_DIR="${DOWNLOADS_DIR}/crowdsmarter"
ARCHIVE="${DOWNLOADS_DIR}/crowdsmarter-phase10.zip"
CHECKSUM="${DOWNLOADS_DIR}/crowdsmarter-phase10.zip.sha256"
BACKUP_DIR="${DOWNLOADS_DIR}/crowdsmarter-backups"
STAMP="$(date +%Y%m%d-%H%M%S)"
SOURCE_BACKUP="${DOWNLOADS_DIR}/crowdsmarter-phase9-source-${STAMP}"
FAILED_SOURCE="${DOWNLOADS_DIR}/crowdsmarter-phase10-failed-${STAMP}"
DATABASE_BACKUP="${BACKUP_DIR}/crowdsmarter-before-phase10-${STAMP}.sql"
STAGE="preflight"
SOURCE_SWAPPED=0

say() {
  printf '\n%s\n' "$1"
}

fail() {
  printf '\nUpgrade stopped: %s\n' "$1" >&2
  return 1
}

show_docker_diagnostics() {
  if [[ -d "${CURRENT_DIR}" && -f "${CURRENT_DIR}/docker-compose.yml" ]]; then
    (
      cd "${CURRENT_DIR}"
      docker compose ps -a >&2 || true
      docker compose logs --tail=180 backend >&2 || true
    )
  fi
}

rollback_source() {
  [[ "${SOURCE_SWAPPED}" -eq 1 ]] || return 0
  [[ -d "${SOURCE_BACKUP}" ]] || return 0

  printf '\nRestoring the previous Phase 9 source automatically.\n' >&2
  if [[ -d "${CURRENT_DIR}" ]]; then
    (
      cd "${CURRENT_DIR}"
      docker compose down --remove-orphans >&2 || true
    )
    mv "${CURRENT_DIR}" "${FAILED_SOURCE}" || true
  fi
  mv "${SOURCE_BACKUP}" "${CURRENT_DIR}" || true
  if [[ -f "${CURRENT_DIR}/docker-compose.yml" ]]; then
    (
      cd "${CURRENT_DIR}"
      docker compose up -d >&2 || true
    )
  fi
}

on_error() {
  local line="$1"
  set +e
  printf '\nUpgrade failed during: %s (script line %s).\n' "${STAGE}" "${line}" >&2
  show_docker_diagnostics
  rollback_source
  [[ -f "${DATABASE_BACKUP}" ]] && printf 'Database backup: %s\n' "${DATABASE_BACKUP}" >&2
  [[ -d "${FAILED_SOURCE}" ]] && printf 'Failed Phase 10 source: %s\n' "${FAILED_SOURCE}" >&2
  printf 'Your PostgreSQL volume was not deleted.\n' >&2
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
  bash ~/Downloads/upgrade-crowdsmarter-to-phase10.sh
MESSAGE
  exit 1
fi

[[ -d "${CURRENT_DIR}" ]] || fail "Current project not found at ${CURRENT_DIR}."
[[ -f "${CURRENT_DIR}/docker-compose.yml" ]] || fail "The current project folder is incomplete."
[[ -f "${CURRENT_DIR}/.env" ]] || fail "The current .env file was not found."
[[ -f "${ARCHIVE}" ]] || fail "Download crowdsmarter-phase10.zip directly into ${DOWNLOADS_DIR}."
[[ -f "${CHECKSUM}" ]] || fail "Download crowdsmarter-phase10.zip.sha256 directly into ${DOWNLOADS_DIR}."
mkdir -p "${BACKUP_DIR}"

STAGE="archive verification"
say "1/10 Verifying the Phase 10 download"
(
  cd "${DOWNLOADS_DIR}"
  sha256sum -c "$(basename "${CHECKSUM}")"
)
unzip -tq "${ARCHIVE}" >/dev/null

STAGE="stopping Phase 9"
say "2/10 Stopping Phase 9 without deleting data"
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
say "3/10 Starting PostgreSQL and creating a database backup"
docker compose up -d db
for _ in {1..60}; do
  if docker compose exec -T db sh -c \
    'pg_isready --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' \
    >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
docker compose exec -T db sh -c \
  'pg_isready --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' \
  >/dev/null 2>&1 || fail "PostgreSQL did not become ready."
docker compose exec -T db sh -c \
  'pg_dump --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' \
  > "${DATABASE_BACKUP}"
[[ -s "${DATABASE_BACKUP}" ]] || fail "The PostgreSQL backup file is empty."
docker compose down --remove-orphans
printf 'Database backup created: %s\n' "${DATABASE_BACKUP}"

STAGE="preserving Phase 9 source"
say "4/10 Preserving the current source and configuration"
cd "${DOWNLOADS_DIR}"
mv "${CURRENT_DIR}" "${SOURCE_BACKUP}"
SOURCE_SWAPPED=1
printf 'Previous source preserved: %s\n' "${SOURCE_BACKUP}"

STAGE="extracting Phase 10"
say "5/10 Installing the Phase 10 source"
unzip -q "${ARCHIVE}" -d "${DOWNLOADS_DIR}"
[[ -d "${CURRENT_DIR}" ]] || fail "The archive did not create ${CURRENT_DIR}."
[[ -f "${CURRENT_DIR}/docker-compose.yml" ]] || fail "The extracted project is incomplete."
cp "${SOURCE_BACKUP}/.env" "${CURRENT_DIR}/.env"

ensure_env_value() {
  local key="$1"
  local value="$2"
  if grep -q "^${key}=" "${CURRENT_DIR}/.env"; then
    return 0
  fi
  printf '\n%s=%s\n' "${key}" "${value}" >> "${CURRENT_DIR}/.env"
}

allowed_hosts="$(grep '^DJANGO_ALLOWED_HOSTS=' "${CURRENT_DIR}/.env" | tail -n1 | cut -d= -f2- || true)"
if [[ -z "${allowed_hosts}" ]]; then
  printf '\nDJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,backend\n' >> "${CURRENT_DIR}/.env"
elif [[ ",${allowed_hosts}," != *,backend,* ]]; then
  sed -i \
    "s/^DJANGO_ALLOWED_HOSTS=.*/DJANGO_ALLOWED_HOSTS=${allowed_hosts},backend/" \
    "${CURRENT_DIR}/.env"
fi
ensure_env_value \
  "AI_PROVIDER_BACKEND" \
  "apps.ai_assistance.providers.rules.RuleBasedAIProvider"
ensure_env_value "API_AI_REVIEW_THROTTLE_RATE" "20/hour"
ensure_env_value "PASSWORD_RESET_TIMEOUT" "3600"
ensure_env_value "API_PASSWORD_RESET_REQUEST_THROTTLE_RATE" "5/hour"
ensure_env_value "API_PASSWORD_RESET_CONFIRM_THROTTLE_RATE" "20/hour"
ensure_env_value "API_ACCOUNT_SECURITY_THROTTLE_RATE" "20/hour"
ensure_env_value "API_DATA_EXPORT_THROTTLE_RATE" "20/hour"

STAGE="building containers"
say "6/10 Building the Phase 10 backend and frontend"
cd "${CURRENT_DIR}"
docker compose build backend frontend

STAGE="database connectivity and migrations"
say "7/10 Starting PostgreSQL, checking container networking, and applying migrations"
docker compose up -d db redis
for _ in {1..60}; do
  health="$(docker inspect -f '{{.State.Health.Status}}' "$(docker compose ps -q db)" 2>/dev/null || true)"
  [[ "${health}" == "healthy" ]] && break
  sleep 1
done
[[ "$(docker inspect -f '{{.State.Health.Status}}' "$(docker compose ps -q db)")" == "healthy" ]] \
  || fail "PostgreSQL did not report healthy."
docker compose run --rm --no-deps backend \
  python -c "import socket; print('Database address:', socket.gethostbyname('db'))"
docker compose run --rm backend python manage.py migrate

STAGE="backend quality checks"
say "8/10 Running Django, account-security, and export checks"
docker compose run --rm backend python manage.py check
docker compose run --rm backend python manage.py makemigrations --check --dry-run
docker compose run --rm backend pytest \
  apps/accounts/tests/test_api.py \
  apps/accounts/tests/test_models.py \
  apps/exports/tests/test_api.py \
  apps/organisations/tests/test_api.py \
  apps/decisions/tests/test_api.py

STAGE="frontend quality checks"
say "9/10 Running frontend type, account, navigation, and production-build checks"
docker compose run --rm --no-deps frontend npm run typecheck
docker compose run --rm --no-deps frontend npm test -- --run \
  src/components/AppShell.test.tsx \
  src/features/auth/LoginPage.test.tsx \
  src/features/auth/ForgotPasswordPage.test.tsx \
  src/features/auth/ResetPasswordPage.test.tsx \
  src/features/auth/AccountSettingsPage.test.tsx \
  src/features/decisions/DecisionLifecycle.test.tsx \
  src/features/landing/LandingPage.test.tsx
docker compose run --rm --no-deps frontend npm run build

STAGE="application startup and health checks"
say "10/10 Starting Phase 10 and checking both application services"
docker compose up -d backend frontend
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

CrowdSmarter Phase 10 is running successfully.

Open these addresses in your browser:
  Public site:    http://localhost:5173/
  Application:    http://localhost:5173/app
  Quick navigation: press Ctrl+K or Command+K inside the application
  Account:        http://localhost:5173/account
  Notifications:  http://localhost:5173/notifications
  My work:        http://localhost:5173/app

Organisation owners and administrators can open Data export from an organisation.
Every decision workspace includes Download dossier.

Use your existing email address and password.

Database backup:
  ${DATABASE_BACKUP}

Previous Phase 9 source:
  ${SOURCE_BACKUP}

Do not run: docker compose down -v
MESSAGE
