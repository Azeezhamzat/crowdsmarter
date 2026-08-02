# Administrator access

CrowdSmarter distinguishes platform administration from organisation membership.

## Product administration

Open `/platform-admin`. An active `PlatformAdministrator` capability is required. Platform authority allows service-wide operations but does not silently add the operator to customer organisations.

To inspect tenant details, record a reasoned support-access grant in the tenant support workspace. Access is visible, scoped, expiring, and audited.

## Technical Django administration

Open the backend `/admin/` route only for technical recovery and low-level diagnosis. It requires Django `is_staff` and `is_superuser` flags and can bypass product workflow safeguards.

## Grant the named operator

```bash
docker compose exec backend python manage.py ensure_platform_admin \
  --email hello@crowdsmarter.com \
  --technical-admin \
  --demo-organisations
```

The demo option grants owner membership only in CrowdSmarter's three fictional demonstration organisations. Real clients remain separated.
