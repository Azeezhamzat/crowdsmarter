# Upgrade Phase 4 to Phase 5 on Linux

Use the supplied one-terminal script. It preserves the existing `.env`, creates a PostgreSQL dump, retains the Phase 4 source folder, verifies the archive checksum, applies additive migrations, runs focused checks, and starts Phase 5.

Place these files in `~/Downloads`:

- `crowdsmarter-phase5.zip`
- `crowdsmarter-phase5.zip.sha256`
- `upgrade-crowdsmarter-to-phase5.sh`

Then run:

```bash
bash ~/Downloads/upgrade-crowdsmarter-to-phase5.sh
```

If Docker permission is denied:

```bash
newgrp docker
bash ~/Downloads/upgrade-crowdsmarter-to-phase5.sh
```

Do not use `sudo` for the script and never run `docker compose down -v`; `-v` removes the PostgreSQL volume.

After success, open `http://localhost:5173`. The public landing page is at `/`, and the authenticated application is at `/app`. Existing users, organisations, decisions, and reasoning records remain in the same PostgreSQL volume.
