import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_canvas_api_creates_driver_and_returns_workspace(api_client, organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    api_client.force_authenticate(organisation.created_by)
    canvas_response = api_client.post(
        reverse("foresight:canvases", kwargs={"organisation_id": organisation.id}),
        {
            "title": "Future of field operations",
            "focal_question": "How might automation reshape field operations by 2035?",
            "scope": "Field labour, technology, regulation, and service providers.",
            "horizon_year": 2035,
            "status": "active",
        },
        format="json",
    )
    assert canvas_response.status_code == 201
    canvas_id = canvas_response.json()["id"]
    driver_response = api_client.post(
        reverse("foresight:canvas-drivers", kwargs={"canvas_id": canvas_id}),
        {
            "title": "Availability of affordable robotics",
            "description": "Hardware and service costs shape adoption beyond large farms.",
            "driver_type": "critical_uncertainty",
            "steep_category": "technological",
            "direction": "decreasing",
            "impact": 5,
            "uncertainty": 4,
        },
        format="json",
    )
    assert driver_response.status_code == 201

    workspace = api_client.get(reverse("foresight:canvas-detail", kwargs={"canvas_id": canvas_id}))
    assert workspace.status_code == 200
    loop_response = api_client.post(
        reverse("foresight:canvas-feedback-loops", kwargs={"canvas_id": canvas_id}),
        {
            "name": "Affordability adoption loop",
            "description": "Lower costs increase adoption and service scale.",
            "loop_type": "reinforcing",
            "driver_ids": [driver_response.json()["id"], driver_response.json()["id"]],
            "rationale": "This deliberately duplicates one driver and must be rejected.",
        },
        format="json",
    )
    assert loop_response.status_code == 400

    assert workspace.json()["summary"]["critical_uncertainty_count"] == 1
    assert workspace.json()["drivers"][0]["attention_score"] == 20


@pytest.mark.django_db
def test_canvas_api_rejects_unknown_fields(api_client, organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    api_client.force_authenticate(organisation.created_by)
    response = api_client.post(
        reverse("foresight:canvases", kwargs={"organisation_id": organisation.id}),
        {
            "title": "Strict contract",
            "focal_question": "What should be explored?",
            "scope": "A bounded system.",
            "horizon_year": 2035,
            "silent_ai_decision": True,
        },
        format="json",
    )
    assert response.status_code == 400
    assert "silent_ai_decision" in response.json()


@pytest.mark.django_db
def test_canvas_api_is_tenant_isolated(api_client, user_factory, organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    api_client.force_authenticate(user_factory())

    assert (
        api_client.get(
            reverse("foresight:canvases", kwargs={"organisation_id": organisation.id})
        ).status_code
        == 404
    )
