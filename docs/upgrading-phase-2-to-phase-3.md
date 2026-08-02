# Upgrade from Phase 2 to Phase 3 on Linux

This guide assumes the current Phase 2 project is at `~/Downloads/crowdsmarter` and has already been stopped with `docker compose down`.

Phase 3 contains all Phase 1 and Phase 2 functionality. Do not merge source files manually.

## 1. Download the Phase 3 archive

Save `crowdsmarter-phase3.zip` in your `~/Downloads` directory.

## 2. Back up the current database

Start only PostgreSQL, create a SQL backup, and stop it again:

```bash
cd ~/Downloads/crowdsmarter
docker compose up -d db
docker compose exec -T db sh -c 'pg_dump --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' > ~/crowdsmarter-before-phase3.sql
docker compose down
```

The backup is stored at `~/crowdsmarter-before-phase3.sql`.

Do not run `docker compose down -v`; `-v` deletes the database volume.

## 3. Preserve the Phase 2 source and environment

```bash
cd ~/Downloads
mv crowdsmarter crowdsmarter-phase2-backup
unzip crowdsmarter-phase3.zip
cp crowdsmarter-phase2-backup/.env crowdsmarter/.env
```

Keeping the new folder name as `crowdsmarter` allows Docker Compose to reuse the existing named database volume.

## 4. Start Phase 3

```bash
cd ~/Downloads/crowdsmarter
docker compose up -d --build
```

The backend runs the new Django migrations automatically before starting.

Check the services:

```bash
docker compose ps
```

The `backend`, `frontend`, `db`, and `redis` services should be running. Open:

```text
http://localhost:5173
```

Use the same account and password you used in Phase 2.

## 5. Verify the upgrade

```bash
docker compose exec backend python manage.py check
docker compose exec backend python manage.py showmigrations decision_options evidence assumptions risks
```

Each new app should show `[X] 0001_initial`. Also confirm the account migration was applied:

```bash
docker compose exec backend python manage.py showmigrations accounts
```

Both `0001_initial` and `0002_align_inherited_auth_field_metadata` should show `[X]`.

Check migration drift without creating files:

```bash
docker compose exec backend python manage.py makemigrations --check --dry-run
```

The account migration in this release only aligns inherited Django field metadata and does not change account values. The dry-run should report `No changes detected`. If it reports another change, do not run `makemigrations`; preserve the output for review.

## 6. Stop the application later

```bash
cd ~/Downloads/crowdsmarter
docker compose down
```

This preserves the database, account, organisations, decisions, and Phase 3 records.

## Restore Phase 2 if necessary

Stop Phase 3 without deleting volumes:

```bash
cd ~/Downloads/crowdsmarter
docker compose down
cd ~/Downloads
mv crowdsmarter crowdsmarter-phase3-source
mv crowdsmarter-phase2-backup crowdsmarter
cd crowdsmarter
docker compose up -d --build
```

The SQL backup provides an additional recovery point. Restoring it is normally unnecessary because the Phase 3 migrations only add new tables and advance one lifecycle capability.
