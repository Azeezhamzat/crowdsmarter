"""Lookup configuration and organisation verification, audit-redacted like disbursements/AI provider settings."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.audit.services import record_event
from apps.organisations.models import Membership
from apps.platform_admin.crypto import decrypt_secret, encrypt_secret

from .models import OrganisationLookupConfiguration
from .providers.registry import get_provider


class OrgEnrichmentServiceError(ValidationError):
    pass


def _require_manager(*, actor, organisation) -> Membership:
    membership = organisation.memberships.filter(user=actor, status=Membership.Status.ACTIVE).first()
    if membership is None or membership.role not in {Membership.Role.OWNER, Membership.Role.ADMIN}:
        raise PermissionDenied("Only an organisation owner or administrator may manage organisation lookups.")
    return membership


def configuration_for_organisation(*, organisation) -> OrganisationLookupConfiguration:
    config, _ = OrganisationLookupConfiguration.objects.get_or_create(organisation=organisation)
    return config


@transaction.atomic
def set_lookup_provider(*, actor, organisation, provider_key: str) -> OrganisationLookupConfiguration:
    _require_manager(actor=actor, organisation=organisation)
    config = OrganisationLookupConfiguration.objects.select_for_update().get_or_create(organisation=organisation)[0]
    previous = config.provider_key
    config.provider_key = provider_key
    config.full_clean(validate_unique=False, validate_constraints=False)
    config.save()
    record_event(
        action="lookup_configuration.provider_changed",
        object_type="org_enrichment.OrganisationLookupConfiguration",
        object_id=str(config.id),
        actor=actor,
        organisation=organisation,
        metadata={"previous_provider": previous, "new_provider": config.provider_key},
    )
    return config


@transaction.atomic
def set_lookup_api_key(*, actor, organisation, api_key: str) -> OrganisationLookupConfiguration:
    _require_manager(actor=actor, organisation=organisation)
    api_key = api_key.strip()
    if not api_key:
        raise OrgEnrichmentServiceError({"api_key": "Provide a non-empty API key."})
    config = OrganisationLookupConfiguration.objects.select_for_update().get_or_create(organisation=organisation)[0]
    had_key_before = config.api_key_is_set
    config.api_key_encrypted = encrypt_secret(api_key)
    config.save(update_fields=["api_key_encrypted", "updated_at"])
    record_event(
        action="lookup_configuration.api_key_set",
        object_type="org_enrichment.OrganisationLookupConfiguration",
        object_id=str(config.id),
        actor=actor,
        organisation=organisation,
        metadata={"had_key_before": had_key_before, "key_last_4": api_key[-4:] if len(api_key) >= 4 else "****"},
    )
    return config


@transaction.atomic
def clear_lookup_api_key(*, actor, organisation) -> OrganisationLookupConfiguration:
    _require_manager(actor=actor, organisation=organisation)
    config = OrganisationLookupConfiguration.objects.select_for_update().get_or_create(organisation=organisation)[0]
    config.api_key_encrypted = ""
    if config.provider_key != OrganisationLookupConfiguration.ProviderKey.MANUAL:
        config.provider_key = OrganisationLookupConfiguration.ProviderKey.MANUAL
    config.save(update_fields=["api_key_encrypted", "provider_key", "updated_at"])
    record_event(
        action="lookup_configuration.api_key_cleared",
        object_type="org_enrichment.OrganisationLookupConfiguration",
        object_id=str(config.id),
        actor=actor,
        organisation=organisation,
    )
    return config


def _decrypted_provider(config: OrganisationLookupConfiguration):
    api_key = decrypt_secret(config.api_key_encrypted) if config.api_key_encrypted else ""
    return get_provider(provider_key=config.provider_key, api_key=api_key)


def test_lookup_connection(*, actor, organisation) -> dict[str, Any]:
    _require_manager(actor=actor, organisation=organisation)
    config = configuration_for_organisation(organisation=organisation)
    try:
        provider = _decrypted_provider(config)
        outcome = provider.test_connection()
        result = {"ok": outcome.ok, "detail": outcome.detail, "provider_key": provider.key, "provider_label": provider.label}
    except Exception as error:  # noqa: BLE001 - surface any failure as a diagnosable result
        result = {"ok": False, "detail": str(error), "provider_key": config.provider_key, "provider_label": ""}
    record_event(
        action="lookup_configuration.connection_tested",
        object_type="org_enrichment.OrganisationLookupConfiguration",
        object_id=str(config.id),
        actor=actor,
        organisation=organisation,
        metadata={"ok": result["ok"]},
    )
    return result


def lookup_organisation(*, actor, organisation, query: str) -> dict[str, Any]:
    """Look up an applicant organisation. Any active member may use this - it's a review aid, not an admin action."""
    membership = organisation.memberships.filter(user=actor, status=Membership.Status.ACTIVE).first()
    if membership is None:
        raise PermissionDenied("You are not an active member of this organisation.")
    query = query.strip()
    if not query:
        raise OrgEnrichmentServiceError({"query": "Enter an organisation name or registration number."})
    config = configuration_for_organisation(organisation=organisation)
    provider = _decrypted_provider(config)
    result = provider.lookup(query=query)
    record_event(
        action="lookup_configuration.organisation_looked_up",
        object_type="org_enrichment.OrganisationLookupConfiguration",
        object_id=str(config.id),
        actor=actor,
        organisation=organisation,
        metadata={"provider": provider.key, "found": result.found},
    )
    return result.as_dict()
