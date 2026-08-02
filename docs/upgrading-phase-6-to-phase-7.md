# Upgrade Phase 6 to Phase 7 on Linux

Use one terminal. Do not extract the ZIP manually and do not use `sudo` to run the script.

Place these files directly in `~/Downloads`:

- `crowdsmarter-phase7.zip`
- `crowdsmarter-phase7.zip.sha256`
- `upgrade-crowdsmarter-to-phase7.sh`

Run exactly:

```bash
bash ~/Downloads/upgrade-crowdsmarter-to-phase7.sh
```

If Docker reports permission denied, run exactly:

```bash
newgrp docker
bash ~/Downloads/upgrade-crowdsmarter-to-phase7.sh
```

The script verifies the archive, stops Phase 6 without deleting volumes, backs up PostgreSQL, preserves the Phase 6 source and `.env`, applies migrations, runs focused checks, starts the application, and verifies both services.

Never run:

```bash
docker compose down -v
```

After success, open:

- `http://localhost:5173/app` for My work;
- an organisation's **Decision portfolio** link;
- a decision's **Discussion and activity** link.
