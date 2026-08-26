"""Transactional platform-administration workflows."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit.services import record_event
from apps.demo_requests.models import DemoRequest
from apps.invitations.models import OrganisationInvitation
from apps.invitations.services import deliver_invitation
from apps.invitations.tokens import digest_token, generate_token
from apps.organisations.models import Membership, MembershipEvent, Organisation
from apps.organisations.services import organisation_deactivation_blockers

from .crypto import encrypt_secret
from .models import PlatformAdministrator, PlatformConfiguration, SupportAccessGrant
from .permissions import is_platform_administrator

User = get_user_model()


class PlatformAdministrationError(ValidationError):
    """Expected validation failure in platform-administration workflows."""


def _require_platform_administrator(actor: Any) -> PlatformAdministrator:
    if not is_platform_administrator(actor):
        raise PermissionDenied("An active platform-administrator capability is required.")
    return PlatformAdministrator.objects.get(
        user=actor,
        status=PlatformAdministrator.Status.ACTIVE,
    )


def _meaningful(value: str, field: str = "rationale") -> str:
    value = value.strip()
    if len(value) < 12:
        raise PlatformAdministrationError({field: "Record a specific reason of at least 12 characters."})
    return value


def current_support_access(*, actor: Any, organisation: Organisation) -> SupportAccessGrant | None:
    now = timezone.now()
    SupportAccessGrant.objects.filter(
        administrator=actor,
        organisation=organisation,
        status=SupportAccessGrant.Status.ACTIVE,
        expires_at__lte=now,
    ).update(status=SupportAccessGrant.Status.EXPIRED, updated_at=now)
    return (
        SupportAccessGrant.objects.filter(
            administrator=actor,
            organisation=organisation,
            status=SupportAccessGrant.Status.ACTIVE,
            expires_at__gt=now,
        )
        .select_related("administrator", "organisation", "revoked_by")
        .order_by("-expires_at")
        .first()
    )


def require_support_access(
    *, actor: Any, organisation: Organisation, operational: bool = False
) -> SupportAccessGrant:
    _require_platform_administrator(actor)
    grant = current_support_access(actor=actor, organisation=organisation)
    if grant is None:
        raise PermissionDenied(
            "Create a time-bounded support-access grant with a recorded reason before opening this tenant."
        )
    if operational and grant.access_level != SupportAccessGrant.AccessLevel.OPERATIONAL:
        raise PermissionDenied("This action requires an operational support-access grant.")
    return grant


@transaction.atomic
def grant_platform_administrator(
    *, actor: Any, user: Any, rationale: str
) -> PlatformAdministrator:
    _require_platform_administrator(actor)
    rationale = _meaningful(rationale)
    if not user.is_active:
        raise PlatformAdministrationError("Reactivate the user before granting platform administration.")
    item, created = PlatformAdministrator.objects.select_for_update().get_or_create(
        user=user,
        defaults={
            "status": PlatformAdministrator.Status.ACTIVE,
            "rationale": rationale,
            "granted_by": actor,
        },
    )
    previous_status = item.status
    if not created:
        item.status = PlatformAdministrator.Status.ACTIVE
        item.rationale = rationale
        item.granted_by = actor
        item.suspended_by = None
        item.suspended_at = None
        item.full_clean(validate_unique=False)
        item.save(
            update_fields=[
                "status",
                "rationale",
                "granted_by",
                "suspended_by",
                "suspended_at",
                "updated_at",
            ]
        )
    record_event(
        action="platform_administrator.granted",
        object_type="platform_administrator",
        object_id=str(item.id),
        actor=actor,
        metadata={
            "user_id": str(user.id),
            "email": user.email,
            "previous_status": previous_status if not created else None,
            "rationale": rationale,
        },
    )
    setattr(user, "_crowdsmarter_platform_admin", True)
    return item


@transaction.atomic
def suspend_platform_administrator(
    *, actor: Any, user: Any, rationale: str
) -> PlatformAdministrator:
    _require_platform_administrator(actor)
    rationale = _meaningful(rationale)
    if user.id == actor.id:
        raise PlatformAdministrationError("You cannot suspend your own platform-administrator capability.")
    item = PlatformAdministrator.objects.select_for_update().get(user=user)
    if item.status == PlatformAdministrator.Status.SUSPENDED:
        raise PlatformAdministrationError("This platform-administrator capability is already suspended.")
    active_ids = list(
        PlatformAdministrator.objects.select_for_update()
        .filter(status=PlatformAdministrator.Status.ACTIVE, user__is_active=True)
        .values_list("id", flat=True)
    )
    if len(active_ids) <= 1:
        raise PlatformAdministrationError("CrowdSmarter must retain at least one active platform administrator.")
    item.status = PlatformAdministrator.Status.SUSPENDED
    item.suspended_by = actor
    item.suspended_at = timezone.now()
    item.rationale = rationale
    item.full_clean(validate_unique=False)
    item.save(
        update_fields=["status", "suspended_by", "suspended_at", "rationale", "updated_at"]
    )
    SupportAccessGrant.objects.filter(
        administrator=user,
        status=SupportAccessGrant.Status.ACTIVE,
    ).update(
        status=SupportAccessGrant.Status.REVOKED,
        revoked_by=actor,
        revoked_at=timezone.now(),
        updated_at=timezone.now(),
    )
    record_event(
        action="platform_administrator.suspended",
        object_type="platform_administrator",
        object_id=str(item.id),
        actor=actor,
        metadata={"user_id": str(user.id), "email": user.email, "rationale": rationale},
    )
    return item


@transaction.atomic
def set_user_active(*, actor: Any, user: Any, is_active: bool, rationale: str):
    _require_platform_administrator(actor)
    rationale = _meaningful(rationale)
    if user.id == actor.id and not is_active:
        raise PlatformAdministrationError("You cannot suspend your own account.")
    previous = user.is_active
    if previous == is_active:
        return user
    if not is_active and PlatformAdministrator.objects.filter(
        user=user, status=PlatformAdministrator.Status.ACTIVE
    ).exists():
        raise PlatformAdministrationError(
            "Suspend the platform-administrator capability before suspending this account."
        )
    if not is_active:
        sole_owner_organisations: list[str] = []
        owned_memberships = Membership.objects.select_related("organisation").filter(
            user=user,
            role=Membership.Role.OWNER,
            status=Membership.Status.ACTIVE,
        )
        for membership in owned_memberships:
            has_other_active_owner = Membership.objects.filter(
                organisation=membership.organisation,
                role=Membership.Role.OWNER,
                status=Membership.Status.ACTIVE,
                user__is_active=True,
            ).exclude(user=user).exists()
            if not has_other_active_owner:
                sole_owner_organisations.append(membership.organisation.name)
        if sole_owner_organisations:
            raise PlatformAdministrationError(
                {
                    "is_active": (
                        "Transfer ownership before suspending this account. Sole ownership: "
                        + ", ".join(sorted(sole_owner_organisations))
                    )
                }
            )
    user.is_active = is_active
    user.save(update_fields=["is_active"])
    record_event(
        action="platform_user.reactivated" if is_active else "platform_user.suspended",
        object_type="user",
        object_id=str(user.id),
        actor=actor,
        metadata={"email": user.email, "previous": previous, "rationale": rationale},
    )
    return user


@transaction.atomic
def create_support_access(
    *, actor: Any, organisation: Organisation, access_level: str, reason: str, duration_hours: int
) -> SupportAccessGrant:
    _require_platform_administrator(actor)
    reason = _meaningful(reason, "reason")
    configuration = PlatformConfiguration.objects.select_for_update().get(singleton_key=1)
    if duration_hours > configuration.support_access_max_hours:
        raise PlatformAdministrationError(
            {"duration_hours": f"Support access is limited to {configuration.support_access_max_hours} hours."}
        )
    now = timezone.now()
    SupportAccessGrant.objects.filter(
        administrator=actor,
        organisation=organisation,
        status=SupportAccessGrant.Status.ACTIVE,
    ).update(
        status=SupportAccessGrant.Status.REVOKED,
        revoked_by=actor,
        revoked_at=now,
        updated_at=now,
    )
    grant = SupportAccessGrant(
        administrator=actor,
        organisation=organisation,
        access_level=access_level,
        reason=reason,
        expires_at=now + timedelta(hours=duration_hours),
    )
    grant.full_clean(validate_unique=False)
    grant.save()
    record_event(
        action="platform_support_access.granted",
        object_type="support_access_grant",
        object_id=str(grant.id),
        actor=actor,
        organisation=organisation,
        metadata={
            "access_level": access_level,
            "reason": reason,
            "expires_at": grant.expires_at,
        },
    )
    return grant


@transaction.atomic
def revoke_support_access(*, actor: Any, grant: SupportAccessGrant, rationale: str) -> SupportAccessGrant:
    _require_platform_administrator(actor)
    rationale = _meaningful(rationale)
    grant = SupportAccessGrant.objects.select_for_update().select_related("organisation").get(id=grant.id)
    if grant.status != SupportAccessGrant.Status.ACTIVE:
        raise PlatformAdministrationError("Only active support access can be revoked.")
    grant.status = SupportAccessGrant.Status.REVOKED
    grant.revoked_by = actor
    grant.revoked_at = timezone.now()
    grant.save(update_fields=["status", "revoked_by", "revoked_at", "updated_at"])
    record_event(
        action="platform_support_access.revoked",
        object_type="support_access_grant",
        object_id=str(grant.id),
        actor=actor,
        organisation=grant.organisation,
        metadata={"rationale": rationale},
    )
    return grant


def _membership_event(
    *, actor: Any, membership: Membership, kind: str, previous_role: str, new_role: str, note: str
) -> None:
    MembershipEvent.objects.create(
        organisation=membership.organisation,
        membership_id_snapshot=membership.id,
        user=membership.user,
        actor=actor,
        kind=kind,
        previous_role=previous_role,
        new_role=new_role,
        previous_status=membership.status,
        new_status=membership.status,
        note=note,
    )


@transaction.atomic
def platform_transfer_ownership(
    *,
    actor: Any,
    organisation: Organisation,
    target_membership: Membership,
    rationale: str,
    confirmation: str,
    demote_existing_owners: bool,
) -> Membership:
    require_support_access(actor=actor, organisation=organisation, operational=True)
    rationale = _meaningful(rationale)
    if confirmation.strip() != organisation.name:
        raise PlatformAdministrationError({"confirmation": "Enter the organisation name exactly."})
    organisation = Organisation.objects.select_for_update().get(id=organisation.id)
    target = Membership.objects.select_for_update().select_related("user", "organisation").get(
        id=target_membership.id,
        organisation=organisation,
        status=Membership.Status.ACTIVE,
    )
    if not target.user.is_active:
        raise PlatformAdministrationError("The new owner account must be active.")
    previous_role = target.role
    target.role = Membership.Role.OWNER
    target.save(update_fields=["role", "updated_at"])
    _membership_event(
        actor=actor,
        membership=target,
        kind=MembershipEvent.Kind.OWNERSHIP_TRANSFERRED,
        previous_role=previous_role,
        new_role=Membership.Role.OWNER,
        note=rationale,
    )
    demoted: list[str] = []
    if demote_existing_owners:
        others = list(
            Membership.objects.select_for_update()
            .select_related("user")
            .filter(
                organisation=organisation,
                role=Membership.Role.OWNER,
                status=Membership.Status.ACTIVE,
            )
            .exclude(id=target.id)
        )
        for membership in others:
            membership.role = Membership.Role.ADMIN
            membership.save(update_fields=["role", "updated_at"])
            _membership_event(
                actor=actor,
                membership=membership,
                kind=MembershipEvent.Kind.ROLE_CHANGED,
                previous_role=Membership.Role.OWNER,
                new_role=Membership.Role.ADMIN,
                note=f"Platform-admin ownership transfer to {target.user.email}: {rationale}",
            )
            demoted.append(membership.user.email)
    record_event(
        action="platform_organisation.ownership_transferred",
        object_type="organisation",
        object_id=str(organisation.id),
        actor=actor,
        organisation=organisation,
        metadata={
            "new_owner_user_id": str(target.user_id),
            "new_owner_email": target.user.email,
            "demoted_owner_emails": demoted,
            "rationale": rationale,
        },
    )
    return target


@transaction.atomic
def platform_change_organisation_state(
    *, actor: Any, organisation: Organisation, action: str, rationale: str, confirmation: str
) -> Organisation:
    require_support_access(actor=actor, organisation=organisation, operational=True)
    rationale = _meaningful(rationale)
    if confirmation.strip() != organisation.name:
        raise PlatformAdministrationError({"confirmation": "Enter the organisation name exactly."})
    organisation = Organisation.objects.select_for_update().get(id=organisation.id)
    if action == "deactivate":
        if organisation.status == Organisation.Status.DEACTIVATED:
            raise PlatformAdministrationError("The organisation is already deactivated.")
        blockers = organisation_deactivation_blockers(organisation=organisation)
        if blockers:
            raise PlatformAdministrationError({"blockers": blockers})
        organisation.status = Organisation.Status.DEACTIVATED
        organisation.deactivated_at = timezone.now()
        organisation.deactivated_by = actor
        event_action = "platform_organisation.deactivated"
    elif action == "reactivate":
        if organisation.status == Organisation.Status.ACTIVE:
            raise PlatformAdministrationError("The organisation is already active.")
        organisation.status = Organisation.Status.ACTIVE
        organisation.deactivated_at = None
        organisation.deactivated_by = None
        event_action = "platform_organisation.reactivated"
    else:
        raise PlatformAdministrationError("Choose a valid organisation state action.")
    organisation.full_clean(exclude=["created_by"], validate_unique=False)
    organisation.save(
        update_fields=["status", "deactivated_at", "deactivated_by", "updated_at"]
    )
    record_event(
        action=event_action,
        object_type="organisation",
        object_id=str(organisation.id),
        actor=actor,
        organisation=organisation,
        metadata={"rationale": rationale},
    )
    return organisation


@transaction.atomic
def platform_invitation_action(
    *, actor: Any, invitation: OrganisationInvitation, action: str, rationale: str
) -> tuple[OrganisationInvitation, dict[str, str | None]]:
    organisation = invitation.organisation
    require_support_access(actor=actor, organisation=organisation, operational=True)
    rationale = _meaningful(rationale)
    invitation = OrganisationInvitation.objects.select_for_update().select_related("organisation").get(
        id=invitation.id
    )
    if invitation.status != OrganisationInvitation.Status.PENDING:
        raise PlatformAdministrationError("Only a pending invitation can be changed.")
    if action == "revoke":
        invitation.status = OrganisationInvitation.Status.REVOKED
        invitation.revoked_at = timezone.now()
        invitation.save(update_fields=["status", "revoked_at", "updated_at"])
        record_event(
            action="platform_invitation.revoked",
            object_type="organisation_invitation",
            object_id=str(invitation.id),
            actor=actor,
            organisation=organisation,
            metadata={"email": invitation.email, "rationale": rationale},
        )
        return invitation, {"delivery_status": None, "acceptance_url": None}
    if action != "resend":
        raise PlatformAdministrationError("Choose a valid invitation action.")
    issuer_membership = (
        Membership.objects.select_for_update()
        .select_related("user")
        .filter(
            organisation=organisation,
            status=Membership.Status.ACTIVE,
            role=Membership.Role.OWNER,
        )
        .order_by("created_at")
        .first()
    )
    if issuer_membership is None:
        raise PlatformAdministrationError(
            "The organisation has no active owner who can remain accountable for this invitation."
        )
    raw_token = generate_token()
    invitation.token_digest = digest_token(raw_token)
    invitation.expires_at = timezone.now() + timedelta(
        hours=int(getattr(settings, "INVITATION_EXPIRY_HOURS", 168))
    )
    invitation.invited_by = issuer_membership.user
    invitation.save(update_fields=["token_digest", "expires_at", "invited_by", "updated_at"])
    delivery = deliver_invitation(invitation=invitation, raw_token=raw_token, actor=actor)
    record_event(
        action="platform_invitation.resent",
        object_type="organisation_invitation",
        object_id=str(invitation.id),
        actor=actor,
        organisation=organisation,
        metadata={"email": invitation.email, "rationale": rationale, "delivery": delivery.status},
    )
    return invitation, {
        "delivery_status": delivery.status,
        "acceptance_url": delivery.acceptance_url,
    }


@transaction.atomic
def update_platform_configuration(*, actor: Any, values: dict[str, Any], rationale: str) -> PlatformConfiguration:
    _require_platform_administrator(actor)
    rationale = _meaningful(rationale)
    item = PlatformConfiguration.objects.select_for_update().get(singleton_key=1)
    before = {field: getattr(item, field) for field in values}
    for field, value in values.items():
        setattr(item, field, value)
    item.full_clean(validate_unique=False)
    item.save(update_fields=[*values.keys(), "updated_at"])
    record_event(
        action="platform_configuration.updated",
        object_type="platform_configuration",
        object_id=str(item.id),
        actor=actor,
        metadata={
            "before": before,
            "after": {field: getattr(item, field) for field in values},
            "rationale": rationale,
        },
    )
    return item


@transaction.atomic
def set_ai_provider(
    *, actor: Any, provider_key: str, model: str, rationale: str
) -> PlatformConfiguration:
    """Choose which AI provider backend serves decision reviews."""
    _require_platform_administrator(actor)
    rationale = _meaningful(rationale)
    item = PlatformConfiguration.objects.select_for_update().get(singleton_key=1)
    previous_key = item.ai_provider_key
    previous_model = item.ai_provider_model
    item.ai_provider_key = provider_key
    item.ai_provider_model = model.strip()
    item.full_clean(validate_unique=False, validate_constraints=False)
    item.save(update_fields=["ai_provider_key", "ai_provider_model", "updated_at"])
    record_event(
        action="platform_configuration.ai_provider_changed",
        object_type="platform_configuration",
        object_id=str(item.id),
        actor=actor,
        metadata={
            "previous_provider": previous_key,
            "new_provider": item.ai_provider_key,
            "previous_model": previous_model,
            "new_model": item.ai_provider_model,
            "rationale": rationale,
        },
    )
    return item


@transaction.atomic
def set_ai_provider_api_key(
    *, actor: Any, api_key: str, rationale: str
) -> PlatformConfiguration:
    """Store a new provider API key, encrypted at rest.

    The raw key is never written to the audit log, only whether one was
    already set and its last 4 characters, enough for an administrator to
    recognise which key is active without exposing it.
    """
    _require_platform_administrator(actor)
    rationale = _meaningful(rationale)
    api_key = api_key.strip()
    if not api_key:
        raise PlatformAdministrationError({"api_key": "Provide a non-empty API key."})
    item = PlatformConfiguration.objects.select_for_update().get(singleton_key=1)
    had_key_before = item.ai_provider_api_key_is_set
    item.ai_provider_api_key_encrypted = encrypt_secret(api_key)
    item.save(update_fields=["ai_provider_api_key_encrypted", "updated_at"])
    record_event(
        action="platform_configuration.ai_provider_api_key_set",
        object_type="platform_configuration",
        object_id=str(item.id),
        actor=actor,
        metadata={
            "had_key_before": had_key_before,
            "key_last_4": api_key[-4:] if len(api_key) >= 4 else "****",
            "rationale": rationale,
        },
    )
    return item


@transaction.atomic
def clear_ai_provider_api_key(*, actor: Any, rationale: str) -> PlatformConfiguration:
    """Remove the stored API key, reverting to the rules provider if a keyed provider was active."""
    _require_platform_administrator(actor)
    rationale = _meaningful(rationale)
    item = PlatformConfiguration.objects.select_for_update().get(singleton_key=1)
    item.ai_provider_api_key_encrypted = ""
    if item.ai_provider_key != PlatformConfiguration.AIProviderKey.RULES:
        item.ai_provider_key = PlatformConfiguration.AIProviderKey.RULES
    item.save(
        update_fields=["ai_provider_api_key_encrypted", "ai_provider_key", "updated_at"]
    )
    record_event(
        action="platform_configuration.ai_provider_api_key_cleared",
        object_type="platform_configuration",
        object_id=str(item.id),
        actor=actor,
        metadata={"rationale": rationale},
    )
    return item


def test_ai_provider_connection(*, actor: Any) -> dict[str, Any]:
    """Make the smallest possible live call to confirm the configured provider is reachable.

    Never raises for a provider-side failure (missing key, bad credentials, network
    error) - those are all reported back as an ok=False result an administrator can
    read, not a 500. Only a permission failure raises.
    """
    _require_platform_administrator(actor)
    from apps.ai_assistance.providers.registry import get_provider

    try:
        provider = get_provider()
    except Exception as error:  # noqa: BLE001 - surface any failure as a diagnosable result
        result = {"ok": False, "detail": str(error), "provider_key": "", "provider_label": ""}
    else:
        outcome = provider.test_connection()
        result = {
            "ok": outcome.ok,
            "detail": outcome.detail,
            "provider_key": provider.key,
            "provider_label": provider.label,
        }
    record_event(
        action="platform_configuration.ai_provider_connection_tested",
        object_type="platform_configuration",
        object_id=str(PlatformConfiguration.load().id),
        actor=actor,
        metadata={"ok": result["ok"], "provider_key": result["provider_key"]},
    )
    return result


@transaction.atomic
def update_demo_request_status(
    *, actor: Any, demo_request: DemoRequest, status: str, rationale: str
) -> DemoRequest:
    _require_platform_administrator(actor)
    rationale = _meaningful(rationale)
    item = DemoRequest.objects.select_for_update().get(id=demo_request.id)
    previous = item.status
    item.status = status
    item.save(update_fields=["status", "updated_at"])
    record_event(
        action="platform_demo_request.status_changed",
        object_type="demo_request",
        object_id=str(item.id),
        actor=actor,
        metadata={
            "previous_status": previous,
            "status": status,
            "work_email": item.work_email,
            "organisation_name": item.organisation_name,
            "rationale": rationale,
        },
    )
    return item
