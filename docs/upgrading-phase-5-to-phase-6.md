# Upgrade Phase 5 to Phase 6 on Linux

Use the supplied one-terminal script. Do not extract the archive manually.

Place these three files directly in your Linux `Downloads` folder:

- `crowdsmarter-phase6.zip`
- `crowdsmarter-phase6.zip.sha256`
- `upgrade-crowdsmarter-to-phase6.sh`

Open one terminal and run exactly:

```bash
bash ~/Downloads/upgrade-crowdsmarter-to-phase6.sh
```

If the terminal reports Docker permission denied, run exactly:

```bash
newgrp docker
bash ~/Downloads/upgrade-crowdsmarter-to-phase6.sh
```

Do not run the script with `sudo`. Never run `docker compose down -v`; `-v` deletes the PostgreSQL volume.

The script checks the required files and Docker access, verifies the SHA-256 checksum, stops the current containers without deleting volumes, starts PostgreSQL and waits for health, creates a database dump, preserves the Phase 5 source directory and `.env`, installs Phase 6, builds the containers, applies migrations, runs focused checks, starts the application, and verifies the backend and frontend.

After a successful upgrade, open:

- public site: `http://localhost:5173/`
- application: `http://localhost:5173/app`
- notifications: `http://localhost:5173/notifications`

Your existing account, password, organisations, invitations, decisions, reasoning records, finalisations, outcomes, lessons, audit history, PostgreSQL volume, and `.env` are preserved.

The default advisory provider is local and free. No API key is required. To create due-review notifications without the optional scheduler, run from `~/Downloads/crowdsmarter`:

```bash
docker compose exec backend python manage.py send_due_review_notifications
```

To run the optional worker and daily scheduler:

```bash
cd ~/Downloads/crowdsmarter
docker compose --profile workers up -d worker scheduler
```
