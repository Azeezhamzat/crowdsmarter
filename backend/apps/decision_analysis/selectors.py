"""Tenant-safe selectors for decision analysis records."""

from django.shortcuts import get_object_or_404

from apps.decisions.selectors import decision_for_user

from .models import DecisionIssue, DecisionQualityReview, ExecutiveDecisionSummary
from .policies import can_manage_analysis


def analysis_decision_for_user(*, user, decision_id):
    return decision_for_user(user=user, decision_id=decision_id)


def issues_for_decision(*, user, decision_id):
    decision = decision_for_user(user=user, decision_id=decision_id)
    return DecisionIssue.objects.filter(decision=decision).select_related(
        "owner",
        "created_by",
        "resolved_by",
        "option",
        "evidence",
        "assumption",
        "risk",
        "evaluation_exercise",
        "scenario_set",
    )


def issue_for_user(*, user, issue_id):
    return get_object_or_404(
        DecisionIssue.objects.select_related(
            "decision__organisation",
            "owner",
            "created_by",
            "resolved_by",
            "option",
            "evidence",
            "assumption",
            "risk",
            "evaluation_exercise",
            "scenario_set",
        ).filter(organisation__memberships__user=user, organisation__memberships__status="active"),
        id=issue_id,
    )


def reviews_for_decision(*, user, decision_id):
    decision = decision_for_user(user=user, decision_id=decision_id)
    queryset = DecisionQualityReview.objects.filter(decision=decision).select_related("author")
    if not can_manage_analysis(actor=user, decision=decision):
        queryset = queryset.exclude(status=DecisionQualityReview.Status.DRAFT)
    return queryset


def review_for_user(*, user, review_id):
    return get_object_or_404(
        DecisionQualityReview.objects.select_related("decision__organisation", "author").filter(
            organisation__memberships__user=user, organisation__memberships__status="active"
        ),
        id=review_id,
    )


def summaries_for_decision(*, user, decision_id):
    decision = decision_for_user(user=user, decision_id=decision_id)
    queryset = ExecutiveDecisionSummary.objects.filter(decision=decision).select_related(
        "created_by", "approved_by"
    )
    if not can_manage_analysis(actor=user, decision=decision):
        queryset = queryset.exclude(status=ExecutiveDecisionSummary.Status.DRAFT)
    return queryset


def summary_for_user(*, user, summary_id):
    return get_object_or_404(
        ExecutiveDecisionSummary.objects.select_related(
            "decision__organisation", "created_by", "approved_by"
        ).filter(organisation__memberships__user=user, organisation__memberships__status="active"),
        id=summary_id,
    )
