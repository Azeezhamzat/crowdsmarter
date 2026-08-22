from __future__ import annotations

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_lookup_configuration_and_lookup_flow(api_client, organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    api_client.force_authenticate(owner)

    config = api_client.get(reverse("org_enrichment:configuration", kwargs={"organisation_id": organisation.id}))
    assert config.status_code == 200
    assert config.json()["provider_key"] == "manual"

    lookup = api_client.post(
        reverse("org_enrichment:lookup", kwargs={"organisation_id": organisation.id}),
        {"query": "Water for All"},
        format="json",
    )
    assert lookup.status_code == 200
    assert lookup.json()["found"] is False


@pytest.mark.django_db
def test_lookup_configuration_requires_membership(api_client, organisation_factory, user_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    api_client.force_authenticate(user_factory())
    response = api_client.get(reverse("org_enrichment:configuration", kwargs={"organisation_id": organisation.id}))
    assert response.status_code == 404
