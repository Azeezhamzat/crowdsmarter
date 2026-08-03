"""Explainable portfolio and personal-work read models."""

from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from django.db import models
from django.db.models import Count, OuterRef, Q, Subquery
from django.utils import timezone

from apps.accounts.models import User
from apps.assumptions.models import Assumption
from apps.collaboration.models import DiscussionEntry
from apps.decisions.models import Decision
from apps.foresight.models import SignpostObservation
from apps.notifications.models import Notification
from apps.organisations.selectors import organisation_for_user
from apps.participants.models import Participant
from apps.positions.models import Position
from apps.reviews.models import DecisionReview
from apps.risks.models import Risk

STALLED_THRESHOLD_DAYS = 21
TRIGGERED_SIGNPOST_WINDOW_DAYS = 30
HIGH_RISK_THRESHOLD = 4
WATCHLIST_LIST_LIMIT = 10


def _participant_role_subquery(user: User):  # type: ignore[no-untyped-def]
    return Participant.objects.filter(
        decision=OuterRef("pk"),
        user=user,
        status=Participant.Status.ACTIVE,
    ).values("role")[:1]


def _base_portfolio_queryset(*, user: User) -> models.QuerySet[Decision]:
    return (
        Decision.objects.for_user(user)
        .select_related("organisation", "workspace", "owner", "review")
        .annotate(
            participant_role=Subquery(_participant_role_subquery(user)),
            unresolved_discussion_count=Count(
                "discussion_entries",
                filter=Q(
                    discussion_entries__kind__in=[
                        DiscussionEntry.Kind.QUESTION,
                        DiscussionEntry.Kind.CONCERN,
                    ],
                    discussion_entries__resolved_at__isnull=True,
                ),
                distinct=True,
            ),
        )
    )



def _review_for(decision: Decision) -> DecisionReview | None:
    try:
        return decision.review
    except DecisionReview.DoesNotExist:
        return None


def _due_date_for(decision: Decision) -> date | None:
    if decision.status in {
        Decision.Status.OPEN_FOR_CONTRIBUTION,
        Decision.Status.FRAMING,
    } and decision.contribution_deadline:
        return decision.contribution_deadline.date()
    if decision.status in {
        Decision.Status.DRAFT,
        Decision.Status.FRAMING,
        Decision.Status.OPEN_FOR_CONTRIBUTION,
        Decision.Status.UNDER_REVIEW,
        Decision.Status.READY_FOR_DECISION,
    }:
        return decision.target_decision_date
    review = _review_for(decision)
    if review and not review.reviewed_at:
        return review.review_due_date
    return None


def _next_action_for(*, decision: Decision, user: User, participant_role: str | None) -> str:
    if decision.status == Decision.Status.ARCHIVED:
        return ""
    if decision.status in {Decision.Status.DRAFT, Decision.Status.FRAMING}:
        return "Complete decision framing" if decision.owner_id == user.id else "Review framing"
    if decision.status == Decision.Status.OPEN_FOR_CONTRIBUTION:
        if participant_role and participant_role != Participant.Role.OBSERVER:
            return "Contribute options, evidence, assumptions, or risks"
        return "Monitor contributions"
    if decision.status == Decision.Status.UNDER_REVIEW:
        return "Review reasoning and unresolved concerns"
    if decision.status == Decision.Status.READY_FOR_DECISION:
        has_position = Position.objects.filter(
            decision=decision,
            participant__user=user,
            participant__status=Participant.Status.ACTIVE,
        ).exists()
        if participant_role in {
            Participant.Role.DECISION_OWNER,
            Participant.Role.DECISION_MAKER,
        } and not has_position:
            return "Submit your stakeholder position"
        if decision.owner_id == user.id or participant_role == Participant.Role.DECISION_MAKER:
            return "Review positions and finalise"
        return "Review stakeholder positions"
    if decision.status == Decision.Status.DECISION_FINALISED:
        if decision.owner_id == user.id:
            return "Record the implementation commitment"
        return "Review the final decision"
    review = _review_for(decision)
    if decision.status == Decision.Status.COMMITMENT:
        if review and review.implementation_owner_id == user.id:
            return "Start implementation"
        return "Monitor the commitment"
    if decision.status == Decision.Status.IMPLEMENTATION:
        if review and review.implementation_owner_id == user.id:
            return "Record implementation progress or open the outcome review"
        return "Monitor implementation"
    if decision.status == Decision.Status.OUTCOME_REVIEW:
        if review and review.implementation_owner_id == user.id:
            return "Complete the outcome review"
        return "Review outcome evidence"
    if decision.status == Decision.Status.LESSONS_LEARNED:
        return "Capture lessons and archive"
    return "Open decision"


def _decorate(*, decisions: list[Decision], user: User) -> list[Decision]:
    today = timezone.localdate()
    for decision in decisions:
        participant_role = getattr(decision, "participant_role", None)
        due_date = _due_date_for(decision)
        decision.portfolio_due_date = due_date  # type: ignore[attr-defined]
        decision.portfolio_is_overdue = bool(  # type: ignore[attr-defined]
            due_date and due_date < today and decision.status != Decision.Status.ARCHIVED
        )
        decision.portfolio_next_action = _next_action_for(  # type: ignore[attr-defined]
            decision=decision,
            user=user,
            participant_role=participant_role,
        )
    return decisions


def _stalled_decisions(*, organisation) -> list[dict]:
    """Decisions that have not moved status/content in STALLED_THRESHOLD_DAYS, excluding terminal statuses."""
    threshold = timezone.now() - timedelta(days=STALLED_THRESHOLD_DAYS)
    today = timezone.localdate()
    queryset = (
        Decision.objects.filter(organisation=organisation, updated_at__lt=threshold)
        .exclude(status__in=[Decision.Status.ARCHIVED, Decision.Status.LESSONS_LEARNED])
        .order_by("updated_at")[:WATCHLIST_LIST_LIMIT]
    )
    return [
        {
            "id": decision.id,
            "title": decision.title,
            "status": decision.status,
            "status_label": decision.get_status_display(),
            "days_stalled": (today - decision.updated_at.date()).days,
        }
        for decision in queryset
    ]


def _open_high_risks(*, organisation) -> list[dict]:
    queryset = (
        Risk.objects.filter(
            organisation=organisation,
            status__in=[Risk.Status.OPEN, Risk.Status.MONITORING],
        )
        .filter(Q(likelihood__gte=HIGH_RISK_THRESHOLD) | Q(impact__gte=HIGH_RISK_THRESHOLD))
        .select_related("decision")
        .order_by("-likelihood", "-impact")[:WATCHLIST_LIST_LIMIT]
    )
    return [
        {
            "id": risk.id,
            "title": risk.title,
            "decision_id": risk.decision_id,
            "decision_title": risk.decision.title,
            "likelihood": risk.likelihood,
            "impact": risk.impact,
        }
        for risk in queryset
    ]


def _assumptions_at_risk(*, organisation) -> list[dict]:
    today = timezone.localdate()
    queryset = (
        Assumption.objects.filter(organisation=organisation, status=Assumption.Status.ACTIVE)
        .filter(
            Q(verification_status=Assumption.VerificationStatus.INVALIDATED)
            | Q(review_date__lt=today)
        )
        .select_related("decision")
        .order_by("review_date")[:WATCHLIST_LIST_LIMIT]
    )
    return [
        {
            "id": assumption.id,
            "statement": assumption.statement,
            "decision_id": assumption.decision_id,
            "decision_title": assumption.decision.title,
            "verification_status": assumption.verification_status,
            "verification_status_label": assumption.get_verification_status_display(),
        }
        for assumption in queryset
    ]


def _triggered_signposts(*, organisation) -> list[dict]:
    since = timezone.localdate() - timedelta(days=TRIGGERED_SIGNPOST_WINDOW_DAYS)
    queryset = (
        SignpostObservation.objects.filter(
            signpost__scenario_set__canvas__organisation=organisation,
            assessment__in=[
                SignpostObservation.Assessment.STRONG,
                SignpostObservation.Assessment.CONTRADICTORY,
            ],
            observed_on__gte=since,
        )
        .select_related("signpost__scenario_set")
        .order_by("-observed_on")[:WATCHLIST_LIST_LIMIT]
    )
    return [
        {
            "id": observation.id,
            "signpost_id": observation.signpost_id,
            "signpost_title": observation.signpost.title,
            "scenario_set_id": observation.signpost.scenario_set_id,
            "canvas_id": observation.signpost.scenario_set.canvas_id,
            "assessment": observation.assessment,
            "assessment_label": observation.get_assessment_display(),
            "observed_on": observation.observed_on,
        }
        for observation in queryset
    ]


def _benefits_realization(*, organisation) -> dict:
    counts = {
        choice: 0 for choice, _ in DecisionReview.OutcomeAssessment.choices
    }
    rows = (
        DecisionReview.objects.filter(organisation=organisation)
        .exclude(outcome_assessment="")
        .values("outcome_assessment")
        .annotate(count=Count("id"))
    )
    for row in rows:
        counts[row["outcome_assessment"]] = row["count"]
    return {**counts, "total_reviewed": sum(counts.values())}


def _organisation_watchlist(*, organisation) -> dict:
    """Action-oriented cross-decision signals: every entry drills down to a source decision."""
    return {
        "stalled_decisions": _stalled_decisions(organisation=organisation),
        "open_high_risks": _open_high_risks(organisation=organisation),
        "assumptions_at_risk": _assumptions_at_risk(organisation=organisation),
        "triggered_signposts": _triggered_signposts(organisation=organisation),
        "benefits_realization": _benefits_realization(organisation=organisation),
    }


def organisation_portfolio(
    *,
    user: User,
    organisation_id: UUID,
    status: str = "",
    urgency: str = "",
    workspace_id: UUID | None = None,
    owner_id: UUID | None = None,
    query: str = "",
    my_work: bool = False,
    overdue_only: bool = False,
) -> dict:
    """Return one tenant's decision portfolio with explicit filters and counts."""
    organisation = organisation_for_user(user=user, organisation_id=organisation_id)
    queryset = _base_portfolio_queryset(user=user).filter(organisation=organisation)
    if status:
        queryset = queryset.filter(status=status)
    if urgency:
        queryset = queryset.filter(urgency=urgency)
    if workspace_id:
        queryset = queryset.filter(workspace_id=workspace_id)
    if owner_id:
        queryset = queryset.filter(owner_id=owner_id)
    if query:
        queryset = queryset.filter(
            Q(title__icontains=query)
            | Q(decision_question__icontains=query)
            | Q(purpose__icontains=query)
        )
    if my_work:
        queryset = queryset.filter(
            Q(owner=user)
            | Q(
                participants__user=user,
                participants__status=Participant.Status.ACTIVE,
            )
            | Q(review__implementation_owner=user)
        ).distinct()

    decisions = _decorate(decisions=list(queryset), user=user)
    if overdue_only:
        decisions = [item for item in decisions if item.portfolio_is_overdue]

    all_decisions = Decision.objects.filter(organisation=organisation)
    status_counts = {
        row["status"]: row["count"]
        for row in all_decisions.values("status").annotate(count=Count("id"))
    }
    return {
        "organisation": organisation,
        "summary": {
            "total": all_decisions.count(),
            "active": all_decisions.exclude(status=Decision.Status.ARCHIVED).count(),
            "overdue": sum(
                1
                for item in _decorate(
                    decisions=list(
                        _base_portfolio_queryset(user=user).filter(
                            organisation=organisation
                        )
                    ),
                    user=user,
                )
                if item.portfolio_is_overdue
            ),
            "unresolved_discussion": DiscussionEntry.objects.filter(
                organisation=organisation,
                kind__in=[DiscussionEntry.Kind.QUESTION, DiscussionEntry.Kind.CONCERN],
                resolved_at__isnull=True,
            ).count(),
            "status_counts": status_counts,
        },
        "decisions": decisions,
        "watchlist": _organisation_watchlist(organisation=organisation),
    }


def personal_work(*, user: User) -> dict:
    """Return the current user's accountable decisions across all tenants."""
    implementation_decisions = DecisionReview.objects.filter(
        implementation_owner=user,
        reviewed_at__isnull=True,
    ).values("decision_id")
    queryset = _base_portfolio_queryset(user=user).filter(
        Q(owner=user)
        | Q(
            participants__user=user,
            participants__status=Participant.Status.ACTIVE,
        )
        | Q(id__in=Subquery(implementation_decisions))
    ).exclude(status=Decision.Status.ARCHIVED).distinct()
    decisions = _decorate(decisions=list(queryset), user=user)
    urgency_order = {"critical": 0, "high": 1, "normal": 2, "low": 3}
    decisions.sort(
        key=lambda item: (
            not item.portfolio_is_overdue,
            item.portfolio_due_date or date.max,
            urgency_order.get(item.urgency, 9),
            -item.updated_at.timestamp(),
        )
    )
    return {
        "unread_notifications": Notification.objects.filter(
            recipient=user,
            read_at__isnull=True,
        ).count(),
        "overdue_count": sum(1 for item in decisions if item.portfolio_is_overdue),
        "decision_count": len(decisions),
        "decisions": decisions[:50],
    }
