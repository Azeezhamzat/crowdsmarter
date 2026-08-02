# Upgrade Phase 8 to Phase 9 on Linux

Use one terminal. Do not extract the Phase 9 ZIP manually.

## Files required in Downloads

- `crowdsmarter-phase9.zip`
- `crowdsmarter-phase9.zip.sha256`
- `upgrade-crowdsmarter-to-phase9.sh`

## Run the upgrade

```bash
bash ~/Downloads/upgrade-crowdsmarter-to-phase9.sh
```

If Docker reports permission denied, run these two commands in the same terminal:

```bash
newgrp docker
bash ~/Downloads/upgrade-crowdsmarter-to-phase9.sh
```

Do not run the script with `sudo`.

## What the script does

1. verifies the archive checksum;
2. stops Phase 8 without deleting data;
3. confirms ports 8000 and 5173 are available;
4. creates a PostgreSQL backup;
5. preserves the Phase 8 source folder;
6. preserves `.env`;
7. builds Phase 9;
8. applies migrations and checks migration drift;
9. runs backend and frontend checks;
10. starts and verifies the application.

## Successful result

The script ends with:

```text
CrowdSmarter Phase 9 is running successfully.
```

Open:

- public site: `http://localhost:5173/`
- application: `http://localhost:5173/app`

## Never run

```bash
docker compose down -v
```

The `-v` option deletes the local PostgreSQL volume.
