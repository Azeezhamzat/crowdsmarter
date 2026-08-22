from __future__ import annotations

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_disbursement_configuration_and_issue_flow(api_client, organisation_factory, decision_factory):  # type: ignore[no-untyped-def]
    from apps.decision_options.services import create_option, set_outcome

    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner, title="Grant round")
    option = create_option(actor=owner, decision=decision, title="Water project", description="d")
    set_outcome(actor=owner, option=option, outcome_status="funded", awarded_amount="500.00", outcome_note="")

    api_client.force_authenticate(owner)

    config = api_client.get(reverse("disbursements:configuration", kwargs={"organisation_id": organisation.id}))
    assert config.status_code == 200
    assert config.json()["provider_key"] == "manual"

    issued = api_client.post(
        reverse("disbursements:option-disbursements", kwargs={"option_id": option.id}),
        {"amount": "500.00", "note": "First tranche"},
        format="json",
    )
    assert issued.status_code == 201
    assert issued.json()["status"] == "paid"

    listed = api_client.get(reverse("disbursements:option-disbursements", kwargs={"option_id": option.id}))
    assert listed.status_code == 200
    assert len(listed.json()) == 1


@pytest.mark.django_db
def test_disbursement_configuration_requires_membership(api_client, organisation_factory, user_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    api_client.force_authenticate(user_factory())
    response = api_client.get(reverse("disbursements:configuration", kwargs={"organisation_id": organisation.id}))
    assert response.status_code == 404
