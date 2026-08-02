# Upgrade Phase 14 to Phase 15 on Linux

Use one terminal. Do not extract the ZIP manually and do not run the upgrade with `sudo`.

## 1. Put these files in Downloads

- `crowdsmarter-phase15.zip`
- `crowdsmarter-phase15.zip.sha256`
- `upgrade-crowdsmarter-to-phase15.sh`

Your current project must remain at:

```text
~/Downloads/crowdsmarter
```

## 2. Run the upgrade

```bash
bash ~/Downloads/upgrade-crowdsmarter-to-phase15.sh
```

If Docker reports permission denied, run these two commands in the same terminal:

```bash
newgrp docker
bash ~/Downloads/upgrade-crowdsmarter-to-phase15.sh
```

## 3. Expected result

The final message should say:

```text
CrowdSmarter Phase 15 is running successfully.
```

Open `http://localhost:5173/app`, open a decision, and select **Integrated analysis**.

## Data safety

The script verifies the archive, creates a PostgreSQL backup, preserves the entire Phase 14 source folder, carries forward the existing `.env`, and never deletes Docker volumes. If a validation step fails after source replacement, it restores both the Phase 14 source and the pre-upgrade PostgreSQL backup automatically.

Never run:

```bash
docker compose down -v
```
