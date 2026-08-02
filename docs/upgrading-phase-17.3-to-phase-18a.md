# Upgrade from Phase 17.3 to Phase 18A

Place `crowdsmarter-phase18a.zip`, `crowdsmarter-phase18a.zip.sha256`, and `upgrade-crowdsmarter-to-phase18a.sh` directly in `~/Downloads`.

Run:

```bash
bash ~/Downloads/upgrade-crowdsmarter-to-phase18a.sh
```

The installer builds and validates the complete candidate frontend before stopping the current frontend. It then performs an atomic frontend replacement and verifies the public routes, not-found route, accessibility source markers, and mounted version.

It does not run migrations, dump or restore PostgreSQL, alter backend source, or delete Docker volumes.
