import pytest
from django.urls import reverse

from apps.organisations.models import Membership
from apps.participants.models import Participant


@pytest.mark.django_db
def test_contribution_api_is_tenant_safe_and_strict(api_client, decision_factory, user_factory):  # type: ignore[no-untyped-def]
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
        {
            "body": "The evidence is attributable and its limitations are explicit.",
            "references": "Study A",
        },
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


@pytest.mark.django_db
def test_facilitation_api_accepts_role_aware_participants(
    api_client, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status="open_for_contribution")
    observer = user_factory(email="session-observer@example.com")
    Membership.objects.create(
        organisation=decision.organisation,
        user=observer,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    Participant.objects.create(
        organisation=decision.organisation,
        decision=decision,
        user=observer,
        role=Participant.Role.OBSERVER,
        added_by=decision.owner,
    )

    api_client.force_authenticate(decision.owner)
    response = api_client.post(
        reverse("contributions:session-list-create", kwargs={"decision_id": decision.id}),
        {
            "title": "Decision framing workshop",
            "objective": "Agree the question, scope, and authority.",
            "agenda": "Test the framing and name unresolved concerns.",
            "participation_guidance": "Observers may listen and flag factual errors.",
            "participants": [{"user_id": str(observer.id), "role": "observer"}],
            "external_participants": [
                {
                    "external_label": "Telephone participant 1",
                    "stakeholder_group": "Local residents",
                    "role": "participant",
                }
            ],
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["participation_guidance"] == (
        "Observers may listen and flag factual errors."
    )
    assert len(response.json()["participants"]) == 2
    observer_record = next(item for item in response.json()["participants"] if item["user"])
    offline_record = next(item for item in response.json()["participants"] if not item["user"])
    assert observer_record["user"]["id"] == str(observer.id)
    assert observer_record["role"] == "observer"
    assert observer_record["role_label"] == "Observer"
    assert offline_record["display_label"] == "Telephone participant 1"
    assert offline_record["stakeholder_group"] == "Local residents"


@pytest.mark.django_db
def test_facilitation_run_of_show_enforces_one_live_item_and_links_outputs(
    api_client, decision_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status="open_for_contribution")
    api_client.force_authenticate(decision.owner)
    created = api_client.post(
        reverse("contributions:session-list-create", kwargs={"decision_id": decision.id}),
        {
            "title": "Decision criteria workshop",
            "objective": "Produce a reviewed set of decision criteria.",
            "accessibility_arrangements": "Offer a telephone channel and screen-reader-ready materials.",
            "consent_boundary": "Ask before attributing or quoting participant statements.",
            "agenda_items": [
                {
                    "title": "Frame the question",
                    "purpose": "Confirm the decision boundary.",
                    "method": "Silent reflection and round robin",
                    "facilitator_prompt": "What must this decision resolve?",
                    "output_prompt": "Record an agreed question or unresolved disagreement.",
                    "planned_minutes": 15,
                },
                {
                    "title": "Test the criteria",
                    "method": "Small-group review",
                    "planned_minutes": 25,
                },
            ],
        },
        format="json",
    )
    assert created.status_code == 201
    session_id = created.json()["id"]
    first, second = created.json()["agenda_items"]
    assert first["order"] == 1
    assert first["record_count"] == 0

    opened = api_client.post(
        reverse("contributions:session-status", kwargs={"session_id": session_id}),
        {"status": "open"},
        format="json",
    )
    assert opened.status_code == 200
    started = api_client.post(
        reverse("contributions:agenda-item-action", kwargs={"item_id": first["id"]}),
        {"action": "start"},
        format="json",
    )
    assert started.status_code == 200
    assert started.json()["status"] == "active"
    assert started.json()["started_at"] is not None

    conflicting = api_client.post(
        reverse("contributions:agenda-item-action", kwargs={"item_id": second["id"]}),
        {"action": "start"},
        format="json",
    )
    assert conflicting.status_code == 400

    linked_record = api_client.post(
        reverse("contributions:session-record-create", kwargs={"session_id": session_id}),
        {
            "agenda_item_id": first["id"],
            "kind": "agreement",
            "body": "The decision must resolve allocation within the approved budget.",
            "channel": "in_person",
            "origin": "facilitator_synthesis",
        },
        format="json",
    )
    assert linked_record.status_code == 201
    assert linked_record.json()["agenda_item_id"] == first["id"]

    completed = api_client.post(
        reverse("contributions:agenda-item-action", kwargs={"item_id": first["id"]}),
        {"action": "complete"},
        format="json",
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert completed.json()["actual_minutes"] is not None

    api_client.post(
        reverse("contributions:agenda-item-action", kwargs={"item_id": second["id"]}),
        {"action": "start"},
        format="json",
    )
    cannot_close = api_client.post(
        reverse("contributions:session-status", kwargs={"session_id": session_id}),
        {"status": "closed"},
        format="json",
    )
    assert cannot_close.status_code == 400
    premature_quality = api_client.put(
        reverse("contributions:session-quality-review", kwargs={"session_id": session_id}),
        {
            "inclusion_score": 3,
            "clarity_score": 3,
            "neutrality_score": 3,
            "participation_score": 3,
            "follow_through_score": 3,
            "what_worked": "The opening activity was clear.",
            "improve_next_time": "Complete the session before reviewing it.",
        },
        format="json",
    )
    assert premature_quality.status_code == 400
    skipped = api_client.post(
        reverse("contributions:agenda-item-action", kwargs={"item_id": second["id"]}),
        {"action": "skip"},
        format="json",
    )
    assert skipped.status_code == 200
    closed = api_client.post(
        reverse("contributions:session-status", kwargs={"session_id": session_id}),
        {"status": "closed"},
        format="json",
    )
    assert closed.status_code == 200
    quality = api_client.put(
        reverse("contributions:session-quality-review", kwargs={"session_id": session_id}),
        {
            "inclusion_score": 4,
            "clarity_score": 5,
            "neutrality_score": 4,
            "participation_score": 4,
            "follow_through_score": 3,
            "what_worked": "The influence boundary and round robin made participation concrete.",
            "improve_next_time": "Create follow-up owners before closing the final activity.",
            "unresolved_risks": "Telephone participants still had less time than the room.",
        },
        format="json",
    )
    assert quality.status_code == 200
    assert quality.json()["overall_score"] == 4.0
    listed = api_client.get(
        reverse("contributions:session-list-create", kwargs={"decision_id": decision.id})
    )
    assert listed.status_code == 200
    assert listed.json()[0]["agenda_items"][0]["record_count"] == 1
    assert listed.json()[0]["quality_review"]["overall_score"] == 4.0
    report = api_client.get(
        reverse("contributions:session-report", kwargs={"session_id": session_id}),
        HTTP_ACCEPT="text/html",
    )
    assert report.status_code == 200
    assert "Run of show" in report.content.decode("utf-8")
    assert "Frame the question" in report.content.decode("utf-8")
    assert "Overall quality 4.0/5" in report.content.decode("utf-8")
    assert "screen-reader-ready materials" in report.content.decode("utf-8")


@pytest.mark.django_db
def test_facilitation_record_response_and_report_protect_confidential_identity(
    api_client, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    from apps.contributions.services import create_session, update_session_status

    decision = decision_factory(status="open_for_contribution")
    contributor = user_factory(email="confidential-participant@example.com")
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
    session = create_session(
        actor=decision.owner,
        decision=decision,
        title="Confidential access workshop",
        objective="Understand access constraints.",
        participation_channels=["phone"],
        participants=[{"user_id": contributor.id, "role": "participant"}],
    )
    session = update_session_status(actor=decision.owner, session=session, status="open")
    session_participant = session.participants.get(user=contributor)

    api_client.force_authenticate(decision.owner)
    captured = api_client.post(
        reverse("contributions:session-record-create", kwargs={"session_id": session.id}),
        {
            "kind": "participant_statement",
            "body": "The evening channel creates a safety concern.",
            "channel": "phone",
            "origin": "participant_input",
            "attribution": "confidential",
            "source_participant_id": str(session_participant.id),
            "speaker_label": "Protected community representative",
        },
        format="json",
    )
    assert captured.status_code == 201
    assert captured.json()["speaker_label"] == "Protected community representative"

    draft = api_client.put(
        reverse("contributions:session-authority-response", kwargs={"session_id": session.id}),
        {
            "what_we_heard": "The evening channel creates a safety concern.",
            "what_changed": "A daytime callback route will be provided.",
            "next_steps": "Test the route next week.",
        },
        format="json",
    )
    assert draft.status_code == 200
    assert draft.json()["status"] == "draft"

    api_client.force_authenticate(contributor)
    visible = api_client.get(
        reverse("contributions:session-list-create", kwargs={"decision_id": decision.id})
    )
    assert visible.status_code == 200
    assert visible.json()[0]["authority_response"] is None
    assert visible.json()[0]["records"][0]["speaker_label"] == ""
    assert visible.json()[0]["records"][0]["source_participant"] is None
    forbidden_report = api_client.get(
        reverse("contributions:session-report", kwargs={"session_id": session.id})
    )
    assert forbidden_report.status_code == 403

    api_client.force_authenticate(decision.owner)
    update_session_status(actor=decision.owner, session=session, status="closed")
    published = api_client.put(
        reverse("contributions:session-authority-response", kwargs={"session_id": session.id}),
        {
            "what_we_heard": "The evening channel creates a safety concern.",
            "what_changed": "A daytime callback route will be provided.",
            "next_steps": "Test the route next week.",
            "publish": True,
        },
        format="json",
    )
    assert published.status_code == 200
    assert published.json()["status"] == "published"

    report = api_client.get(
        reverse("contributions:session-report", kwargs={"session_id": session.id}),
        HTTP_ACCEPT="text/html",
    )
    assert report.status_code == 200
    assert report["Content-Disposition"].endswith('-report.html"')
    report_text = report.content.decode("utf-8")
    assert "Confidential participant input" in report_text
    assert "Protected community representative" not in report_text
