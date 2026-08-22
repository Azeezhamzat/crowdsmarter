from __future__ import annotations

from decimal import Decimal

import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from apps.decision_options.services import create_option, set_outcome
from apps.disbursements import services
from apps.disbursements.models import Disbursement, OrganisationDisbursementConfiguration
from apps.organisations.models import Membership


@pytest.mark.django_db
def test_set_disbursement_provider_requires_manager(organisation_factory, decision_factory, user_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    viewer = user_factory(email="viewer@example.com")
    Membership.objects.create(organisation=organisation, user=viewer, role=Membership.Role.VIEWER, status=Membership.Status.ACTIVE)

    with pytest.raises(PermissionDenied):
        services.set_disbursement_provider(actor=viewer, organisation=organisation, provider_key="manual")

    config = services.set_disbursement_provider(actor=owner, organisation=organisation, provider_key="manual")
    assert config.provider_key == "manual"


@pytest.mark.django_db
def test_stripe_requires_account_and_key_before_selection(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    with pytest.raises(ValidationError):
        services.set_disbursement_provider(actor=owner, organisation=organisation, provider_key="stripe")

    with pytest.raises(ValidationError):
        services.set_disbursement_provider(actor=owner, organisation=organisation, provider_key="stripe", stripe_account_id="acct_1")

    services.set_disbursement_api_key(actor=owner, organisation=organisation, api_key="sk_test_abcd")
    services.set_disbursement_provider(actor=owner, organisation=organisation, provider_key="stripe", stripe_account_id="acct_1")
    config = OrganisationDisbursementConfiguration.objects.get(organisation=organisation)
    assert config.provider_key == "stripe"
    assert config.api_key_is_set is True


@pytest.mark.django_db
def test_clear_api_key_reverts_to_manual(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    services.set_disbursement_api_key(actor=owner, organisation=organisation, api_key="sk_test_abcd")
    services.set_disbursement_provider(actor=owner, organisation=organisation, provider_key="stripe", stripe_account_id="acct_1")
    config = services.clear_disbursement_api_key(actor=owner, organisation=organisation)
    assert config.provider_key == "manual"
    assert config.api_key_is_set is False


@pytest.mark.django_db
def test_issue_disbursement_requires_funded_outcome(organisation_factory, decision_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner, title="Grant round")
    option = create_option(actor=owner, decision=decision, title="Water project", description="d")

    with pytest.raises(ValidationError):
        services.issue_disbursement(actor=owner, option=option, amount=Decimal("500.00"))

    set_outcome(actor=owner, option=option, outcome_status="funded", awarded_amount=Decimal("500.00"), outcome_note="")
    option.refresh_from_db()
    disbursement = services.issue_disbursement(actor=owner, option=option, amount=Decimal("500.00"), note="First tranche")
    assert disbursement.status == "paid"
    assert disbursement.provider_key == "manual"
    assert Disbursement.objects.filter(option=option).count() == 1

    listed = list(services.disbursements_for_option(option=option))
    assert listed[0].id == disbursement.id


@pytest.mark.django_db
def test_test_disbursement_connection_reports_manual_ok(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    result = services.test_disbursement_connection(actor=owner, organisation=organisation)
    assert result["ok"] is True
    assert result["provider_key"] == "manual"
