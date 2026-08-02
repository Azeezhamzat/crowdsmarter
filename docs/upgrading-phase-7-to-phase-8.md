# Upgrade Phase 7 to Phase 8 on Linux

Use one terminal only.

## Files to download

Save these files directly in `~/Downloads`:

- `crowdsmarter-phase8.zip`
- `crowdsmarter-phase8.zip.sha256`
- `upgrade-crowdsmarter-to-phase8.sh`

Do not extract the ZIP manually.

## Run the upgrade

```bash
bash ~/Downloads/upgrade-crowdsmarter-to-phase8.sh
```

If the terminal reports Docker permission denied, run these two commands in the same terminal:

```bash
newgrp docker
bash ~/Downloads/upgrade-crowdsmarter-to-phase8.sh
```

Do not run the script with `sudo`.

## Successful result

The final line should state:

```text
CrowdSmarter Phase 8 is running successfully.
```

Open:

```text
http://localhost:5173/app
```

## New workflow

1. Open an organisation and workspace.
2. Select **Start a guided decision**.
3. Choose the closest template.
4. Complete framing, boundaries, authority, and timing.
5. Review the summary and create the draft.
6. Open the draft to see its next required action and decision-health overview.

## Important

Never run:

```bash
docker compose down -v
```

The `-v` option deletes the PostgreSQL volume.
