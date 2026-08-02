# Upgrade from Phase 17.2 to Phase 17.3

Place `crowdsmarter-phase17.3.zip`, `crowdsmarter-phase17.3.zip.sha256`, and `upgrade-crowdsmarter-to-phase17.3.sh` directly in `~/Downloads`.

Run:

```bash
bash ~/Downloads/upgrade-crowdsmarter-to-phase17.3.sh
```

The installer builds and validates the candidate frontend before stopping the current frontend. It then performs an atomic frontend replacement and verifies the public routes and installed source markers. It does not run migrations or any PostgreSQL command.
