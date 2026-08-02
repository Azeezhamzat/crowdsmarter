# Upgrade Phase 16 to Phase 17.1 on Linux

Place these files directly in `~/Downloads`:

- `crowdsmarter-phase17.1.zip`
- `crowdsmarter-phase17.1.zip.sha256`
- `upgrade-crowdsmarter-to-phase17.1.sh`

Ensure the local installation has `DJANGO_DEBUG=true`, then run:

```bash
bash ~/Downloads/upgrade-crowdsmarter-to-phase17.1.sh
```

The upgrader removes containers left by the defective Phase 17 script without deleting their volumes, pins the active Compose project to `crowdsmarter`, backs up PostgreSQL, preserves Phase 16 source, validates the release, and exits non-zero after any rollback.

After success, open the exact credentials file path printed by the script and sign in with `hello@crowdsmarter.com`.
