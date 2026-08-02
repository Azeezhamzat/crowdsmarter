# Source provenance

This GitHub-ready source archive was reconstructed from the CrowdSmarter Phase 17.1 corrective release and includes the successfully validated Request Demo R4 frontend hotfix.

The R4 hotfix provides:

- the public `/request-demo` route and form;
- prominent Request a demo calls to action on the landing page;
- a branded not-found experience;
- the corrected AppShell command-palette test assertion.

For repository hygiene, user-specific local-development email addresses and names were replaced with generic examples, and historical local-login upgrade scripts now accept `CROWDSMARTER_LOCAL_LOGIN_EMAIL` with `owner@crowdsmarter.local` as the default. No production behaviour, migrations, tenant data model, or authentication security boundary was weakened.
