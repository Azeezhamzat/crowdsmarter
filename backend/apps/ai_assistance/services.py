"""Attributable AI review workflows with no record mutation."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.services import record_event
from apps.decisions.models import Decision
from apps.notifications.models import Notification
from apps.notifications.services import create_notification

from .models import AIReview
from .permissions import can_moderate_ai_review, can_request_ai_review
from .providers.base import AIProvider
from .providers.registry import get_provider
from .snapshots import build_decision_snapshot

logger = logging.getLogger(__name__)


class AIReviewServiceError(ValidationError):
    """Expected AI review workflow failure."""


def _json_default(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _fingerprint(snapshot: dict[str, Any]) -> str:
    """Hash the substantive decision content only.

    Excludes generated_at: it changes on every snapshot build, so including it
    would make the fingerprint change even when nothing about the decision
    record itself did, defeating its purpose as a reproducibility signal.
    """
    stable = {key: value for key, value in snapshot.items() if key != "generated_at"}
    encoded = json.dumps(
        stable,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def request_ai_review(*, actor: User, decision: Decision) -> AIReview:
    """Create and execute one advisory review using the configured provider."""
    if not can_request_ai_review(actor=actor, decision=decision):
        raise PermissionDenied("You cannot request AI assistance for this decision state.")
    decision = Decision.objects.select_related("organisation", "owner").get(id=decision.id)
    snapshot = build_decision_snapshot(decision=decision)
    try:
        provider = get_provider()
    except Exception as exc:  # noqa: BLE001 - configuration errors stay private
        logger.exception("Configured AI provider could not be loaded")
        raise AIReviewServiceError(
            "AI assistance is temporarily unavailable because its provider "
            "configuration is invalid."
        ) from exc
    review = AIReview.objects.create(
        organisation=decision.organisation,
        decision=decision,
        requested_by=actor,
        provider_key=provider.key,
        provider_label=provider.label,
        model_identifier=provider.model_identifier,
        input_fingerprint=_fingerprint(snapshot),
        input_snapshot=snapshot,
    )
    record_event(
        action="ai_review.requested",
        object_type="ai_review",
        object_id=str(review.id),
        actor=actor,
        organisation=decision.organisation,
        metadata={
            "decision_id": str(decision.id),
            "provider": provider.key,
            "input_fingerprint": review.input_fingerprint,
        },
    )
    return execute_ai_review(review=review, provider=provider)


def execute_ai_review(
    *, review: AIReview, provider: AIProvider | None = None
) -> AIReview:
    """Execute outside a long database transaction and preserve failures."""
    provider = provider or get_provider()
    with transaction.atomic():
        current = AIReview.objects.select_for_update().get(id=review.id)
        if current.status not in {AIReview.Status.PENDING, AIReview.Status.FAILED}:
            raise AIReviewServiceError("This AI review cannot be executed again.")
        current.status = AIReview.Status.RUNNING
        current.started_at = timezone.now()
        current.error_message = ""
        current.save(
            update_fields=["status", "started_at", "error_message", "updated_at"]
        )
    try:
        output = provider.review_decision(snapshot=current.input_snapshot).as_dict()
    except Exception:  # noqa: BLE001 - provider failure must degrade gracefully
        logger.exception(
            "Configured AI provider failed",
            extra={"ai_review_id": str(current.id), "provider": current.provider_key},
        )
        safe_message = "The configured AI provider could not complete this review."
        with transaction.atomic():
            failed = AIReview.objects.select_for_update().get(id=current.id)
            failed.status = AIReview.Status.FAILED
            failed.error_message = safe_message
            failed.completed_at = timezone.now()
            failed.save(
                update_fields=[
                    "status",
                    "error_message",
                    "completed_at",
                    "updated_at",
                ]
            )
        record_event(
            action="ai_review.failed",
            object_type="ai_review",
            object_id=str(failed.id),
            actor=failed.requested_by,
            organisation=failed.organisation,
            metadata={"decision_id": str(failed.decision_id), "error": safe_message},
        )
        return failed
    with transaction.atomic():
        completed = AIReview.objects.select_for_update().select_related(
            "requested_by", "organisation", "decision"
        ).get(id=current.id)
        completed.status = AIReview.Status.COMPLETED
        completed.output = output
        completed.completed_at = timezone.now()
        completed.error_message = ""
        completed.full_clean(validate_unique=False, validate_constraints=False)
        completed.save(
            update_fields=[
                "status",
                "output",
                "completed_at",
                "error_message",
                "updated_at",
            ]
        )
        create_notification(
            recipient=completed.requested_by,
            organisation=completed.organisation,
            decision=completed.decision,
            kind=Notification.Kind.AI_REVIEW,
            title="AI review ready",
            message=(
                f"The advisory review for “{completed.decision.title}” "
                "is ready for human review."
            ),
            url=f"/decisions/{completed.decision_id}/ai-review",
            dedup_key=f"ai-review-completed:{completed.id}",
        )
    record_event(
        action="ai_review.completed",
        object_type="ai_review",
        object_id=str(completed.id),
        actor=completed.requested_by,
        organisation=completed.organisation,
        metadata={
            "decision_id": str(completed.decision_id),
            "provider": completed.provider_key,
        },
    )
    return completed


@transaction.atomic
def mark_ai_review_reviewed(
    *, actor: User, review: AIReview, notes: str = ""
) -> AIReview:
    current = AIReview.objects.select_for_update().select_related(
        "decision__owner", "organisation"
    ).get(id=review.id)
    if not can_moderate_ai_review(actor=actor, review=current):
        raise PermissionDenied("You cannot review this AI output.")
    if current.status != AIReview.Status.COMPLETED:
        raise AIReviewServiceError("Only completed AI output can be marked reviewed.")
    if current.reviewed_at:
        raise AIReviewServiceError("This AI output has already been marked reviewed.")
    if current.dismissed_at:
        raise AIReviewServiceError("A dismissed AI review cannot be marked reviewed.")
    current.reviewed_by = actor
    current.reviewed_at = timezone.now()
    current.review_notes = notes.strip()
    current.save(
        update_fields=["reviewed_by", "reviewed_at", "review_notes", "updated_at"]
    )
    record_event(
        action="ai_review.reviewed",
        object_type="ai_review",
        object_id=str(current.id),
        actor=actor,
        organisation=current.organisation,
        metadata={"decision_id": str(current.decision_id)},
    )
    return current


@transaction.atomic
def dismiss_ai_review(*, actor: User, review: AIReview, reason: str) -> AIReview:
    current = AIReview.objects.select_for_update().select_related(
        "decision__owner", "organisation"
    ).get(id=review.id)
    if not can_moderate_ai_review(actor=actor, review=current):
        raise PermissionDenied("You cannot dismiss this AI output.")
    if current.status != AIReview.Status.COMPLETED:
        raise AIReviewServiceError("Only completed AI output can be dismissed.")
    if current.dismissed_at:
        raise AIReviewServiceError("This AI output has already been dismissed.")
    if not reason.strip():
        raise AIReviewServiceError({"reason": "Explain why this output is dismissed."})
    if current.reviewed_at:
        raise AIReviewServiceError("A reviewed AI output cannot be dismissed.")
    current.dismissed_by = actor
    current.dismissed_at = timezone.now()
    current.dismissal_reason = reason.strip()
    current.full_clean(validate_unique=False, validate_constraints=False)
    current.save(
        update_fields=[
            "dismissed_by",
            "dismissed_at",
            "dismissal_reason",
            "updated_at",
        ]
    )
    record_event(
        action="ai_review.dismissed",
        object_type="ai_review",
        object_id=str(current.id),
        actor=actor,
        organisation=current.organisation,
        metadata={
            "decision_id": str(current.decision_id),
            "reason": current.dismissal_reason,
        },
    )
    return current


def ai_review_quality_metrics(*, organisation) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    """Aggregate human disposition of completed AI reviews as an evaluation signal.

    A high dismissal rate suggests the advisory output isn't earning trust;
    this is the harness the roadmap calls "user correction rate," built
    entirely from the reviewed_at/dismissed_at fields humans already set.
    """
    completed = AIReview.objects.filter(
        organisation=organisation, status=AIReview.Status.COMPLETED
    )
    total_completed = completed.count()
    reviewed_count = completed.filter(reviewed_at__isnull=False).count()
    dismissed_count = completed.filter(dismissed_at__isnull=False).count()
    actioned_count = reviewed_count + dismissed_count
    correction_rate = (
        round(dismissed_count / actioned_count * 100, 2) if actioned_count else None
    )
    return {
        "total_completed": total_completed,
        "reviewed_count": reviewed_count,
        "dismissed_count": dismissed_count,
        "pending_disposition_count": total_completed - actioned_count,
        "correction_rate": correction_rate,
    }
