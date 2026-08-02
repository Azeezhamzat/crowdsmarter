# Upgrade from Phase 17.1 R4 to Phase 17.2

Use `upgrade-crowdsmarter-to-phase17.2.sh` from `~/Downloads` alongside the Phase 17.2 archive and checksum.

This is an atomic frontend-only upgrade. It creates a timestamped frontend backup, replaces the frontend from the verified archive, executes the frontend quality gate, and recreates only the frontend service. It does not stop, migrate, dump, restore, or otherwise modify PostgreSQL.
