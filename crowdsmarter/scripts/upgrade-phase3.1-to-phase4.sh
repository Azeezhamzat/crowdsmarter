#!/usr/bin/env bash
set -Eeuo pipefail

DOWNLOADS_DIR="${HOME}/Downloads"
CURRENT_DIR="${DOWNLOADS_DIR}/crowdsmarter"
ARCHIVE="${DOWNLOADS_DIR}/crowdsmarter-phase4.zip"
CHECKSUM="${DOWNLOADS_DIR}/crowdsmarter-phase4.zip.sha256"
STAMP="$(date +%Y%m%d-%H%M%S)"
SOURCE_BACKUP="${DOWNLOADS_DIR}/crowdsmarter-phase3.1-backup-${STAMP}"
DATABASE_BACKUP="${HOME}/crowdsmarter-before-phase4-${STAMP}.sql"
STAGE="preflight"

say() {
  printf '\n%s\n' "$1"
}

fail() {
  printf '\nUpgrade stopped: %s\n' "$1" >&2
  exit 1
}

on_error() {
  local line="$1"
  printf '\nUpgrade failed during %s (script line %s).\n' "${STAGE}" "${line}" >&2
  if [[ -d "${CURRENT_DIR}" && -f "${CURRENT_DIR}/docker-compose.yml" ]]; then
    (
      cd "${CURRENT_DIR}"
      docker compose ps >&2 || true
      docker compose logs --tail=160 backend >&2 || true
    )
  fi
  [[ -f "${DATABASE_BACKUP}" ]] && printf 'Database backup: %s\n' "${DATABASE_BACKUP}" >&2
  [[ -d "${SOURCE_BACKUP}" ]] && printf 'Previous source: %s\n' "${SOURCE_BACKUP}" >&2
  printf 'Do not run: docker compose down -v\n' >&2
}
trap 'on_error "$LINENO"' ERR

command -v docker >/dev/null 2>&1 || fail "Docker is not installed or is not on PATH."
docker compose version >/dev/null 2>&1 || fail "Docker Compose is unavailable."
command -v unzip >/dev/null 2>&1 || fail "unzip is not installed. Run: sudo apt install unzip"
command -v curl >/dev/null 2>&1 || fail "curl is not installed. Run: sudo apt install curl"
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum is unavailable."

if ! docker info >/dev/null 2>&1; then
  fail "Docker is not available to this terminal. Run: newgrp docker, then run this script again."
fi

[[ -d "${CURRENT_DIR}" ]] || fail "${CURRENT_DIR} was not found."
[[ -f "${CURRENT_DIR}/docker-compose.yml" ]] || fail "The current CrowdSmarter folder is incomplete."
[[ -f "${CURRENT_DIR}/.env" ]] || fail "${CURRENT_DIR}/.env was not found."
[[ -f "${ARCHIVE}" ]] || fail "Download crowdsmarter-phase4.zip into ${DOWNLOADS_DIR} first."
[[ -f "${CHECKSUM}" ]] || fail "Download crowdsmarter-phase4.zip.sha256 into ${DOWNLOADS_DIR} first."

STAGE="archive verification"
say "1/9 Verifying the Phase 4 archive"
(
  cd "${DOWNLOADS_DIR}"
  sha256sum -c "$(basename "${CHECKSUM}")"
)
unzip -tq "${ARCHIVE}" >/dev/null

STAGE="stopping Phase 3.1"
say "2/9 Stopping the current application safely"
cd "${CURRENT_DIR}"
docker compose down

STAGE="database backup"
say "3/9 Creating a PostgreSQL backup"
docker compose up -d db
for _ in {1..30}; do
  if docker compose exec -T db sh -c \
    'pg_isready --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' \
    >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
if ! docker compose exec -T db sh -c \
  'pg_isready --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' \
  >/dev/null 2>&1; then
  fail "PostgreSQL did not become ready. Your source files have not been changed."
fi
docker compose exec -T db sh -c \
  'pg_dump --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' \
  > "${DATABASE_BACKUP}"
docker compose down
printf 'Database backup: %s\n' "${DATABASE_BACKUP}"

STAGE="preserving Phase 3.1 source"
say "4/9 Preserving the Phase 3.1 source and configuration"
cd "${DOWNLOADS_DIR}"
mv "${CURRENT_DIR}" "${SOURCE_BACKUP}"
printf 'Source backup: %s\n' "${SOURCE_BACKUP}"

STAGE="extracting Phase 4"
say "5/9 Extracting Phase 4"
unzip -q "${ARCHIVE}" -d "${DOWNLOADS_DIR}"
[[ -d "${CURRENT_DIR}" ]] || fail "The archive did not create ${CURRENT_DIR}. Your previous source remains at ${SOURCE_BACKUP}."
cp "${SOURCE_BACKUP}/.env" "${CURRENT_DIR}/.env"

allowed_hosts="$(grep '^DJANGO_ALLOWED_HOSTS=' "${CURRENT_DIR}/.env" | tail -n1 | cut -d= -f2- || true)"
if [[ -z "${allowed_hosts}" ]]; then
  printf '\nDJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,backend\n' >> "${CURRENT_DIR}/.env"
elif [[ ",${allowed_hosts}," != *,backend,* ]]; then
  sed -i "s/^DJANGO_ALLOWED_HOSTS=.*/DJANGO_ALLOWED_HOSTS=${allowed_hosts},backend/" "${CURRENT_DIR}/.env"
fi

STAGE="building and migrating"
say "6/9 Building Phase 4 and applying additive migrations"
cd "${CURRENT_DIR}"
docker compose up -d --build

STAGE="Django checks"
say "7/9 Running Django and migration checks"
docker compose exec backend python manage.py check
docker compose exec backend python manage.py makemigrations --check --dry-run
docker compose exec backend python manage.py showmigrations positions decisions

STAGE="focused regression checks"
say "8/9 Running focused governance checks"
docker compose exec backend pytest \
  apps/positions \
  apps/decisions/tests/test_finalisation.py \
  apps/decisions/tests/test_finalisation_api.py \
  apps/decisions/tests/test_services.py::test_generic_transition_cannot_bypass_finalisation \
  apps/audit/tests/test_api.py
docker compose exec frontend npm run typecheck
docker compose exec frontend npm test -- --run \
  src/features/governance/DecisionGovernancePage.test.tsx \
  src/features/decisions/DecisionLifecycle.test.tsx
docker compose exec frontend npm run build

STAGE="application health check"
say "9/9 Checking application health"
for _ in {1..30}; do
  if curl --silent --fail --output /dev/null http://localhost:8000/health/live/; then
    docker compose ps
    trap - ERR
    cat <<EOF2

Phase 4 is running.

Open: http://localhost:5173
Use your existing email address and password.

Database backup:
  ${DATABASE_BACKUP}

Previous source backup:
  ${SOURCE_BACKUP}

Open a decision and choose "Positions and final decision" to use the new governance workflow.

Do not run: docker compose down -v
EOF2
    exit 0
  fi
  sleep 1
done

printf '\nThe containers started, but the backend health check did not become ready.\n' >&2
docker compose ps >&2
docker compose logs --tail=180 backend >&2
exit 1
