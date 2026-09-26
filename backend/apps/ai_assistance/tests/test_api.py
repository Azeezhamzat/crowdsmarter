import pytest
from django.urls import reverse

from apps.ai_assistance.models import AIReview
from apps.audit.models import AuditEvent
from apps.decisions.models import Decision
from apps.notifications.models import Notification
from apps.organisations.models import Membership


@pytest.mark.django_db
def test_ai_review_is_attributable_reviewable_and_does_not_change_decision(
    api_client, decision_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory(
        status=Decision.Status.UNDER_REVIEW,
        title="AI-assisted monitoring pilot",
    )
    original_status = decision.status
    api_client.force_authenticate(decision.owner)
    url = reverse("ai_assistance:list-create", kwargs={"decision_id": decision.id})
    response = api_client.post(url, {}, format="json")
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert body["provider_key"] == "rules"
    assert body["output"]["missing_evidence"]

    decision.refresh_from_db()
    assert decision.status == original_status
    assert AuditEvent.objects.filter(action="ai_review.completed").exists()
    assert Notification.objects.filter(
        recipient=decision.owner,
        kind=Notification.Kind.AI_REVIEW,
    ).exists()

    detail_url = reverse("ai_assistance:detail", kwargs={"review_id": body["id"]})
    assert api_client.get(detail_url).status_code == 200

    acknowledge_url = reverse(
        "ai_assistance:acknowledge",
        kwargs={"review_id": body["id"]},
    )
    acknowledged = api_client.post(
        acknowledge_url,
        {"notes": "Reviewed as a prompt, not a decision."},
        format="json",
    )
    assert acknowledged.status_code == 200
    assert acknowledged.json()["is_reviewed"] is True
    assert (
        api_client.post(
            acknowledge_url,
            {"notes": "Attempted overwrite."},
            format="json",
        ).status_code
        == 400
    )


@pytest.mark.django_db
def test_viewer_cannot_request_ai_review(api_client, user_factory, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    viewer = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=viewer,
        role=Membership.Role.VIEWER,
        status=Membership.Status.ACTIVE,
    )
    api_client.force_authenticate(viewer)
    url = reverse("ai_assistance:list-create", kwargs={"decision_id": decision.id})
    assert api_client.get(url).status_code == 200
    assert api_client.post(url, {}, format="json").status_code == 403


@pytest.mark.django_db
def test_ai_review_is_tenant_isolated(api_client, user_factory, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    review = AIReview.objects.create(
        organisation=decision.organisation,
        decision=decision,
        requested_by=decision.owner,
        status=AIReview.Status.FAILED,
        provider_key="rules",
        provider_label="Rules",
        model_identifier="rules-v1",
        input_fingerprint="a" * 64,
        input_snapshot={},
        error_message="Expected test failure.",
    )
    api_client.force_authenticate(user_factory())
    detail = reverse("ai_assistance:detail", kwargs={"review_id": review.id})
    assert api_client.get(detail).status_code == 404


@pytest.mark.django_db
def test_completed_ai_review_can_be_dismissed_with_a_reason(api_client, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    api_client.force_authenticate(decision.owner)
    create_url = reverse("ai_assistance:list-create", kwargs={"decision_id": decision.id})
    created = api_client.post(create_url, {}, format="json")
    review_id = created.json()["id"]
    dismiss_url = reverse("ai_assistance:dismiss", kwargs={"review_id": review_id})
    response = api_client.post(
        dismiss_url,
        {"reason": "The rule does not apply to this context."},
        format="json",
    )
    assert response.status_code == 200
    review = AIReview.objects.get(id=review_id)
    assert review.dismissed_at is not None
    assert review.dismissal_reason
    assert (
        api_client.post(
            dismiss_url,
            {"reason": "Attempted overwrite."},
            format="json",
        ).status_code
        == 400
    )


@pytest.mark.django_db
def test_ai_review_request_rejects_unknown_input(api_client, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    api_client.force_authenticate(decision.owner)
    url = reverse("ai_assistance:list-create", kwargs={"decision_id": decision.id})
    assert api_client.post(url, {"provider": "hidden"}, format="json").status_code == 400


class FailingProvider:
    key = "failing-test-provider"
    label = "Failing test provider"
    model_identifier = "test-v1"

    def review_decision(self, *, snapshot):  # type: ignore[no-untyped-def]
        raise RuntimeError("provider-secret-should-not-be-returned")


@pytest.mark.django_db
def test_provider_failure_is_safe_and_does_not_change_the_decision(
    api_client, decision_factory, monkeypatch
):  # type: ignore[no-untyped-def]
    monkeypatch.setattr("apps.ai_assistance.services.get_provider", lambda: FailingProvider())
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    original_status = decision.status
    api_client.force_authenticate(decision.owner)

    url = reverse("ai_assistance:list-create", kwargs={"decision_id": decision.id})
    response = api_client.post(url, {}, format="json")

    assert response.status_code == 201
    assert response.json()["status"] == "failed"
    assert response.json()["error_message"] == (
        "The configured AI provider could not complete this review."
    )
    assert "provider-secret" not in str(response.json())
    decision.refresh_from_db()
    assert decision.status == original_status
    assert AuditEvent.objects.filter(action="ai_review.failed").exists()
