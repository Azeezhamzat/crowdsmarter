# Phase 18B R2 — Migration-state compatibility hotfix

This release corrects the serialized state of the `support_access_revocation_consistent` model constraint so it exactly matches migration `platform_admin.0001_initial`.

The SQL rule is unchanged. The correction prevents Django from proposing a redundant remove-and-recreate migration during `makemigrations --check --dry-run`.
