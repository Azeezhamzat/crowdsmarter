#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_dir"

drill_stamp="$(date -u +%Y%m%d%H%M%S)"
drill_database="crowdsmarter_restore_drill_${drill_stamp}"
drill_directory="$(mktemp -d)"
dump_path="${drill_directory}/crowdsmarter.dump"
database_created=false

case "$drill_database" in
  crowdsmarter_restore_drill_[0-9]*) ;;
  *) printf 'Refusing unsafe drill database name: %s\n' "$drill_database" >&2; exit 1 ;;
esac

cleanup() {
  if [ "$database_created" = true ]; then
    docker compose exec -T db sh -c 'dropdb --force --if-exists --username="$POSTGRES_USER" "$1"' sh "$drill_database" >/dev/null
  fi
  case "$drill_directory" in
    /tmp/*|/private/tmp/*|/var/folders/*|/private/var/folders/*) rm -rf "$drill_directory" ;;
    *) printf 'Temporary drill directory was not removed: %s\n' "$drill_directory" >&2 ;;
  esac
}
trap cleanup EXIT INT TERM

docker compose ps db >/dev/null
docker compose exec -T db sh -c 'pg_dump --format=custom --no-owner --no-privileges --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' >"$dump_path"
test -s "$dump_path"

dump_sha256="$(shasum -a 256 "$dump_path" | awk '{print $1}')"
dump_bytes="$(wc -c <"$dump_path" | tr -d ' ')"

docker compose exec -T db sh -c 'createdb --username="$POSTGRES_USER" "$1"' sh "$drill_database"
database_created=true
docker compose exec -T db sh -c 'pg_restore --exit-on-error --no-owner --no-privileges --username="$POSTGRES_USER" --dbname="$1"' sh "$drill_database" <"$dump_path"

count_sql='SELECT (SELECT count(*) FROM django_migrations), (SELECT count(*) FROM accounts_user), (SELECT count(*) FROM organisations_organisation), (SELECT count(*) FROM audit_auditevent);'
source_counts="$(docker compose exec -T db sh -c 'psql --no-psqlrc --tuples-only --no-align --field-separator=, --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" --command="$1"' sh "$count_sql" | tr -d '[:space:]')"
restored_counts="$(docker compose exec -T db sh -c 'psql --no-psqlrc --tuples-only --no-align --field-separator=, --username="$POSTGRES_USER" --dbname="$1" --command="$2"' sh "$drill_database" "$count_sql" | tr -d '[:space:]')"

if [ "$source_counts" != "$restored_counts" ]; then
  printf 'Backup restoration count mismatch: source=%s restored=%s\n' "$source_counts" "$restored_counts" >&2
  exit 1
fi

printf 'BACKUP_RESTORE_DRILL=PASS\n'
printf 'isolated_database=%s\n' "$drill_database"
printf 'dump_bytes=%s\n' "$dump_bytes"
printf 'dump_sha256=%s\n' "$dump_sha256"
printf 'counts_migrations_users_organisations_audit=%s\n' "$restored_counts"
printf 'The isolated database and temporary dump will now be removed.\n'
