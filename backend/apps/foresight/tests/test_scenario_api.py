import pytest
from django.urls import reverse

from apps.foresight.mapping_services import create_canvas, create_driver


@pytest.mark.django_db
def test_scenario_api_builds_workspace_and_rejects_unknown_fields(
    api_client, organisation_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    actor = organisation.created_by
    api_client.force_authenticate(actor)
    canvas = create_canvas(
        actor=actor,
        organisation=organisation,
        title="API scenario canvas",
        focal_question="What futures should be tested?",
        scope="A bounded API test system.",
        horizon_year=2040,
    )
    first = create_driver(
        actor=actor,
        canvas=canvas,
        title="Access uncertainty",
        description="Access could broaden or contract.",
        driver_type="critical_uncertainty",
        steep_category="economic",
        impact=5,
        uncertainty=5,
    )
    second = create_driver(
        actor=actor,
        canvas=canvas,
        title="Trust uncertainty",
        description="Trust could strengthen or erode.",
        driver_type="critical_uncertainty",
        steep_category="social",
        impact=5,
        uncertainty=5,
    )
    response = api_client.post(
        reverse("foresight:canvas-scenario-sets", kwargs={"canvas_id": canvas.id}),
        {
            "title": "API scenario set",
            "purpose": "Exercise the scenario API.",
            "axis_x_driver_id": str(first.id),
            "axis_x_low_label": "Restricted access",
            "axis_x_high_label": "Open access",
            "axis_y_driver_id": str(second.id),
            "axis_y_low_label": "Low trust",
            "axis_y_high_label": "High trust",
            "status": "active",
        },
        format="json",
    )
    assert response.status_code == 201
    scenario_set_id = response.json()["id"]

    world = api_client.post(
        reverse(
            "foresight:scenario-set-scenarios",
            kwargs={"scenario_set_id": scenario_set_id},
        ),
        {
            "title": "Open trusted networks",
            "code": "OT",
            "axis_x_position": "high",
            "axis_y_position": "high",
            "headline": "Access and trust reinforce participation.",
            "narrative": "A broad network of trusted participants coordinates effectively.",
            "key_assumptions": "Institutions remain transparent and interoperable.",
        },
        format="json",
    )
    assert world.status_code == 201

    workspace = api_client.get(
        reverse(
            "foresight:scenario-set-detail",
            kwargs={"scenario_set_id": scenario_set_id},
        )
    )
    assert workspace.status_code == 200
    assert workspace.json()["summary"]["scenario_count"] == 1
    assert workspace.json()["scenarios"][0]["review_summary"]["review_count"] == 0

    strict = api_client.post(
        reverse(
            "foresight:scenario-reviews",
            kwargs={"scenario_id": world.json()["id"]},
        ),
        {
            "plausibility": 4,
            "internal_consistency": 4,
            "distinctiveness": 4,
            "usefulness": 4,
            "confidence": 4,
            "silent_consensus": True,
        },
        format="json",
    )
    assert strict.status_code == 400
    assert "silent_consensus" in strict.json()


@pytest.mark.django_db
def test_scenario_workspace_is_tenant_isolated(
    api_client, user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    api_client.force_authenticate(user_factory())
    response = api_client.get(
        reverse(
            "foresight:canvas-scenario-sets",
            kwargs={"canvas_id": organisation.id},
        )
    )
    assert response.status_code == 404
