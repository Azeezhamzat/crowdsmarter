import pytest
from django.urls import reverse


def test_request_id_is_returned_and_untrusted_values_are_replaced(client):  # type: ignore[no-untyped-def]
    accepted = client.get(reverse("health-live"), HTTP_X_REQUEST_ID="edge-req_123")
    assert accepted.headers["X-Request-ID"] == "edge-req_123"

    replaced = client.get(reverse("health-live"), HTTP_X_REQUEST_ID="unsafe request id")
    generated = replaced.headers["X-Request-ID"]
    assert generated != "unsafe request id"
    assert len(generated) == 32


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
    assert response.json()["cache"] == "up"


@pytest.mark.django_db
def test_metrics_endpoint_exposes_bounded_request_metrics(api_client):  # type: ignore[no-untyped-def]
    api_client.get(reverse("health-live"))
    response = api_client.get(reverse("health-metrics"))

    assert response.status_code == 200
    body = response.content.decode()
    assert "crowdsmarter_http_requests_total" in body
    assert 'route="health-live"' in body
    assert "?" not in body
