"""Tenant-safe read models for contribution orchestration."""

from __future__ import annotations

from uuid import UUID

from django.db import models
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.accounts.models import User
from apps.decisions.selectors import decision_for_user

from .models import ContributionPreference, ContributionRequest, FacilitationSession, SessionParticipant
from .policies import can_manage_contributions, has_contribution_authority


def requests_for_decision(*, user: User, decision_id: UUID) -> models.QuerySet[ContributionRequest]:
    decision = decision_for_user(user=user, decision_id=decision_id)
    queryset = ContributionRequest.objects.filter(decision=decision).select_related(
        "assignee", "reviewer", "requested_by", "option", "session", "decision", "organisation"
    ).prefetch_related("submissions__author", "reviews__reviewer")
    if not has_contribution_authority(actor=user, decision=decision):
        queryset = queryset.exclude(status=ContributionRequest.Status.DRAFT)
    return queryset


def request_for_user(*, user: User, request_id: UUID) -> ContributionRequest:
    visible_decisions = decision_for_user_queryset(user=user)
    request = get_object_or_404(
        ContributionRequest.objects.select_related(
            "assignee", "reviewer", "requested_by", "option", "session", "decision", "organisation"
        ).prefetch_related("submissions__author", "reviews__reviewer"),
        id=request_id,
        decision__in=visible_decisions,
    )
    from .policies import can_view_request

    if not can_view_request(actor=user, request=request):
        raise Http404
    return request


def decision_for_user_queryset(*, user: User):
    from apps.decisions.models import Decision

    return Decision.objects.for_user(user)


def sessions_for_decision(*, user: User, decision_id: UUID) -> models.QuerySet[FacilitationSession]:
    decision = decision_for_user(user=user, decision_id=decision_id)
    return FacilitationSession.objects.filter(decision=decision).select_related(
        "facilitator", "created_by", "decision", "organisation"
    ).prefetch_related("participants__user")


def session_for_user(*, user: User, session_id: UUID) -> FacilitationSession:
    return get_object_or_404(
        FacilitationSession.objects.select_related(
            "facilitator", "created_by", "decision", "organisation"
        ).prefetch_related("participants__user"),
        id=session_id,
        decision__in=decision_for_user_queryset(user=user),
    )


def personal_contribution_work(*, user: User) -> dict:
    now = timezone.now()
    requests = list(
        ContributionRequest.objects.filter(Q(assignee=user) | Q(reviewer=user))
        .exclude(status__in=[ContributionRequest.Status.ACCEPTED, ContributionRequest.Status.CANCELLED])
        .filter(decision__in=decision_for_user_queryset(user=user))
        .select_related("decision", "organisation", "reviewer", "requested_by", "assignee", "session")
        .prefetch_related("submissions__author", "reviews__reviewer")
        .distinct()
        .order_by("due_at", "-priority", "created_at")[:100]
    )
    return {
        "summary": {
            "total": len(requests),
            "overdue": sum(1 for item in requests if item.assignee_id == user.id and item.due_at and item.due_at < now),
            "returned": sum(1 for item in requests if item.status == ContributionRequest.Status.RETURNED),
            "submitted": sum(1 for item in requests if item.status in {ContributionRequest.Status.SUBMITTED, ContributionRequest.Status.UNDER_REVIEW}),
            "awaiting_review": sum(
                1 for item in requests
                if item.reviewer_id == user.id
                and item.status in {ContributionRequest.Status.SUBMITTED, ContributionRequest.Status.UNDER_REVIEW}
            ),
        },
        "requests": requests,
    }


def contribution_preference(*, user: User, organisation_id: UUID) -> ContributionPreference:
    from apps.organisations.selectors import organisation_for_user

    organisation = organisation_for_user(user=user, organisation_id=organisation_id)
    preference, _ = ContributionPreference.objects.get_or_create(
        organisation=organisation,
        user=user,
    )
    return preference


def participation_summary(*, user: User, decision_id: UUID) -> dict:
    decision = decision_for_user(user=user, decision_id=decision_id)
    active_participants = list(
        decision.participants.filter(status="active").select_related("user")
    )
    requests = ContributionRequest.objects.filter(decision=decision).exclude(
        status=ContributionRequest.Status.DRAFT
    )
    assigned_user_ids = set(requests.values_list("assignee_id", flat=True))
    submitted_user_ids = set(
        requests.filter(status__in=[
            ContributionRequest.Status.SUBMITTED,
            ContributionRequest.Status.UNDER_REVIEW,
            ContributionRequest.Status.ACCEPTED,
        ]).values_list("assignee_id", flat=True)
    )
    return {
        "participant_count": len(active_participants),
        "assigned_count": len(assigned_user_ids),
        "submitted_count": len(submitted_user_ids),
        "coverage_percent": round((len(assigned_user_ids) / len(active_participants)) * 100) if active_participants else 0,
        "unassigned_participants": [
            {
                "id": str(item.user_id),
                "email": item.user.email,
                "role": item.role,
            }
            for item in active_participants
            if item.user_id not in assigned_user_ids and item.role != "observer"
        ],
        "role_counts": {
            role: sum(1 for item in active_participants if item.role == role)
            for role in {item.role for item in active_participants}
        },
    }


def session_participant_for_user(*, user: User, participant_id: UUID) -> SessionParticipant:
    return get_object_or_404(
        SessionParticipant.objects.select_related(
            "session__decision", "session__organisation", "user", "added_by"
        ),
        id=participant_id,
        session__decision__in=decision_for_user_queryset(user=user),
    )
