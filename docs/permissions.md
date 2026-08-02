# Permission model

## Organisation roles

| Role | Purpose |
|---|---|
| Owner | Ultimate organisational accountability; may appoint or remove owners |
| Administrator | Day-to-day tenant and membership administration, excluding owner control |
| Contributor | Creates and contributes to decisions but cannot administer the tenant |
| Viewer | Read-only tenant and decision visibility |

All roles require an active membership. Suspended memberships grant no access.

## Organisation and workspace permissions

| Action | Owner | Administrator | Contributor | Viewer | Outsider |
|---|:---:|:---:|:---:|:---:|:---:|
| Read organisation and memberships | ✓ | ✓ | ✓ | ✓ | — |
| Rename organisation | ✓ | ✓ | — | — | — |
| Invite non-owner members | ✓ | ✓ | — | — | — |
| Invite, resend, or revoke owner access | ✓ | — | — | — | — |
| Change/remove accepted non-owner memberships | ✓ | ✓ | — | — | — |
| Change/remove owners | ✓ | — | — | — | — |
| Read workspaces | ✓ | ✓ | ✓ | ✓ | — |
| Create or update workspaces | ✓ | ✓ | — | — | — |
| Read tenant audit log | ✓ | ✓ | — | — | — |

## Invitation rules

1. Contributors, viewers, suspended members, and outsiders cannot inspect or manage invitations.
2. Administrators may invite administrator, contributor, or viewer roles but never an owner.
3. Only an owner may issue, resend, or revoke an owner-role invitation.
4. Existing accounts must authenticate with the invited email before acceptance.
5. An invitation becomes unusable after expiry, revocation, acceptance, token rotation, or loss of issuer authority.
6. Cross-tenant invitation detail actions return `404` rather than disclosing existence.

## Decision permissions

Decision authority combines organisation role, decision ownership, participant role, and lifecycle state.

| Action | Org owner/admin | Decision owner | Decision maker | Contributor/reviewer | Observer/viewer | Outsider |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Read visible decision | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Create a decision | ✓ | ✓* | ✓* | ✓* | — | — |
| Edit framing in Draft/Framing | ✓ | ✓ | — | — | — | — |
| Transfer ownership in Draft/Framing | ✓ | ✓ | — | — | — | — |
| Manage participants before Under Review | ✓ | ✓ | — | — | — | — |
| Execute enabled ordinary lifecycle transition | ✓ | ✓ | — | — | — | — |
| Submit own formal position | If eligible participant | ✓ | ✓ | ✓ | — | — |
| Finalise at Ready for Decision | ✓ | ✓ | ✓ | — | — | — |
| Patch lifecycle status directly | — | — | — | — | — | — |

`*` An organisation contributor can create a decision they own; tenant managers may assign another active member as owner.

UI controls are advisory. Tenant-safe selectors and transactional services remain authoritative.

## Participant and position rules

1. Only active organisation members may be added as participants.
2. Decision-owner participation is created and maintained by the decision service.
3. The owner participant cannot be removed or assigned another role through participant endpoints.
4. Participant management is allowed only in Draft, Framing, and Open for Contribution.
5. Removed participants remain as historical records but are excluded from active lists.
6. Decision owners, decision makers, contributors, and reviewers may submit only their own position.
7. Observers cannot submit a formal position.
8. Positions are accepted only in Open for Contribution, Under Review, and Ready for Decision.
9. Revisions append a new immutable version; no role may edit or delete a submitted version.

## Finalisation rules

1. The decision must be `Ready for Decision`.
2. The caller must be an active organisation owner/administrator, the decision owner, or an active designated decision maker.
3. At least one active human authority must exist.
4. Every active decision owner and decision maker must have a current position.
5. The selected option must be active and belong to the same decision and organisation.
6. The caller must confirm that current positions were reviewed.
7. Dissent treatment is mandatory if any current position abstains, rejects all options, or supports another option.
8. Finalisation, the lifecycle transition, and audit events are one transaction.
9. Finalisation is immutable and cannot be performed through the generic transition endpoint.

## Offboarding rules

A membership cannot be removed if doing so would strand:

- ownership of an unfinished decision;
- ownership of an active assumption; or
- ownership of an unresolved risk.

Ordinary non-owner participant assignments are soft-removed and audited during authorised offboarding. Ownership must be transferred first where accountability would otherwise be lost.

## Outcomes and learning

All active organisation members may read the commitment, implementation, outcome review, and lessons for a visible decision. Only the decision owner or an organisation owner/administrator may:

- record commitment;
- transfer implementation ownership;
- begin implementation;
- open or complete outcome review;
- create, revise, or retire lessons;
- archive the decision.

A member who owns an active implementation record cannot be removed until ownership is transferred. Cross-tenant outcome, lesson, and search reads return `404`.
