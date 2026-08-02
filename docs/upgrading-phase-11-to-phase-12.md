# Upgrade Phase 11 to Phase 12 on Linux

Use one terminal. Do not extract the ZIP manually and do not run the upgrade with `sudo`.

## 1. Put these files in Downloads

- `crowdsmarter-phase12.zip`
- `crowdsmarter-phase12.zip.sha256`
- `upgrade-crowdsmarter-to-phase12.sh`

Your current project must remain at:

```text
~/Downloads/crowdsmarter
```

## 2. Run the upgrade

```bash
bash ~/Downloads/upgrade-crowdsmarter-to-phase12.sh
```

If Docker reports permission denied, run these two commands in the same terminal:

```bash
newgrp docker
bash ~/Downloads/upgrade-crowdsmarter-to-phase12.sh
```

## 3. Expected result

The final message should say:

```text
CrowdSmarter Phase 12 is running successfully.
```

Open:

```text
http://localhost:5173/app
```

Open an organisation, select **Foresight**, then **Systems canvases**.

## Data safety

The script creates a PostgreSQL backup, preserves the entire Phase 11 source folder, copies the existing `.env`, and never deletes Docker volumes. If a validation step fails after source replacement, the Phase 11 source and the pre-upgrade PostgreSQL backup are restored automatically.

Never run:

```bash
docker compose down -v
```
