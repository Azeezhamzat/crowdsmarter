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

## Phase 6 permissions

- Notifications are visible and mutable only by their recipient.
- Any active organisation member may read organisation analytics.
- Active owners, administrators, and contributors may request an advisory review when the decision is between `Framing` and `Lessons Learned`; viewers cannot request one.
- An advisory review is visible only to active members of its organisation.
- The requesting human, decision owner, organisation owner, or administrator may acknowledge or dismiss a completed review.
- Acknowledgement and dismissal are mutually exclusive and cannot be overwritten.
- No AI provider or task receives a user identity capable of finalising a decision or changing a customer record.

## Phase 7 collaboration and portfolio permissions

- Any active organisation member may read the organisation portfolio and decisions they can already access.
- Personal work contains only decisions from organisations where the user has an active membership.
- Organisation owners and administrators may contribute to any non-archived decision in their tenant.
- Active decision owners, decision makers, contributors, and reviewers may contribute to non-archived decisions.
- Observers and organisation viewers without a non-observer participant role cannot add discussion entries.
- The decision owner and organisation owners or administrators may resolve questions and concerns.
- Original discussion content cannot be edited or deleted through the API or Django administration.

## Phase 8 guided creation and overview permissions

- Any authenticated user may read the built-in template catalogue. It contains product prompts only and no customer records.
- Draft creation retains the existing workspace permission matrix: owners and administrators may assign any active member as owner; contributors may create only a draft they own; viewers cannot create decisions.
- Only active organisation members with access to a decision may read its overview.
- The overview grants no mutation capability. Editing, participant management, transitions, positions, finalisation, and outcomes continue to use their existing object-level policies and service checks.

## Phase 10 account and export permissions

- An authenticated user may edit only their own first and last name.
- An authenticated user may change only their own password and must provide the current password.
- Password-reset request and confirmation endpoints are anonymous but CSRF protected and throttled.
- Only active organisation owners and administrators may download a complete organisation archive.
- Any active member who can resolve a decision through the tenant-safe selector may download that decision dossier.
- Export endpoints do not grant access to records that are otherwise outside the caller's tenant.

## Foresight permissions

| Action | Owner | Administrator | Contributor | Viewer |
|---|---:|---:|---:|---:|
| Read sources, research claims, signals, watchlists, and feeds | Yes | Yes | Yes | Yes |
| Create sources, research claims, and signals | Yes | Yes | Yes | No |
| Edit own source | Yes | Yes | Yes | No |
| Edit any source | Yes | Yes | No | No |
| Edit claims owned or created by self | Yes | Yes | Yes | No |
| Edit any research claim | Yes | Yes | No | No |
| Link/unlink same-tenant sources on an editable claim | Yes | Yes | Yes | No |
| Edit signal owned or created by self | Yes | Yes | Yes | No |
| Edit any signal or watchlist | Yes | Yes | No | No |
| Upload private source files | Yes | Yes | Own sources | No |
| Download private source files | Yes | Yes | Yes | Yes |
| Create and synchronise owned feeds | Yes | Yes | Yes | No |
| Link signals to same-tenant decisions | Yes | Yes | Yes | No |

A viewer can inspect private source files and research claims because active
tenant membership already grants read access to the organisation's decision
knowledge. Files are never accessible through public media URLs. Active feed,
claim, signal, and watchlist ownership must be transferred before the owner can
be removed from the organisation.

## Phase 12 foresight permissions

Active contributors, administrators, and owners may create systems-mapping records. Viewers remain read-only. Canvas owners, record creators, and organisation managers may edit records where an edit route exists. Owners assigned to canvases, drivers, or open strategic implications must be transferred before their organisation membership can be removed. Archived canvases are read-only for every role.

## Phase 13 scenario-intelligence permissions

Active contributors, administrators, and owners may create scenario sets, worlds, driver states, reviews, wind-tunnel assessments, implication links, signposts, and observations. Viewers remain read-only. Scenario-set owners, record creators, and organisation managers may edit scenario sets and worlds where an edit route exists. A user may maintain only their own structured review. Scenario-set and active-signpost ownership must be transferred before organisation removal. Archived canvases and archived scenario sets are read-only for every role.

## Phase 14 collective-evaluation permissions

- active organisation members may read same-tenant evaluation and prioritisation workspaces;
- active decision participants with contributor, reviewer, decision-maker, or decision-owner capability may submit only their own evaluation response;
- observers and removed participants cannot submit;
- exercise owners, decision owners, and organisation managers configure criteria, create rounds, open or close rounds, and update exercise governance;
- any eligible contributor may publish their own minority report; it remains attributable even when the round is peer-anonymous;
- active organisation contributors may record only their own portfolio assessments while the portfolio is open;
- portfolio owners and organisation managers configure the envelope, criteria, and candidates and record authority selections;
- peer anonymity controls representation to peers, not system attribution, export ownership, legal discovery, or authorised audit;
- sealed-result rules apply equally to managers and contributors until closure, preventing privileged early anchoring;
- active exercise and portfolio ownership prevents membership removal until ownership is transferred or the record is archived.

## Phase 15 integrated analysis permissions

- Any active organisation member who can view a decision may read the integrated analysis workspace.
- Organisation owners and administrators, the decision owner, and active decision makers may manage quality reviews and executive summaries while the decision remains between Draft and Ready for Decision.
- Active non-viewer decision participants other than observers may create governed analysis issues during those writable states.
- Only the assigned issue owner or an accountable analysis manager may update an issue.
- Only accountable analysis managers may transfer issue ownership.
- Draft quality reviews and executive summaries are visible only to accountable analysis managers.
- Published reviews, approved summaries, and all superseded versions are read-only.
- Archived and post-finalisation decisions expose Phase 15 records as read-only; Phase 15 commands cannot alter lifecycle history.
- Tenant outsiders receive `404`, not a permission response that confirms an object exists.

## Phase 15.1 public and operational permissions

- Anyone with a valid same-origin CSRF token may submit a rate-limited decision enquiry.
- Public callers cannot list, retrieve, update, or delete decision enquiries.
- Decision-enquiry review uses protected platform or Django administration and requires the corresponding administrator authority.
- `ensure_local_owner` and `reset_local_password` are management commands, not API endpoints, and reject execution unless `DJANGO_DEBUG=true`.
- Public demo submission never grants product access; organisation membership remains invitation controlled.

## Phase 16 contribution permissions

- Organisation owners and administrators, the decision owner, and active decision makers/reviewers may manage contribution requests while the decision remains in a writable pre-finalisation state.
- Assignees must be active, non-observer decision participants.
- Named reviewers must be an organisation owner/administrator or an active decision owner, decision maker, or reviewer.
- Only the assignee may create or update a draft and submit a revision.
- Only the named reviewer or an accountable authority may review a submitted revision.
- Draft requests are visible only to managers until opened. Draft submission content is visible only to the assignee, named reviewer, and accountable authorities.
- Session status, attendance, run-of-show creation, and agenda execution may be managed only by the facilitator or an accountable authority. Only one agenda item may be live, and the live item must be completed or skipped before session closure.
- Only the facilitator or an accountable authority may save a session-quality review, and only after the session is closed. The review is a human reflection and does not change decision authority or participant records.
- A session invite may name an active decision participant as a participant or observer. This session role records how the person is involved in the workshop; it does not grant decision authority or make an observer eligible for a contribution assignment.
- Archived and other non-writable decisions expose read-only history.
- Member removal is blocked while active assignments, pending named reviews, or live facilitation responsibility remains.

## Phase 17 methodology and administration permissions

- Owners and administrators may prepare and revise draft organisation methods.
- Only owners may approve or retire methods.
- Contributors and viewers may read approved methods but cannot see drafts or draft successor versions.
- Owners and administrators may edit ordinary profile and branding fields.
- Only owners may change invitation policy, retention, ownership, deactivation, reactivation, or deletion requests.
- Membership history is visible to owners and administrators; deletion-request history is owner-only.
- Every permission is checked server-side; hidden frontend controls are not an authority boundary.

## Platform administration

Phase 18B separates service-wide authority from tenant membership. An active `PlatformAdministrator` capability permits access to the protected platform workspace and safe global summaries. Django `is_staff` or `is_superuser` alone does not grant this product permission.

Tenant details require a time-bounded `SupportAccessGrant`. Read-only support permits inspection; operational support permits protected ownership, invitation, and organisation-state interventions. Neither mode creates membership or grants contributor identity in a client decision. Every grant and material action is attributable in the audit log.
