# Phase 17 release: Organisation methodology and administration

Phase 17 gives each customer organisation a governed way to define how important decisions should be framed and a safe way to administer its tenant account.

## Organisation-owned decision methods

Owners and administrators can create a method from a clean frame or clone a built-in template. Each method has versioned prompts for the decision question, purpose, context, scope, contribution guidance, evidence, assumptions, risks, stakeholders, checklists, and lifecycle expectations.

Draft versions are visible only to owners and administrators. Only an owner may approve a version. Approval freezes that version, retires the previous current version, and makes the new version available during guided decision creation. Decisions retain an immutable usage record identifying the exact approved version and human who applied it.

Methods are process guidance only. They cannot select an option, calculate a binding recommendation, change the decision lifecycle, or bypass final human authority.

## Organisation administration

Phase 17 adds:

- organisation description, website, brand name, and primary colour;
- owner-controlled invitation policy;
- configurable default invitation role;
- append-only membership and ownership history;
- explicit ownership transfer with rationale;
- owner-controlled retention waiting period;
- controlled deactivation with closure blockers;
- delayed, auditable deletion requests and cancellation;
- search, audit, export, and decision-dossier integration.

An organisation must close active decisions, invitations, contribution work, and facilitated sessions before deactivation. Deactivation does not delete data. A deletion request is accepted only after deactivation and starts a minimum 30-day waiting period.

## Local access

The Phase 16 to Phase 17 upgrader creates or repairs the local debug account `hello@crowdsmarter.com`. It generates a strong temporary password and writes it to a mode-`0600` file in `~/Downloads`. The requested password `Admin1` is deliberately not embedded because it is weak and unsuitable for an administrative account. The provisioner refuses to run when `DJANGO_DEBUG=false`.

## Non-goals

Phase 17 does not add automatic methodology enforcement, policy engines, automated organisation deletion, custom workflow code, single sign-on, billing, or a preferred decision outcome. Accessibility and production-assurance verification remain Phase 18.
