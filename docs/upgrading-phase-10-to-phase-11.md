# Upgrade Phase 10 to Phase 11 on Linux

Use one terminal. Do not extract the archive manually and do not run the script with `sudo`.

Place these files directly in `~/Downloads`:

- `crowdsmarter-phase11.zip`
- `crowdsmarter-phase11.zip.sha256`
- `upgrade-crowdsmarter-to-phase11.sh`

Run exactly:

```bash
bash ~/Downloads/upgrade-crowdsmarter-to-phase11.sh
```

Only when Docker reports permission denied, run:

```bash
newgrp docker
bash ~/Downloads/upgrade-crowdsmarter-to-phase11.sh
```

The script verifies the archive, safely stops Phase 10, creates a PostgreSQL backup, preserves the complete Phase 10 source folder and `.env`, builds Phase 11, applies migrations, checks migration drift, runs focused backend and frontend tests, starts the application, and verifies both services.

A successful ending says:

```text
CrowdSmarter Phase 11 is running successfully.
```

Open:

```text
http://localhost:5173/app
```

Open an organisation and select **Foresight and signals**. Local storage works without further configuration. Public feeds can be tested manually in local development. Production deployments must configure `FORESIGHT_FEED_ALLOWED_DOMAINS` before feed creation or synchronisation is enabled.

Never run:

```bash
docker compose down -v
```

The `-v` option deletes the PostgreSQL and private-media volumes.
