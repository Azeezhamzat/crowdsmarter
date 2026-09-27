"""Disbursement configuration and payout issuance, audit-redacted like the AI provider settings."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Sum

from apps.audit.services import record_event
from apps.organisations.models import Membership
from apps.platform_admin.crypto import encrypt_secret

from .models import Disbursement, OrganisationDisbursementConfiguration
from .providers.registry import get_provider


class DisbursementServiceError(ValidationError):
    pass


def _require_manager(*, actor, organisation) -> Membership:
    membership = organisation.memberships.filter(
        user=actor, status=Membership.Status.ACTIVE
    ).first()
    if membership is None or membership.role not in {Membership.Role.OWNER, Membership.Role.ADMIN}:
        raise PermissionDenied(
            "Only an organisation owner or administrator may manage disbursements."
        )
    return membership


def configuration_for_organisation(*, organisation) -> OrganisationDisbursementConfiguration:
    config, _ = OrganisationDisbursementConfiguration.objects.get_or_create(
        organisation=organisation
    )
    return config


def _require_no_pending_disbursements(*, organisation) -> None:
    if Disbursement.objects.filter(
        organisation=organisation,
        status=Disbursement.Status.PENDING,
    ).exists():
        raise DisbursementServiceError(
            "Finish or reconcile pending disbursements before changing payout credentials."
        )


@transaction.atomic
def set_disbursement_provider(
    *,
    actor,
    organisation,
    provider_key: str,
    stripe_account_id: str = "",
    currency: str | None = None,
) -> OrganisationDisbursementConfiguration:
    _require_manager(actor=actor, organisation=organisation)
    config = OrganisationDisbursementConfiguration.objects.select_for_update().get_or_create(
        organisation=organisation
    )[0]
    _require_no_pending_disbursements(organisation=organisation)
    previous = config.provider_key
    config.provider_key = provider_key
    config.stripe_account_id = stripe_account_id
    if currency is not None:
        config.currency = currency
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
def set_disbursement_api_key(
    *, actor, organisation, api_key: str
) -> OrganisationDisbursementConfiguration:
    _require_manager(actor=actor, organisation=organisation)
    api_key = api_key.strip()
    if not api_key:
        raise DisbursementServiceError({"api_key": "Provide a non-empty API key."})
    config = OrganisationDisbursementConfiguration.objects.select_for_update().get_or_create(
        organisation=organisation
    )[0]
    _require_no_pending_disbursements(organisation=organisation)
    had_key_before = config.api_key_is_set
    config.api_key_encrypted = encrypt_secret(api_key)
    config.save(update_fields=["api_key_encrypted", "updated_at"])
    record_event(
        action="disbursement_configuration.api_key_set",
        object_type="disbursements.OrganisationDisbursementConfiguration",
        object_id=str(config.id),
        actor=actor,
        organisation=organisation,
        metadata={
            "had_key_before": had_key_before,
            "key_last_4": api_key[-4:] if len(api_key) >= 4 else "****",
        },
    )
    return config


@transaction.atomic
def clear_disbursement_api_key(*, actor, organisation) -> OrganisationDisbursementConfiguration:
    _require_manager(actor=actor, organisation=organisation)
    config = OrganisationDisbursementConfiguration.objects.select_for_update().get_or_create(
        organisation=organisation
    )[0]
    _require_no_pending_disbursements(organisation=organisation)
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
    return get_provider(
        provider_key=config.provider_key, api_key=api_key, account_id=config.stripe_account_id
    )


def test_disbursement_connection(*, actor, organisation) -> dict[str, Any]:
    _require_manager(actor=actor, organisation=organisation)
    config = configuration_for_organisation(organisation=organisation)
    try:
        provider = _decrypted_provider(config)
        outcome = provider.test_connection()
        result = {
            "ok": outcome.ok,
            "detail": outcome.detail,
            "provider_key": provider.key,
            "provider_label": provider.label,
        }
    except Exception as error:  # noqa: BLE001 - surface any failure as a diagnosable result
        result = {
            "ok": False,
            "detail": str(error),
            "provider_key": config.provider_key,
            "provider_label": "",
        }
    record_event(
        action="disbursement_configuration.connection_tested",
        object_type="disbursements.OrganisationDisbursementConfiguration",
        object_id=str(config.id),
        actor=actor,
        organisation=organisation,
        metadata={"ok": result["ok"]},
    )
    return result


def _reserve_disbursement(
    *,
    actor,
    option,
    amount: Decimal,
    note: str,
    idempotency_key: uuid.UUID,
) -> Disbursement:
    """Commit a payout reservation before any external provider is called."""
    from apps.decision_options.models import DecisionOption

    organisation = option.organisation
    _require_manager(actor=actor, organisation=organisation)
    with transaction.atomic():
        option = DecisionOption.objects.select_for_update().get(id=option.id)
        existing = Disbursement.objects.filter(idempotency_key=idempotency_key).first()
        if existing is not None:
            if (
                existing.organisation_id != organisation.id
                or existing.option_id != option.id
                or existing.amount != amount
            ):
                raise DisbursementServiceError(
                    "That idempotency key was already used for a different disbursement."
                )
            return existing
        if option.outcome_status != DecisionOption.OutcomeStatus.FUNDED:
            raise DisbursementServiceError("Only a funded application can receive a disbursement.")
        if amount <= 0:
            raise DisbursementServiceError({"amount": "The amount must be greater than zero."})
        if option.awarded_amount is None:
            raise DisbursementServiceError("The funded application has no awarded amount.")

        reserved_total = Disbursement.objects.filter(
            option=option,
            status__in=[Disbursement.Status.PENDING, Disbursement.Status.PAID],
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        if reserved_total + amount > option.awarded_amount:
            remaining = option.awarded_amount - reserved_total
            raise DisbursementServiceError(
                {"amount": f"This exceeds the undisbursed award balance of {remaining:.2f}."}
            )

        config = OrganisationDisbursementConfiguration.objects.select_for_update().get_or_create(
            organisation=organisation
        )[0]
        disbursement = Disbursement(
            organisation=organisation,
            option=option,
            amount=amount,
            currency=config.currency,
            provider_key=config.provider_key,
            status=Disbursement.Status.PENDING,
            idempotency_key=idempotency_key,
            note=note,
            issued_by=actor,
        )
        disbursement.full_clean(validate_unique=False, validate_constraints=False)
        disbursement.save()
        record_event(
            action="disbursement.requested",
            object_type="disbursements.Disbursement",
            object_id=str(disbursement.id),
            actor=actor,
            organisation=organisation,
            metadata={
                "option_id": str(option.id),
                "amount": str(amount),
                "currency": disbursement.currency,
                "provider": disbursement.provider_key,
            },
        )
        return disbursement


def _execute_reserved_disbursement(*, disbursement: Disbursement) -> Disbursement:
    """Execute a committed reservation; provider retries reuse the same stable key."""
    if disbursement.status != Disbursement.Status.PENDING:
        return disbursement

    config = configuration_for_organisation(organisation=disbursement.organisation)
    if config.provider_key != disbursement.provider_key:
        raise DisbursementServiceError(
            "The payout provider changed while this disbursement was pending; reconcile it first."
        )
    try:
        provider = _decrypted_provider(config)
        outcome = provider.issue_payout(
            amount=disbursement.amount,
            currency=disbursement.currency,
            idempotency_key=str(disbursement.idempotency_key),
            reference_hint=disbursement.option.title,
        )
    except Exception as error:  # noqa: BLE001 - persist a safe failure instead of losing the ledger
        from .providers.base import DisbursementResult

        outcome = DisbursementResult(
            ok=False,
            status=Disbursement.Status.FAILED,
            external_reference="",
            detail=f"The payout provider could not be called: {error}",
        )

    with transaction.atomic():
        locked = Disbursement.objects.select_for_update().get(id=disbursement.id)
        if locked.status != Disbursement.Status.PENDING:
            return locked
        locked.status = Disbursement.Status.PAID if outcome.ok else Disbursement.Status.FAILED
        locked.external_reference = outcome.external_reference
        locked.provider_detail = outcome.detail
        locked.save(
            update_fields=[
                "status",
                "external_reference",
                "provider_detail",
                "updated_at",
            ]
        )
        record_event(
            action="disbursement.issued",
            object_type="disbursements.Disbursement",
            object_id=str(locked.id),
            actor=locked.issued_by,
            organisation=locked.organisation,
            metadata={
                "option_id": str(locked.option_id),
                "amount": str(locked.amount),
                "currency": locked.currency,
                "provider": locked.provider_key,
                "status": locked.status,
                "ok": outcome.ok,
            },
        )
        return locked


def issue_disbursement(
    *,
    actor,
    option,
    amount: Decimal,
    idempotency_key: uuid.UUID,
    note: str = "",
) -> Disbursement:
    """Reserve, execute, and persist an idempotent funded-application payout."""
    disbursement = _reserve_disbursement(
        actor=actor,
        option=option,
        amount=amount,
        note=note,
        idempotency_key=idempotency_key,
    )
    return _execute_reserved_disbursement(disbursement=disbursement)


def disbursements_for_option(*, option):
    return Disbursement.objects.filter(option=option).select_related("issued_by")
