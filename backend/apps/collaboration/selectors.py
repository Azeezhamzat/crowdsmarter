"""Tenant-safe discussion and activity selectors."""

from __future__ import annotations

from uuid import UUID

from django.db import models
from django.shortcuts import get_object_or_404

from apps.accounts.models import User
from apps.audit.models import AuditEvent
from apps.decisions.models import Decision
from apps.decisions.selectors import decision_for_user

from .models import DiscussionEntry


def discussion_for_decision(
    *, user: User, decision_id: UUID
) -> models.QuerySet[DiscussionEntry]:
    decision = decision_for_user(user=user, decision_id=decision_id)
    return DiscussionEntry.objects.filter(decision=decision).select_related(
        "author",
        "reply_to",
        "reply_to__author",
        "resolved_by",
    ).prefetch_related("mentioned_users")


def discussion_entry_for_user(*, user: User, entry_id: UUID) -> DiscussionEntry:
    return get_object_or_404(
        DiscussionEntry.objects.select_related(
            "organisation",
            "decision",
            "author",
            "reply_to",
            "resolved_by",
        ).prefetch_related("mentioned_users").filter(
            decision__in=Decision.objects.for_user(user)
        ),
        id=entry_id,
    )


def audit_events_for_decision(*, user: User, decision_id: UUID):  # type: ignore[no-untyped-def]
    decision = decision_for_user(user=user, decision_id=decision_id)
    return (
        AuditEvent.objects.filter(organisation=decision.organisation)
        .filter(
            models.Q(object_type="decision", object_id=str(decision.id))
            | models.Q(metadata__decision_id=str(decision.id))
        )
        .exclude(action__startswith="collaboration.")
        .select_related("actor")
    )
