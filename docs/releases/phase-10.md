# Phase 10 release — account trust and customer data ownership

Phase 10 closes two trust-critical gaps: users can recover and maintain their own accounts, and customer organisations can take a portable copy of their governed decision records.

## Account self-service

- authenticated first-name and last-name editing;
- password change requiring the current password;
- current browser session preserved after a successful password change;
- anonymous password-reset requests with generic responses;
- time-limited Django reset tokens that become invalid after password change;
- reset secrets carried in the browser URL fragment;
- local development reset links displayed in the UI when console email is used;
- throttling and attributable security audit events.

Email-address change remains excluded because it requires a separately verified identity-change workflow.

## Customer-controlled exports

- complete organisation ZIP for active owners and administrators;
- portable decision dossier ZIP for active tenant members;
- versioned JSON for complete structured records;
- CSV copies of major registers;
- readable decision summary;
- stable identifiers and UTC timestamps;
- explicit exclusion of password hashes and invitation token digests;
- private, no-store download responses;
- auditable download events.

The synchronous export is appropriate for the current pre-revenue scale. The service boundary can later move archive generation to Celery or streaming responses without changing the export schema or endpoint contract.

## Product boundary

Phase 10 does not add email-address changes, session/device management, data import, secure evidence attachments, or retention/deletion workflows. Those remain separate security-sensitive slices.
