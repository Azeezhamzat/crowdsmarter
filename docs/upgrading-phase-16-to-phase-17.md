# Upgrade Phase 16 to Phase 17 on Linux

Place these files directly in `~/Downloads`:

- `crowdsmarter-phase17.zip`
- `crowdsmarter-phase17.zip.sha256`
- `upgrade-crowdsmarter-to-phase17.sh`

For a local development installation, confirm that `.env` contains `DJANGO_DEBUG=true`. Then run:

```bash
bash ~/Downloads/upgrade-crowdsmarter-to-phase17.sh
```

The upgrader verifies the archive, backs up PostgreSQL, preserves the Phase 16 source, applies the organisation, methodology, and decision migrations, provisions secure local access for `hello@crowdsmarter.com`, runs backend and frontend quality gates, starts the application, and checks service routes.

The generated credentials file resembles:

```text
~/Downloads/crowdsmarter-local-access-phase17-20260801-234500.txt
```

Read it locally, sign in, change the temporary password through Account settings, and delete the file. The supplied weak password `Admin1` is not used.

If any post-installation validation fails, the script restores the preserved Phase 16 source and the pre-upgrade PostgreSQL backup. Docker volumes are never deleted.

Never run:

```bash
docker compose down -v
```
