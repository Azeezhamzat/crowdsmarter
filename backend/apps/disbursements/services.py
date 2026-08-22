"""Disbursement configuration and payout issuance, audit-redacted like the AI provider settings."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.audit.services import record_event
from apps.organisations.models import Membership
from apps.platform_admin.crypto import encrypt_secret

from .models import Disbursement, OrganisationDisbursementConfiguration
from .providers.registry import get_provider


class DisbursementServiceError(ValidationError):
    pass


def _require_manager(*, actor, organisation) -> Membership:
    membership = organisation.memberships.filter(user=actor, status=Membership.Status.ACTIVE).first()
    if membership is None or membership.role not in {Membership.Role.OWNER, Membership.Role.ADMIN}:
        raise PermissionDenied("Only an organisation owner or administrator may manage disbursements.")
    return membership


def configuration_for_organisation(*, organisation) -> OrganisationDisbursementConfiguration:
    config, _ = OrganisationDisbursementConfiguration.objects.get_or_create(organisation=organisation)
    return config


@transaction.atomic
def set_disbursement_provider(
    *, actor, organisation, provider_key: str, stripe_account_id: str = ""
) -> OrganisationDisbursementConfiguration:
    _require_manager(actor=actor, organisation=organisation)
    config = OrganisationDisbursementConfiguration.objects.select_for_update().get_or_create(
        organisation=organisation
    )[0]
    previous = config.provider_key
    config.provider_key = provider_key
    config.stripe_account_id = stripe_account_id
    config.full_clean(validate_unique=False, validate_constraints=False)
    config.save()
    record_event(
        action="disbursement_configuration.provider_changed",
        object_type="disbursements.OrganisationDisbursementConfiguration",
        object_id=str(config.id),
        actor=actor,
        organisation=organisation,
        metadata={"previous_provider": previous, "new_provider": config.provider_key},
    )
    return config


@transaction.atomic
def set_disbursement_api_key(*, actor, organisation, api_key: str) -> OrganisationDisbursementConfiguration:
    _require_manager(actor=actor, organisation=organisation)
    api_key = api_key.strip()
    if not api_key:
        raise DisbursementServiceError({"api_key": "Provide a non-empty API key."})
    config = OrganisationDisbursementConfiguration.objects.select_for_update().get_or_create(
        organisation=organisation
    )[0]
    had_key_before = config.api_key_is_set
    config.api_key_encrypted = encrypt_secret(api_key)
    config.save(update_fields=["api_key_encrypted", "updated_at"])
    record_event(
        action="disbursement_configuration.api_key_set",
        object_type="disbursements.OrganisationDisbursementConfiguration",
        object_id=str(config.id),
        actor=actor,
        organisation=organisation,
        metadata={"had_key_before": had_key_before, "key_last_4": api_key[-4:] if len(api_key) >= 4 else "****"},
    )
    return config


@transaction.atomic
def clear_disbursement_api_key(*, actor, organisation) -> OrganisationDisbursementConfiguration:
    _require_manager(actor=actor, organisation=organisation)
    config = OrganisationDisbursementConfiguration.objects.select_for_update().get_or_create(
        organisation=organisation
    )[0]
    config.api_key_encrypted = ""
    if config.provider_key != OrganisationDisbursementConfiguration.ProviderKey.MANUAL:
        config.provider_key = OrganisationDisbursementConfiguration.ProviderKey.MANUAL
    config.save(update_fields=["api_key_encrypted", "provider_key", "updated_at"])
    record_event(
        action="disbursement_configuration.api_key_cleared",
        object_type="disbursements.OrganisationDisbursementConfiguration",
        object_id=str(config.id),
        actor=actor,
        organisation=organisation,
    )
    return config


def _decrypted_provider(config: OrganisationDisbursementConfiguration):
    from apps.platform_admin.crypto import decrypt_secret

    api_key = decrypt_secret(config.api_key_encrypted) if config.api_key_encrypted else ""
    return get_provider(provider_key=config.provider_key, api_key=api_key, account_id=config.stripe_account_id)


def test_disbursement_connection(*, actor, organisation) -> dict[str, Any]:
    _require_manager(actor=actor, organisation=organisation)
    config = configuration_for_organisation(organisation=organisation)
    try:
        provider = _decrypted_provider(config)
        outcome = provider.test_connection()
        result = {"ok": outcome.ok, "detail": outcome.detail, "provider_key": provider.key, "provider_label": provider.label}
    except Exception as error:  # noqa: BLE001 - surface any failure as a diagnosable result
        result = {"ok": False, "detail": str(error), "provider_key": config.provider_key, "provider_label": ""}
    record_event(
        action="disbursement_configuration.connection_tested",
        object_type="disbursements.OrganisationDisbursementConfiguration",
        object_id=str(config.id),
        actor=actor,
        organisation=organisation,
        metadata={"ok": result["ok"]},
    )
    return result


@transaction.atomic
def issue_disbursement(*, actor, option, amount, note: str = "") -> Disbursement:
    """Pay out a funded application through the organisation's configured provider."""
    from apps.decision_options.models import DecisionOption

    organisation = option.organisation
    _require_manager(actor=actor, organisation=organisation)
    option = DecisionOption.objects.select_for_update().get(id=option.id)
    if option.outcome_status != DecisionOption.OutcomeStatus.FUNDED:
        raise DisbursementServiceError("Only a funded application can receive a disbursement.")

    config = configuration_for_organisation(organisation=organisation)
    provider = _decrypted_provider(config)
    outcome = provider.issue_payout(amount=amount, reference_hint=option.title)

    disbursement = Disbursement(
        organisation=organisation,
        option=option,
        amount=amount,
        provider_key=provider.key,
        status=outcome.status,
        external_reference=outcome.external_reference,
        note=note,
        issued_by=actor,
    )
    disbursement.full_clean(validate_unique=False, validate_constraints=False)
    disbursement.save()
    record_event(
        action="disbursement.issued",
        object_type="disbursements.Disbursement",
        object_id=str(disbursement.id),
        actor=actor,
        organisation=organisation,
        metadata={"option_id": str(option.id), "amount": str(amount), "provider": provider.key, "status": disbursement.status, "ok": outcome.ok},
    )
    return disbursement


def disbursements_for_option(*, option):
    return Disbursement.objects.filter(option=option).select_related("issued_by")
