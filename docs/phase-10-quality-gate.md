# Phase 10 quality gate

Phase 10 is complete only when all of the following pass.

## Account security

- reset requests return the same public message for existing and missing accounts;
- reset tokens expire and become invalid after use;
- password validation uses Django's configured validators;
- password change requires the current password;
- password change preserves the current authenticated browser session;
- recovery and security endpoints are throttled;
- profile and password security actions are audited;
- CSRF protection remains active on every mutation.

## Data ownership

- complete organisation exports are manager-only;
- outsiders receive `404` through tenant-safe selectors;
- visible decision dossiers can be downloaded without cross-tenant data;
- archives contain a versioned manifest and stable identifiers;
- password hashes and invitation token digests are absent;
- downloads use private, no-store response headers;
- export actions are audited.

## Release

- Python and TypeScript sources parse;
- Django checks and migration drift checks pass;
- focused backend and frontend tests pass;
- the production frontend build succeeds;
- existing Phase 9 data and `.env` are preserved;
- automatic source rollback operates on failure;
- backend and frontend health checks pass before success is reported.
