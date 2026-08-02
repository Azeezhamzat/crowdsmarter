# ADR 0030: Versioned organisation methods and explicit tenant governance

## Status

Accepted for Phase 17.

## Context

CrowdSmarter already provides built-in decision templates, but customer organisations need to govern their own repeatable methods without turning templates into automated recommendations. They also need clear account-level controls for identity, invitations, ownership, retention, deactivation, and deletion requests.

## Decision

Organisation methodology is represented by a stable `DecisionMethod` and immutable-after-approval `DecisionMethodVersion` records. Owners approve and retire versions; owners and administrators may prepare drafts. A decision may start from one approved organisation method version, and `DecisionMethodUsage` permanently records that provenance.

Organisation administration remains part of the modular monolith. Profile and branding settings live on the tenant. Invitation policy, retention, ownership transfer, deactivation, and deletion requests are service-layer commands with object permissions, audit events, and database constraints.

Draft methods are visible only to owners and administrators. Ordinary members can read approved methods but cannot see in-progress versions. A method contains prompts, required fields, checklists, and lifecycle expectations only. It cannot contain or apply a preferred option, final judgement, lifecycle transition, or resource allocation.

Deletion is never immediate. An owner must first deactivate the organisation, pass closure checks, type an explicit confirmation, and create a delayed request. Completion remains a later manual operational action.

## Consequences

- Organisations can standardise decision practice while keeping human judgement authoritative.
- Decisions retain the exact method version they used even after later revisions or retirement.
- Draft methodology and sensitive deletion history are not disclosed to ordinary members.
- Ownership and membership changes are attributable through append-only history.
- The application gains customer-account governance without adding a separate identity or policy service.
- Hard deletion and retention execution remain production-operations concerns for Phase 18 assurance.
