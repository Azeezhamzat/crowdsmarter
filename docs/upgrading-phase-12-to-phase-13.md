# Upgrade Phase 12 to Phase 13 on Linux

Use one terminal. Do not extract the ZIP manually and do not run the upgrade with `sudo`.

## 1. Put these files in Downloads

- `crowdsmarter-phase13.zip`
- `crowdsmarter-phase13.zip.sha256`
- `upgrade-crowdsmarter-to-phase13.sh`

Your current project must remain at:

```text
~/Downloads/crowdsmarter
```

## 2. Run the upgrade

```bash
bash ~/Downloads/upgrade-crowdsmarter-to-phase13.sh
```

If Docker reports permission denied, run these two commands in the same terminal:

```bash
newgrp docker
bash ~/Downloads/upgrade-crowdsmarter-to-phase13.sh
```

## 3. Expected result

The final message should say:

```text
CrowdSmarter Phase 13 is running successfully.
```

Open:

```text
http://localhost:5173/app
```

Open an organisation, select **Foresight**, open a systems canvas, then select **Scenarios**.

## Data safety

The script verifies the archive, creates a PostgreSQL backup, preserves the entire Phase 12 source folder, copies the existing `.env`, and never deletes Docker volumes. If a validation step fails after source replacement, it restores the Phase 12 source and the pre-upgrade PostgreSQL backup automatically.

Never run:

```bash
docker compose down -v
```
