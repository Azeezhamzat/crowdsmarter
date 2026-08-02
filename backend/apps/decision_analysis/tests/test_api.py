import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_analysis_api_is_strict_and_tenant_safe(
    api_client, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    api_client.force_authenticate(decision.owner)
    response = api_client.post(
        reverse("decision_analysis:issues", kwargs={"decision_id": decision.id}),
        {
            "issue_type": "missing_evidence",
            "title": "Missing cost evidence",
            "description": "No verified implementation cost is available.",
            "severity": "high",
            "owner_id": str(decision.owner_id),
            "automatic_option_rejection": True,
        },
        format="json",
    )
    assert response.status_code == 400
    assert "automatic_option_rejection" in response.json()

    api_client.force_authenticate(user_factory())
    hidden = api_client.get(
        reverse("decision_analysis:workspace", kwargs={"decision_id": decision.id})
    )
    assert hidden.status_code == 404


@pytest.mark.django_db
def test_workspace_explains_that_analysis_has_no_authority(
    api_client, decision_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    api_client.force_authenticate(decision.owner)
    response = api_client.get(
        reverse("decision_analysis:workspace", kwargs={"decision_id": decision.id})
    )
    assert response.status_code == 200
    assert "does not select an option" in response.json()["principle"]

@pytest.mark.django_db
def test_non_authority_cannot_read_synthesis_drafts_or_edit_another_owners_issue(
    api_client, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    from apps.decision_analysis.services import (
        create_executive_summary,
        create_issue,
        create_quality_review,
    )
    from apps.organisations.models import Membership
    from apps.participants.models import Participant

    decision = decision_factory()
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
    create_quality_review(
        actor=decision.owner,
        decision=decision,
        judgement="not_ready",
        answers={},
    )
    create_executive_summary(
        actor=decision.owner,
        decision=decision,
        proposed_judgement="Draft judgement not yet approved.",
    )
    issue = create_issue(
        actor=contributor,
        decision=decision,
        owner_id=decision.owner_id,
        issue_type="missing_evidence",
        title="Missing implementation estimate",
        description="The accountable owner must resolve this gap.",
    )

    api_client.force_authenticate(contributor)
    reviews = api_client.get(
        reverse("decision_analysis:quality-reviews", kwargs={"decision_id": decision.id})
    )
    summaries = api_client.get(
        reverse("decision_analysis:executive-summaries", kwargs={"decision_id": decision.id})
    )
    workspace = api_client.get(
        reverse("decision_analysis:workspace", kwargs={"decision_id": decision.id})
    )
    forbidden_update = api_client.patch(
        reverse("decision_analysis:issue-detail", kwargs={"issue_id": issue.id}),
        {"status": "in_progress"},
        format="json",
    )

    assert reviews.status_code == 200
    assert reviews.json() == []
    assert summaries.status_code == 200
    assert summaries.json() == []
    assert workspace.status_code == 200
    assert workspace.json()["quality_review"] is None
    assert workspace.json()["executive_summary"] is None
    assert forbidden_update.status_code == 403
