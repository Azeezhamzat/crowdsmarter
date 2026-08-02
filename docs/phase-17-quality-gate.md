# Phase 17 quality gate

Phase 17 is complete only when all requirements below pass on the upgrade target.

## Method governance

- Owners and administrators can create and edit draft methods.
- Only owners can approve or retire methods.
- Approved and retired versions are immutable and preserve approval attribution.
- Ordinary members cannot see draft methods or draft successor versions.
- A decision can use only an approved method from its own organisation.
- Method usage retains the exact version and applying human.
- No method can preselect an option or change lifecycle state.

## Organisation administration

- Profile and branding changes are tenant-scoped and audited.
- Owner-only invitation and retention policy is enforced server-side.
- Default invitation role is used by the interface.
- Ownership transfer preserves at least one owner and records append-only history.
- Deactivation requires owner confirmation, rationale, and closure checks.
- Deletion requests require deactivation, explicit confirmation, a waiting period, and owner authority.
- Ordinary members cannot view deletion-request history.

## Platform integration

- Method records are searchable and customer-exportable.
- Decision dossiers include method provenance.
- Existing invitation, decision, contribution, export, authentication, and offboarding behaviour remains intact.
- New APIs reject unknown command fields.
- Tenant isolation and object-level permissions have automated tests.
- Migrations have no drift.
- Frontend type checking, focused tests, and production build pass.
- Backend system checks and focused regression tests pass.
- Upgrade rollback restores both Phase 16 source and the pre-upgrade PostgreSQL database.

## Local account

- `hello@crowdsmarter.com` is active after a successful local-debug upgrade.
- A generated temporary password is stored only in a mode-`0600` file.
- No weak hard-coded password is introduced.
- Provisioning is refused outside debug mode.
