import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_liveness_endpoint_is_public(api_client):  # type: ignore[no-untyped-def]
    response = api_client.get(reverse("health-live"))
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_readiness_checks_required_database(api_client):  # type: ignore[no-untyped-def]
    response = api_client.get(reverse("health-ready"))
    assert response.status_code == 200
    assert response.json()["database"] == "up"
