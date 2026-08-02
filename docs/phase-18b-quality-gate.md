# Phase 18B quality gate

Phase 18B is accepted only when the release installer completes all of these gates before and after the live migration.

## Isolated backend gate

- build the exact candidate backend image;
- run Django system checks;
- detect migration drift;
- create a test database through pytest migrations;
- verify explicit platform capability is required even for a Django superuser;
- verify tenant details require support access;
- verify support access does not create membership;
- verify read-only access cannot perform operational actions;
- verify ownership transfer preserves at least one owner and writes audit history;
- verify the named operator command does not add real-client memberships.

## Isolated frontend gate

- TypeScript project check;
- platform overview and support-gate tests;
- AppShell, public homepage, demo request, and login regression tests;
- production Vite build.

## Live migration gate

- complete source and PostgreSQL backups;
- successful `platform_admin` migrations;
- explicit capability for the named operator when that account exists;
- automatic owner membership limited to the three marked fictional organisations;
- backend liveness and readiness;
- public contact configuration endpoint;
- public, login, and platform-administration routes;
- post-migration invariant checks.

No installer path may delete Docker volumes. A post-migration failure must restore the previous source and database backup.
