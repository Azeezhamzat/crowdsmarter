"""Transactional workflows for integrated decision analysis."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.services import record_event
from apps.decisions.models import Decision
from apps.organisations.models import Membership

from .models import DecisionIssue, DecisionQualityReview, ExecutiveDecisionSummary
from .policies import can_contribute_analysis, can_edit_issue, can_manage_analysis


class DecisionAnalysisServiceError(ValidationError):
    """Expected domain validation failure."""


def _active_member(*, decision: Decision, user_id: Any) -> User:
    try:
        return Membership.objects.select_related("user").get(
            organisation=decision.organisation,
            user_id=user_id,
            status=Membership.Status.ACTIVE,
        ).user
    except Membership.DoesNotExist as exc:
        raise DecisionAnalysisServiceError({"owner_id": "Choose an active organisation member."}) from exc


@transaction.atomic
def create_issue(*, actor: User, decision: Decision, owner_id: Any, **fields: Any) -> DecisionIssue:
    if not can_contribute_analysis(actor=actor, decision=decision):
        raise PermissionDenied("You cannot add analysis issues in this decision state.")
    issue = DecisionIssue(
        organisation=decision.organisation,
        decision=decision,
        owner=_active_member(decision=decision, user_id=owner_id),
        created_by=actor,
        **fields,
    )
    issue.full_clean(validate_unique=False, validate_constraints=False)
    issue.save()
    record_event(
        action="decision_analysis.issue_created",
        object_type="decision_analysis_issue",
        object_id=str(issue.id),
        actor=actor,
        organisation=decision.organisation,
        metadata={"decision_id": str(decision.id), "issue_type": issue.issue_type, "severity": issue.severity},
    )
    return issue


@transaction.atomic
def update_issue(*, actor: User, issue: DecisionIssue, fields: dict[str, Any]) -> DecisionIssue:
    issue = DecisionIssue.objects.select_for_update().select_related("decision__organisation").get(id=issue.id)
    if not can_edit_issue(actor=actor, issue=issue):
        raise PermissionDenied("Only the assigned owner or an accountable decision authority may update this issue.")
    if "owner_id" in fields:
        if not can_manage_analysis(actor=actor, decision=issue.decision):
            raise PermissionDenied("Only an accountable decision authority may transfer issue ownership.")
        issue.owner = _active_member(decision=issue.decision, user_id=fields.pop("owner_id"))
    requested_status = fields.pop("status", None)
    for name, value in fields.items():
        setattr(issue, name, value)
    if requested_status is not None:
        issue.status = requested_status
        if requested_status == DecisionIssue.Status.RESOLVED:
            issue.resolved_by = actor
            issue.resolved_at = timezone.now()
        else:
            issue.resolved_by = None
            issue.resolved_at = None
    issue.full_clean(validate_unique=False, validate_constraints=False)
    issue.save()
    record_event(
        action="decision_analysis.issue_updated",
        object_type="decision_analysis_issue",
        object_id=str(issue.id),
        actor=actor,
        organisation=issue.organisation,
        metadata={"decision_id": str(issue.decision_id), "status": issue.status},
    )
    return issue


@transaction.atomic
def create_quality_review(*, actor: User, decision: Decision, **fields: Any) -> DecisionQualityReview:
    decision = Decision.objects.select_for_update().select_related("organisation").get(id=decision.id)
    if not can_manage_analysis(actor=actor, decision=decision):
        raise PermissionDenied("Only accountable decision authorities may author a quality review.")
    if DecisionQualityReview.objects.filter(decision=decision, status=DecisionQualityReview.Status.DRAFT).exists():
        raise DecisionAnalysisServiceError("Complete or publish the existing draft review first.")
    version = (DecisionQualityReview.objects.filter(decision=decision).order_by("-version").values_list("version", flat=True).first() or 0) + 1
    review = DecisionQualityReview(
        organisation=decision.organisation,
        decision=decision,
        version=version,
        author=actor,
        **fields,
    )
    review.full_clean(validate_unique=False, validate_constraints=False)
    review.save()
    record_event(
        action="decision_analysis.quality_review_created",
        object_type="decision_quality_review",
        object_id=str(review.id),
        actor=actor,
        organisation=decision.organisation,
        metadata={"decision_id": str(decision.id), "version": version},
    )
    return review


@transaction.atomic
def update_quality_review(*, actor: User, review: DecisionQualityReview, fields: dict[str, Any]) -> DecisionQualityReview:
    review = DecisionQualityReview.objects.select_for_update().select_related("decision__organisation").get(id=review.id)
    if not can_manage_analysis(actor=actor, decision=review.decision):
        raise PermissionDenied("Only accountable decision authorities may update this review.")
    if review.status != DecisionQualityReview.Status.DRAFT:
        raise DecisionAnalysisServiceError("Published and superseded reviews are immutable.")
    requested_status = fields.pop("status", review.status)
    for name, value in fields.items():
        setattr(review, name, value)
    if requested_status == DecisionQualityReview.Status.PUBLISHED:
        DecisionQualityReview.objects.filter(
            decision=review.decision,
            status=DecisionQualityReview.Status.PUBLISHED,
        ).update(status=DecisionQualityReview.Status.SUPERSEDED)
        review.status = DecisionQualityReview.Status.PUBLISHED
        review.published_at = timezone.now()
    elif requested_status != DecisionQualityReview.Status.DRAFT:
        raise DecisionAnalysisServiceError({"status": "A draft may only be published."})
    review.full_clean(validate_unique=False, validate_constraints=False)
    review.save()
    record_event(
        action="decision_analysis.quality_review_updated",
        object_type="decision_quality_review",
        object_id=str(review.id),
        actor=actor,
        organisation=review.organisation,
        metadata={"decision_id": str(review.decision_id), "version": review.version, "status": review.status},
    )
    return review


@transaction.atomic
def create_executive_summary(*, actor: User, decision: Decision, **fields: Any) -> ExecutiveDecisionSummary:
    decision = Decision.objects.select_for_update().select_related("organisation").get(id=decision.id)
    if not can_manage_analysis(actor=actor, decision=decision):
        raise PermissionDenied("Only accountable decision authorities may author an executive summary.")
    if ExecutiveDecisionSummary.objects.filter(decision=decision, status=ExecutiveDecisionSummary.Status.DRAFT).exists():
        raise DecisionAnalysisServiceError("Complete or approve the existing draft summary first.")
    version = (ExecutiveDecisionSummary.objects.filter(decision=decision).order_by("-version").values_list("version", flat=True).first() or 0) + 1
    summary = ExecutiveDecisionSummary(
        organisation=decision.organisation,
        decision=decision,
        version=version,
        created_by=actor,
        **fields,
    )
    summary.full_clean(validate_unique=False, validate_constraints=False)
    summary.save()
    record_event(
        action="decision_analysis.executive_summary_created",
        object_type="executive_decision_summary",
        object_id=str(summary.id),
        actor=actor,
        organisation=decision.organisation,
        metadata={"decision_id": str(decision.id), "version": version},
    )
    return summary


@transaction.atomic
def update_executive_summary(*, actor: User, summary: ExecutiveDecisionSummary, fields: dict[str, Any]) -> ExecutiveDecisionSummary:
    summary = ExecutiveDecisionSummary.objects.select_for_update().select_related("decision__organisation").get(id=summary.id)
    if not can_manage_analysis(actor=actor, decision=summary.decision):
        raise PermissionDenied("Only accountable decision authorities may update this summary.")
    if summary.status != ExecutiveDecisionSummary.Status.DRAFT:
        raise DecisionAnalysisServiceError("Approved and superseded summaries are immutable.")
    requested_status = fields.pop("status", summary.status)
    for name, value in fields.items():
        setattr(summary, name, value)
    if requested_status == ExecutiveDecisionSummary.Status.APPROVED:
        ExecutiveDecisionSummary.objects.filter(
            decision=summary.decision,
            status=ExecutiveDecisionSummary.Status.APPROVED,
        ).update(status=ExecutiveDecisionSummary.Status.SUPERSEDED)
        summary.status = ExecutiveDecisionSummary.Status.APPROVED
        summary.approved_by = actor
        summary.approved_at = timezone.now()
    elif requested_status != ExecutiveDecisionSummary.Status.DRAFT:
        raise DecisionAnalysisServiceError({"status": "A draft may only be approved."})
    summary.full_clean(validate_unique=False, validate_constraints=False)
    summary.save()
    record_event(
        action="decision_analysis.executive_summary_updated",
        object_type="executive_decision_summary",
        object_id=str(summary.id),
        actor=actor,
        organisation=summary.organisation,
        metadata={"decision_id": str(summary.decision_id), "version": summary.version, "status": summary.status},
    )
    return summary
