# Phase 3.1 release: Secure invitation onboarding

## Customer outcome

Organisation owners and administrators can invite a colleague without first creating that person's account or password. The invited person receives an expiring link, chooses their own password when needed, explicitly accepts membership, and enters only the organisation that invited them.

## Included

- organisation-controlled invitations for owner, administrator, contributor, and viewer roles;
- owner-only authority for owner-role invitations;
- secure random secrets stored only as keyed digests;
- browser-fragment invitation links that stay out of ordinary server URLs and referrer data;
- configurable seven-day default expiry;
- resend with token rotation and expiry extension;
- immediate revocation;
- email delivery through Django's configurable email backend;
- graceful delivery failure that preserves the pending invitation;
- development-only copyable acceptance links for zero-cost local testing;
- new-account creation with Django password validation;
- existing-account sign-in before acceptance;
- issuer-authority revalidation at acceptance;
- explicit membership creation and invitation audit events;
- removal of direct membership creation from the REST API;
- manager invitation list and acceptance user interface;
- backend, permission, API, component, and browser tests.

## Deliberately excluded

- unrestricted public self-registration;
- password reset and account recovery;
- email-address change;
- enterprise SSO or SCIM;
- bulk invitations;
- custom invitation email templates;
- automatic participant assignment after joining.

These are separate customer workflows and should be added only when validated.

## Upgrade behaviour

The release adds the `invitations` Django app and one new table. Existing users, organisations, memberships, decisions, reasoning records, and audit history remain unchanged. The membership collection becomes read-only: all new tenant access begins through invitation acceptance.

Local development continues to use console email at zero recurring cost. Because `DEBUG=true`, the organisation page also displays the current acceptance link after creation or resend. Production hides that link from API responses and requires configured email delivery.
