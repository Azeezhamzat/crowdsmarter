# Upgrade Phase 3.1 to Phase 4 on Linux

This guide preserves the existing PostgreSQL Docker volume, account, organisations, invitations, decisions, and structured reasoning records.

## Files required

Place these files in `~/Downloads`:

- `crowdsmarter-phase4.zip`
- `crowdsmarter-phase4.zip.sha256`
- `upgrade-crowdsmarter-to-phase4.sh`

Do not extract the archive manually.

## Run the upgrade

Use one terminal:

```bash
bash ~/Downloads/upgrade-crowdsmarter-to-phase4.sh
```

If Docker reports a socket permission error:

```bash
newgrp docker
bash ~/Downloads/upgrade-crowdsmarter-to-phase4.sh
```

The script verifies the archive checksum, stops the current application, creates a PostgreSQL backup, preserves the Phase 3.1 source folder, extracts Phase 4, carries forward `.env`, builds the containers, applies migrations, runs focused backend and frontend checks, and verifies the health endpoint.

## After the upgrade

Open:

```text
http://localhost:5173
```

Use the existing email address and password. Open a decision and choose **Positions and final decision**.

## Normal stop and start

```bash
cd ~/Downloads/crowdsmarter
docker compose down
```

```bash
cd ~/Downloads/crowdsmarter
docker compose up -d
```

Never run:

```bash
docker compose down -v
```

The `-v` option deletes the PostgreSQL volume.
