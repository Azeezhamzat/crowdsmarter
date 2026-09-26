from __future__ import annotations

import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from apps.org_enrichment import services
from apps.org_enrichment.models import OrganisationLookupConfiguration
from apps.organisations.models import Membership


@pytest.mark.django_db
def test_set_lookup_provider_requires_manager(organisation_factory, user_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    viewer = user_factory(email="viewer@example.com")
    Membership.objects.create(
        organisation=organisation,
        user=viewer,
        role=Membership.Role.VIEWER,
        status=Membership.Status.ACTIVE,
    )

    with pytest.raises(PermissionDenied):
        services.set_lookup_provider(actor=viewer, organisation=organisation, provider_key="manual")

    config = services.set_lookup_provider(
        actor=owner, organisation=organisation, provider_key="manual"
    )
    assert config.provider_key == "manual"


@pytest.mark.django_db
def test_candid_requires_api_key_before_selection(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    with pytest.raises(ValidationError):
        services.set_lookup_provider(actor=owner, organisation=organisation, provider_key="candid")

    services.set_lookup_api_key(actor=owner, organisation=organisation, api_key="key123")
    services.set_lookup_provider(actor=owner, organisation=organisation, provider_key="candid")
    config = OrganisationLookupConfiguration.objects.get(organisation=organisation)
    assert config.provider_key == "candid"
    assert config.api_key_is_set is True


@pytest.mark.django_db
def test_clear_api_key_reverts_to_manual(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    services.set_lookup_api_key(actor=owner, organisation=organisation, api_key="key123")
    services.set_lookup_provider(actor=owner, organisation=organisation, provider_key="candid")
    config = services.clear_lookup_api_key(actor=owner, organisation=organisation)
    assert config.provider_key == "manual"
    assert config.api_key_is_set is False


@pytest.mark.django_db
def test_lookup_organisation_available_to_any_active_member(organisation_factory, user_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    contributor = user_factory(email="contributor@example.com")
    Membership.objects.create(
        organisation=organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    outsider = user_factory(email="outsider@example.com")

    result = services.lookup_organisation(
        actor=contributor, organisation=organisation, query="Water for All"
    )
    assert result["ok"] is True
    assert result["found"] is False

    with pytest.raises(PermissionDenied):
        services.lookup_organisation(
            actor=outsider, organisation=organisation, query="Water for All"
        )

    with pytest.raises(ValidationError):
        services.lookup_organisation(actor=owner, organisation=organisation, query="   ")


@pytest.mark.django_db
def test_test_lookup_connection_reports_manual_ok(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    result = services.test_lookup_connection(actor=owner, organisation=organisation)
    assert result["ok"] is True
    assert result["provider_key"] == "manual"
