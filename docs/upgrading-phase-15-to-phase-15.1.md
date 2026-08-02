# Upgrade Phase 15 to Phase 15.1 on Linux

Place these files directly in `~/Downloads`:

- `crowdsmarter-phase15.1.zip`
- `crowdsmarter-phase15.1.zip.sha256`
- `upgrade-crowdsmarter-to-phase15.1.sh`

Run:

```bash
bash ~/Downloads/upgrade-crowdsmarter-to-phase15.1.sh
```

Do not extract the archive manually and do not run the script with `sudo`.

The upgrader verifies the archive, creates a PostgreSQL backup, preserves the Phase 15 source, migrates `demo_requests`, runs authentication, demo-request, landing-page, account, and regression checks, builds both applications, and verifies health endpoints.

When the database contains no active account and `DJANGO_DEBUG=true`, the upgrader creates a local owner and writes the generated credential to a mode-`600` file in `~/Downloads`. Existing active accounts are not modified.

To repair an existing local password later, run:

```bash
bash ~/Downloads/crowdsmarter/scripts/reset-local-password.sh
```

A successful upgrade reports:

```text
CrowdSmarter Phase 15.1 is running successfully.
```

Never run `docker compose down -v`.
