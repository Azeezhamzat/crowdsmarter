# PostgreSQL backup and restore runbook

## Objective

A backup is accepted only after it can be restored into an isolated database and key integrity counts match the source. The supplied drill never restores over the live `crowdsmarter` database.

## Run the local drill

Start the ordinary stack, then run:

```bash
./scripts/backup-restore-drill.sh
```

The script creates a custom-format `pg_dump`, calculates its SHA-256, creates an explicitly named temporary database, restores the dump with `--exit-on-error`, and compares migration, user, organisation, and audit-event counts. A trap drops only the validated temporary database name and removes the temporary dump.

A successful run prints `BACKUP_RESTORE_DRILL=PASS`. Record the UTC date, operator, source environment, dump checksum and size, compared counts, elapsed time, and any corrective action in the operational evidence log.

## Local evidence

On 2026-08-30 the script successfully restored the local PostgreSQL database
into `crowdsmarter_restore_drill_20260830213812` and printed:

```text
BACKUP_RESTORE_DRILL=PASS
dump_bytes=611471
dump_sha256=e824091444084cd85b24a8ac5f33f90c1882aca8dfbe8e41e8b64c9f2279ddb0
counts_migrations_users_organisations_audit=83,1,1,6
```

Source and restored counts matched. The isolated database and temporary dump
were removed by the script. An initial run also revealed and corrected a macOS
`/var/folders` cleanup-path allowlist issue before this final evidence run.

## Production schedule

- Encrypted automated backup: daily.
- Restore drill: monthly before customer launch, then at least quarterly.
- Additional drill: after a major PostgreSQL upgrade, storage change, encryption-key change, or recovery failure.
- Off-site copy: required; it must not share the database host's failure domain.
- Backup retention: proposed 35 daily copies plus 12 monthly copies, subject to owner and legal approval.

Production drills must restore into an isolated account/network/database and use a read-only validation process. Never download an unencrypted customer backup to a personal workstation. Test application login and a representative tenant export in addition to count comparison before declaring a production recovery successful.

## Failure handling

If the script exits before `PASS`, preserve the command output, do not label the backup recoverable, open an incident, repair the backup process, and repeat the full drill. A successful `pg_dump` command alone is not recovery evidence.
