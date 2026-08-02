# Phase 18B release notes

Phase 18B adds product-aware platform administration and governed tenant support.

Highlights:

- explicit platform-administrator capability separate from Django superuser flags;
- protected `/platform-admin` workspace;
- global users, organisations, demo requests, service settings, and audit visibility;
- time-bounded read-only or operational support access;
- ownership transfer and organisation-state safeguards;
- no automatic membership in real client organisations;
- automatic owner access only for marked simulated organisations;
- configurable official contact channels, initially routed to `hello@crowdsmarter.com`.

This release includes database migrations. Existing tenant data and memberships are preserved.
