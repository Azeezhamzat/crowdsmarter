# Upgrade Phase 9 to Phase 10 on Linux

Use one terminal. Do not extract the archive manually and do not run the script with `sudo`.

Place these files directly in `~/Downloads`:

- `crowdsmarter-phase10.zip`
- `crowdsmarter-phase10.zip.sha256`
- `upgrade-crowdsmarter-to-phase10.sh`

Run exactly:

```bash
bash ~/Downloads/upgrade-crowdsmarter-to-phase10.sh
```

Only when Docker reports permission denied, run:

```bash
newgrp docker
bash ~/Downloads/upgrade-crowdsmarter-to-phase10.sh
```

The script verifies the archive, creates a PostgreSQL backup, preserves the complete Phase 9 source folder and `.env`, builds Phase 10, applies migrations, runs focused tests and the frontend production build, starts the application, and verifies both services.

A successful ending says:

```text
CrowdSmarter Phase 10 is running successfully.
```

Open:

```text
http://localhost:5173/app
```

Account settings are at `/account`. Organisation managers can open **Data export** from an organisation. Every decision workspace has **Download dossier**.

Never run:

```bash
docker compose down -v
```

The `-v` option deletes the PostgreSQL volume.
