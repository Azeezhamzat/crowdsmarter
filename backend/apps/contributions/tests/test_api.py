import pytest
from django.urls import reverse

from apps.organisations.models import Membership
from apps.participants.models import Participant


@pytest.mark.django_db
def test_contribution_api_is_tenant_safe_and_strict(
    api_client, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status="open_for_contribution")
    contributor = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    Participant.objects.create(
        organisation=decision.organisation,
        decision=decision,
        user=contributor,
        role=Participant.Role.CONTRIBUTOR,
        added_by=decision.owner,
    )
    api_client.force_authenticate(decision.owner)
    invalid = api_client.post(
        reverse("contributions:request-list-create", kwargs={"decision_id": decision.id}),
        {
            "assignee_id": str(contributor.id),
            "kind": "evidence",
            "title": "Collect evidence",
            "instructions": "Find a current attributable source.",
            "automatic_decision": True,
        },
        format="json",
    )
    assert invalid.status_code == 400
    assert "automatic_decision" in invalid.json()

    created = api_client.post(
        reverse("contributions:request-list-create", kwargs={"decision_id": decision.id}),
        {
            "assignee_id": str(contributor.id),
            "kind": "evidence",
            "title": "Collect evidence",
            "instructions": "Find a current attributable source.",
        },
        format="json",
    )
    assert created.status_code == 201
    request_id = created.json()["id"]

    api_client.force_authenticate(contributor)
    submitted = api_client.post(
        reverse("contributions:request-submit", kwargs={"request_id": request_id}),
        {"body": "The evidence is attributable and its limitations are explicit.", "references": "Study A"},
        format="json",
    )
    assert submitted.status_code == 201

    outsider = user_factory()
    api_client.force_authenticate(outsider)
    hidden = api_client.get(
        reverse("contributions:request-detail", kwargs={"request_id": request_id})
    )
    assert hidden.status_code == 404


@pytest.mark.django_db
def test_personal_contribution_work_only_returns_callers_assignments(
    api_client, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    from apps.contributions.services import create_request

    decision = decision_factory(status="open_for_contribution")
    contributor = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    Participant.objects.create(
        organisation=decision.organisation,
        decision=decision,
        user=contributor,
        role=Participant.Role.CONTRIBUTOR,
        added_by=decision.owner,
    )
    create_request(
        actor=decision.owner,
        decision=decision,
        assignee_id=contributor.id,
        reviewer_id=None,
        kind="risk",
        title="Validate risk ownership",
        instructions="Confirm ownership and mitigation timing.",
    )
    api_client.force_authenticate(contributor)
    response = api_client.get(reverse("contributions:my-work"))
    assert response.status_code == 200
    assert response.json()["summary"]["total"] == 1
    assert response.json()["requests"][0]["assignee"]["id"] == str(contributor.id)


@pytest.mark.django_db
def test_personal_work_includes_explicit_pending_reviews(
    api_client, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    from apps.contributions.services import create_request, submit_request

    decision = decision_factory(status="open_for_contribution")
    contributor = user_factory(email="contributor-review-work@example.com")
    reviewer = user_factory(email="named-reviewer@example.com")
    for user in [contributor, reviewer]:
        Membership.objects.create(
            organisation=decision.organisation,
            user=user,
            role=Membership.Role.CONTRIBUTOR,
            status=Membership.Status.ACTIVE,
        )
    Participant.objects.create(
        organisation=decision.organisation,
        decision=decision,
        user=contributor,
        role=Participant.Role.CONTRIBUTOR,
        added_by=decision.owner,
    )
    Participant.objects.create(
        organisation=decision.organisation,
        decision=decision,
        user=reviewer,
        role=Participant.Role.REVIEWER,
        added_by=decision.owner,
    )
    request = create_request(
        actor=decision.owner,
        decision=decision,
        assignee_id=contributor.id,
        reviewer_id=reviewer.id,
        kind="review",
        title="Review the implementation boundary",
        instructions="Confirm that the contribution remains within the approved scope.",
    )
    submit_request(
        actor=contributor,
        request=request,
        body="The implementation boundary is explicit and traceable.",
    )

    api_client.force_authenticate(reviewer)
    response = api_client.get(reverse("contributions:my-work"))

    assert response.status_code == 200
    assert response.json()["summary"]["awaiting_review"] == 1
    assert response.json()["requests"][0]["can_review"] is True


@pytest.mark.django_db
def test_accountable_authority_can_update_open_assignment(
    api_client, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    from apps.contributions.services import create_request

    decision = decision_factory(status="open_for_contribution")
    first = user_factory(email="api-first@example.com")
    second = user_factory(email="api-second@example.com")
    for user in [first, second]:
        Membership.objects.create(
            organisation=decision.organisation,
            user=user,
            role=Membership.Role.CONTRIBUTOR,
            status=Membership.Status.ACTIVE,
        )
        Participant.objects.create(
            organisation=decision.organisation,
            decision=decision,
            user=user,
            role=Participant.Role.CONTRIBUTOR,
            added_by=decision.owner,
        )
    item = create_request(
        actor=decision.owner,
        decision=decision,
        assignee_id=first.id,
        reviewer_id=None,
        kind="risk",
        title="Confirm risk ownership",
        instructions="Confirm the accountable owner and mitigation deadline.",
    )
    api_client.force_authenticate(decision.owner)
    response = api_client.patch(
        reverse("contributions:request-detail", kwargs={"request_id": item.id}),
        {"assignee_id": str(second.id), "priority": "critical"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["assignee"]["id"] == str(second.id)
    assert response.json()["priority"] == "critical"
