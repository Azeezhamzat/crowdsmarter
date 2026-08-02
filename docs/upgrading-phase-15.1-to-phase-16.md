# Upgrade Phase 15.1 to Phase 16 on Linux

Download these files directly into `~/Downloads`:

- `crowdsmarter-phase16.zip`
- `crowdsmarter-phase16.zip.sha256`
- `upgrade-crowdsmarter-to-phase16.sh`

Run:

```bash
bash ~/Downloads/upgrade-crowdsmarter-to-phase16.sh
```

Do not extract the archive manually, do not run the script with `sudo`, and never run `docker compose down -v`.

The upgrader verifies the archive, stops the current application without deleting volumes, creates a PostgreSQL backup, preserves the complete Phase 15.1 source, carries forward `.env`, builds containers, applies migrations, provisions the requested local account, runs backend and frontend quality gates, starts the application, and verifies health endpoints.

## Guaranteed local sign-in

For this local development upgrade, `DJANGO_DEBUG` must be enabled. The upgrader provisions or repairs:

```text
owner@example.test
```

A fresh temporary password is written to a file resembling:

```text
~/Downloads/crowdsmarter-local-access-phase16-20260801-230000.txt
```

The file is readable only by its owner. Open it locally, sign in at `http://localhost:5173/login`, change the password under Account settings, and delete the credentials file.

The account's existing password is intentionally replaced so the upgrader can guarantee access. Existing customer records and organisation memberships remain intact. If the account has no active membership, a local organisation and default workspace are created.

## Rollback

If any validation fails after source replacement, the script automatically restores:

- the preserved Phase 15.1 source directory;
- the pre-upgrade PostgreSQL database;
- the previous running services.

The newly generated local credentials file is deleted during rollback because its password would no longer be authoritative.
