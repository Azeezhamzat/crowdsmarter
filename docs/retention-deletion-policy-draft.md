# Data retention and deletion policy — owner-approval draft

**Version:** 0.1  
**Prepared:** 2026-08-30  
**Approval status:** Pending product owner and legal/privacy review

This document is an operational draft, not a claim of legal compliance. It becomes the agreed policy only when the accountable owner records approval, effective date, jurisdictions, and exceptions.

## Principles

CrowdSmarter keeps personal and customer data only for a documented product, contractual, security, or legal purpose. Tenant deletion is delayed, reviewable, auditable, and never automatic. A legal hold, active dispute, security investigation, or backup-recovery requirement pauses deletion and must be documented.

## Proposed schedule

| Data class | Active use | After approved tenant deletion | Proposed limit |
| --- | --- | --- | --- |
| Tenant decision records and private uploads | While the tenant is active | Delete from primary systems after the configured waiting period and manual review | 30-day minimum waiting period; owner may configure longer |
| User account/profile | While account or required memberships are active | Delete or irreversibly anonymise when no longer required, subject to tenant and security obligations | Review with the tenant deletion or verified account request |
| Append-only security/audit events | While needed for accountability and investigations | Minimise or pseudonymise where compatible with legal obligations | Approval required before setting a fixed term |
| Application logs | Operational troubleshooting and security monitoring | Automatically expire | 7 days in the supplied local Loki configuration |
| Database backups | Disaster recovery | Expire through backup rotation; do not selectively edit immutable backups | Proposed 35 daily plus 12 monthly copies |
| Public decision enquiries | Qualification and follow-up | Delete or anonymise when no longer useful or consent/legitimate purpose ends | Owner must approve a fixed term before launch |

## Current technical workflow

1. An owner deactivates the organisation.
2. An owner submits an auditable deletion request with a reason.
3. CrowdSmarter sets `earliest_deletion_at` using the organisation policy, never less than 30 days.
4. The daily report identifies due requests and blockers without deleting data.
5. An authorised human verifies identity, exports, contractual obligations, legal hold, support cases, backup impact, and scope.
6. Permanent deletion requires a separately approved runbook and two-person evidence. That destructive executor is intentionally not implemented yet.

Preview the queue:

```bash
docker compose exec backend python manage.py retention_report --json
```

Make automation fail when manual review is due:

```bash
docker compose exec backend python manage.py retention_report --fail-if-due
```

## Approval record

Before launch, record: accountable owner; privacy/legal reviewer; effective date; jurisdiction and lawful-basis assumptions; fixed terms for audit events and decision enquiries; backup rotation; legal-hold authority; deletion executor and verification procedure; and customer-facing notice version.
