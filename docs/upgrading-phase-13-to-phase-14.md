# Upgrade Phase 13 to Phase 14 on Linux

Use one terminal. Do not extract the ZIP manually and do not run the upgrade with `sudo`.

## 1. Put these files in Downloads

- `crowdsmarter-phase14.zip`
- `crowdsmarter-phase14.zip.sha256`
- `upgrade-crowdsmarter-to-phase14.sh`

Your current project must remain at:

```text
~/Downloads/crowdsmarter
```

## 2. Run the upgrade

```bash
bash ~/Downloads/upgrade-crowdsmarter-to-phase14.sh
```

If Docker reports permission denied, run these two commands in the same terminal:

```bash
newgrp docker
bash ~/Downloads/upgrade-crowdsmarter-to-phase14.sh
```

## 3. Expected result

The final message should say:

```text
CrowdSmarter Phase 14 is running successfully.
```

Open `http://localhost:5173/app`.

For decision evaluation, open a decision and select **Collective evaluation**. For constrained portfolio prioritisation, open an organisation and select **Prioritisation**.

## Data safety

The script verifies the archive, creates a PostgreSQL backup, preserves the entire Phase 13 source folder, copies the existing `.env`, and never deletes Docker volumes. If a validation step fails after source replacement, it restores the Phase 13 source and the pre-upgrade PostgreSQL backup automatically.

Never run:

```bash
docker compose down -v
```
