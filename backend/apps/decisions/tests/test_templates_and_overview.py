import pytest
from django.urls import reverse

from apps.collaboration.models import DiscussionEntry
from apps.decision_options.models import DecisionOption
from apps.organisations.models import Membership
from apps.risks.models import Risk


@pytest.mark.django_db
def test_template_catalog_requires_authentication(api_client):  # type: ignore[no-untyped-def]
    response = api_client.get(reverse("decisions:template-list"))
    assert response.status_code in {401, 403}


@pytest.mark.django_db
def test_template_catalog_returns_versioned_human_prompts(
    api_client, user_factory
):  # type: ignore[no-untyped-def]
    user = user_factory()
    api_client.force_authenticate(user)

    response = api_client.get(reverse("decisions:template-list"))

    assert response.status_code == 200
    keys = {item["key"] for item in response.json()}
    assert {
        "blank", "technology_adoption", "pilot_experiment", "grant_round",
        "idea_competition", "anticipatory_commons",
    }.issubset(keys)
    grant_round = next(item for item in response.json() if item["key"] == "grant_round")
    assert grant_round["checklist"]
    technology = next(item for item in response.json() if item["key"] == "technology_adoption")
    assert technology["version"] == 1
    assert "Should" in technology["question_prompt"]
    commons = next(item for item in response.json() if item["key"] == "anticipatory_commons")
    assert commons["checklist"]
    assert "institution" in commons["best_for"]
    assert technology["checklist"]


@pytest.mark.django_db
def test_guided_creation_persists_explicit_framing_and_template_provenance(
    api_client, user_factory, organisation_factory, workspace_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    workspace = workspace_factory(organisation=organisation, created_by=owner)
    api_client.force_authenticate(owner)

    response = api_client.post(
        reverse("decisions:list-create", kwargs={"workspace_id": workspace.id}),
        {
            "template_key": "pilot_experiment",
            "title": "Run a field pilot",
            "decision_question": "Should we run a three-month controlled field pilot?",
            "purpose": "Reduce uncertainty before wider adoption.",
            "context": "Current performance under local conditions is unknown.",
            "scope": "Three farms for three months; no wider rollout.",
            "contribution_guidance": "Provide safety, usability, cost, and outcome evidence.",
            "urgency": "high",
            "target_decision_date": "2026-09-30",
        },
        format="json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["source_template_key"] == "pilot_experiment"
    assert body["source_template_version"] == 1
    assert body["purpose"] == "Reduce uncertainty before wider adoption."
    assert body["scope"] == "Three farms for three months; no wider rollout."
    assert body["status"] == "draft"


@pytest.mark.django_db
def test_guided_creation_rejects_unknown_template(
    api_client, user_factory, organisation_factory, workspace_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    workspace = workspace_factory(organisation=organisation, created_by=owner)
    api_client.force_authenticate(owner)

    response = api_client.post(
        reverse("decisions:list-create", kwargs={"workspace_id": workspace.id}),
        {"template_key": "automatic_decider", "title": "Bad template"},
        format="json",
    )

    assert response.status_code == 400
    assert "template_key" in response.json()


@pytest.mark.django_db
def test_decision_overview_is_tenant_isolated(
    api_client, user_factory, decision_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    outsider = user_factory()
    api_client.force_authenticate(outsider)

    response = api_client.get(reverse("decisions:overview", kwargs={"decision_id": decision.id}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_decision_overview_surfaces_next_action_people_options_and_risks(
    api_client, user_factory, decision_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory(
        decision_question="Should we pilot the system?",
        purpose="Reduce uncertainty.",
        context="The current process is slow.",
        scope="One bounded pilot.",
        contribution_guidance="Provide attributable evidence.",
    )
    contributor = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
    )
    from apps.participants.models import Participant

    Participant.objects.create(
        organisation=decision.organisation,
        decision=decision,
        user=contributor,
        role=Participant.Role.CONTRIBUTOR,
        added_by=decision.owner,
    )
    option = DecisionOption.objects.create(
        organisation=decision.organisation,
        decision=decision,
        title="Run a pilot",
        description="A bounded pilot.",
        proposed_by=decision.owner,
        created_by=decision.owner,
    )
    Risk.objects.create(
        organisation=decision.organisation,
        decision=decision,
        option=option,
        title="Operational disruption",
        description="The pilot could distract the field team.",
        likelihood=3,
        impact=4,
        response_strategy=Risk.ResponseStrategy.MITIGATE,
        mitigation_plan="Limit the pilot and monitor workload.",
        owner=contributor,
        created_by=decision.owner,
    )
    DiscussionEntry.objects.create(
        organisation=decision.organisation,
        decision=decision,
        author=contributor,
        kind=DiscussionEntry.Kind.CONCERN,
        body="How will workload be monitored?",
    )
    api_client.force_authenticate(decision.owner)

    response = api_client.get(reverse("decisions:overview", kwargs={"decision_id": decision.id}))

    assert response.status_code == 200
    body = response.json()
    assert body["next_action"]["label"] == "Move into framing"
    assert body["framing"] == {"completed": 5, "total": 5, "missing": []}
    assert body["participants"]["total"] == 2
    assert body["discussion"]["unresolved"] == 1
    assert body["options"][0]["title"] == "Run a pilot"
    assert body["material_risks"][0]["score"] == 12

@pytest.mark.django_db
def test_decision_overview_surfaces_linked_strategic_implication(
    api_client, decision_factory
):  # type: ignore[no-untyped-def]
    from apps.foresight.mapping_services import create_canvas, create_implication

    decision = decision_factory()
    canvas = create_canvas(
        actor=decision.owner,
        organisation=decision.organisation,
        title="Future operating environment",
        focal_question="How might the operating environment reshape this decision?",
        scope="The organisation, its partners, and the relevant external system.",
        horizon_year=2035,
    )
    implication = create_implication(
        actor=decision.owner,
        canvas=canvas,
        title="Build a reversible implementation path",
        description=(
            "The decision should preserve the ability to adapt if the external "
            "operating environment changes."
        ),
        implication_type="decision_requirement",
        priority=5,
        linked_decision_id=decision.id,
    )
    api_client.force_authenticate(decision.owner)

    response = api_client.get(
        reverse("decisions:overview", kwargs={"decision_id": decision.id})
    )

    assert response.status_code == 200
    assert response.json()["foresight_implications"] == [
        {
            "id": str(implication.id),
            "canvas_id": str(canvas.id),
            "canvas_title": canvas.title,
            "title": implication.title,
            "description": implication.description,
            "implication_type": implication.implication_type,
            "priority": 5,
            "status": "open",
            "owner": decision.owner.email,
        }
    ]
