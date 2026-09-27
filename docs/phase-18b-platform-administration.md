# Phase 18B — Platform administration and tenant governance

Phase 18B introduces CrowdSmarter's product-aware administration layer. It separates service-wide authority from membership in a customer organisation.

## Permission model

An active `PlatformAdministrator` record is required for `/api/v1/platform-admin/*` and `/platform-admin`. Django's `is_staff` and `is_superuser` flags remain technical recovery permissions and do not grant product-level platform authority by themselves.

Platform administrators can see safe service-wide summaries, users, decision enquiries, service configuration, and audit events. They do not silently become members of customer organisations and do not gain contributor identity in customer decisions.

## Governed support access

Opening tenant details requires a `SupportAccessGrant` with:

- a specific reason;
- read-only or operational scope;
- an expiry time bounded by platform policy;
- attributable creation and revocation events.

Operational support access permits protected tenant-administration actions such as ownership transfer, invitation intervention, and organisation deactivation or reactivation. It does not create membership and does not bypass normal contribution or decision-participation rules.

## Platform workspace

The `/platform-admin` workspace provides:

- service overview and operational counts;
- organisation directory;
- user activation and suspension;
- explicit platform-administrator capability management;
- decision-enquiry processing;
- official contact and support-access configuration;
- global audit review;
- a tenant support workspace with visible scope and expiry.

## Bootstrap behaviour

During migration, existing active Django superusers receive an explicit platform-administrator capability. Only the three clearly marked simulated organisations grant those administrators owner membership automatically. Real client organisations retain explicit tenant membership boundaries.

The management command below can be used for a named operator:

```bash
python manage.py ensure_platform_admin \
  --email hello@crowdsmarter.com \
  --technical-admin \
  --demo-organisations \
  --rationale "Named CrowdSmarter platform operator responsible for tenant governance."
```

Omit `--technical-admin` when Django technical access is unnecessary. Omit `--demo-organisations` to avoid all automatic tenant membership.

## Audit actions

Material actions append audit events, including support access, capability grants and suspensions, user state changes, ownership transfer, organisation state changes, invitation actions, decision-enquiry state changes, and platform-configuration updates.
