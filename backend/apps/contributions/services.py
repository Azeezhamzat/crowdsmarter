"""Transactional contribution-orchestration workflows."""

from __future__ import annotations

import logging
from datetime import timedelta
from uuid import UUID

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.services import record_event
from apps.decisions.models import Decision
from apps.notifications.models import Notification
from apps.notifications.services import create_notification, notify_users
from apps.organisations.models import Membership
from apps.participants.models import Participant
from apps.platform_admin.contact import notification_sender_email

from .models import (
    ContributionPreference,
    ContributionRequest,
    ContributionReview,
    ContributionSubmission,
    FacilitationSession,
    SessionParticipant,
)
from .policies import (
    WRITABLE_STATUSES,
    can_manage_contributions,
    can_receive_assignment,
    can_review_request,
    can_work_on_request,
)

logger = logging.getLogger(__name__)


class ContributionServiceError(ValidationError):
    """Expected contribution workflow validation failure."""


def _active_member(*, decision: Decision, user_id: UUID) -> User:
    try:
        user = User.objects.get(
            id=user_id,
            organisation_memberships__organisation=decision.organisation,
            organisation_memberships__status=Membership.Status.ACTIVE,
        )
    except User.DoesNotExist as exc:
        raise ContributionServiceError("The selected person is not an active organisation member.") from exc
    return user


def _active_participant(*, decision: Decision, user_id: UUID) -> User:
    user = _active_member(decision=decision, user_id=user_id)
    if not can_receive_assignment(actor=user, decision=decision):
        raise ContributionServiceError(
            "Assignments require an active non-observer decision participant."
        )
    return user


def _reviewer(*, decision: Decision, user_id: UUID | None) -> User | None:
    if not user_id:
        return None
    user = _active_member(decision=decision, user_id=user_id)
    membership = decision.organisation.memberships.get(user=user)
    is_reviewer = decision.participants.filter(
        user=user,
        status=Participant.Status.ACTIVE,
        role__in=[
            Participant.Role.REVIEWER,
            Participant.Role.DECISION_MAKER,
            Participant.Role.DECISION_OWNER,
        ],
    ).exists()
    if membership.role not in {Membership.Role.OWNER, Membership.Role.ADMIN} and not is_reviewer:
        raise ContributionServiceError(
            "The reviewer must be a decision reviewer, decision maker, owner, or organisation manager."
        )
    return user


@transaction.atomic
def create_request(
    *,
    actor: User,
    decision: Decision,
    assignee_id: UUID,
    reviewer_id: UUID | None = None,
    kind: str,
    title: str,
    instructions: str,
    priority: str = ContributionRequest.Priority.NORMAL,
    due_at=None,
    option=None,
    session=None,
    open_immediately: bool = True,
) -> ContributionRequest:
    current = Decision.objects.select_for_update().select_related("organisation").get(id=decision.id)
    if not can_manage_contributions(actor=actor, decision=current):
        raise PermissionDenied("Only accountable decision authorities may create contribution requests.")
    assignee = _active_participant(decision=current, user_id=assignee_id)
    reviewer = _reviewer(decision=current, user_id=reviewer_id)
    if reviewer and reviewer.id == assignee.id:
        raise ContributionServiceError("The reviewer must be different from the assignee.")
    if option and option.decision_id != current.id:
        raise ContributionServiceError("The selected option does not belong to this decision.")
    if session and session.decision_id != current.id:
        raise ContributionServiceError("The selected facilitation session does not belong to this decision.")

    now = timezone.now()
    request = ContributionRequest(
        organisation=current.organisation,
        decision=current,
        option=option,
        session=session,
        requested_by=actor,
        assignee=assignee,
        reviewer=reviewer,
        kind=kind,
        title=title,
        instructions=instructions,
        priority=priority,
        due_at=due_at,
        status=ContributionRequest.Status.OPEN if open_immediately else ContributionRequest.Status.DRAFT,
        opened_at=now if open_immediately else None,
    )
    request.full_clean(validate_unique=False, validate_constraints=False)
    request.save()
    if open_immediately:
        _notify_assignment(request=request, actor=actor)
    record_event(
        action="contributions.request_created",
        object_type="contribution_request",
        object_id=str(request.id),
        actor=actor,
        organisation=current.organisation,
        metadata={
            "decision_id": str(current.id),
            "assignee_id": str(assignee.id),
            "reviewer_id": str(reviewer.id) if reviewer else None,
            "kind": request.kind,
            "status": request.status,
            "due_at": request.due_at.isoformat() if request.due_at else None,
        },
    )
    return request


@transaction.atomic
def update_request(
    *, actor: User, request: ContributionRequest, changes: dict
) -> ContributionRequest:
    """Revise an active assignment without rewriting submitted contribution history."""
    current = ContributionRequest.objects.select_for_update(of=("self",)).select_related(
        "decision", "organisation", "assignee", "reviewer"
    ).get(id=request.id)
    if not can_manage_contributions(actor=actor, decision=current.decision):
        raise PermissionDenied("Only accountable decision authorities may update this request.")
    editable_statuses = {
        ContributionRequest.Status.DRAFT,
        ContributionRequest.Status.OPEN,
        ContributionRequest.Status.IN_PROGRESS,
        ContributionRequest.Status.RETURNED,
    }
    if current.status not in editable_statuses:
        raise ContributionServiceError(
            "Submitted, accepted, or cancelled contribution requests cannot be reassigned or rewritten."
        )

    changed_fields: list[str] = []
    original_assignee = current.assignee
    if "assignee_id" in changes:
        assignee = _active_participant(decision=current.decision, user_id=changes["assignee_id"])
        if assignee.id != current.assignee_id:
            if current.submissions.exists():
                raise ContributionServiceError(
                    "A request with saved or submitted contribution history cannot be reassigned. "
                    "Cancel it and create a new accountable request instead."
                )
            current.assignee = assignee
            changed_fields.append("assignee")

    if "reviewer_id" in changes:
        reviewer = _reviewer(decision=current.decision, user_id=changes["reviewer_id"])
        if reviewer and reviewer.id == current.assignee_id:
            raise ContributionServiceError("The reviewer must be different from the assignee.")
        if (reviewer.id if reviewer else None) != current.reviewer_id:
            current.reviewer = reviewer
            changed_fields.append("reviewer")

    for field in ["title", "instructions", "priority", "due_at"]:
        if field in changes and getattr(current, field) != changes[field]:
            setattr(current, field, changes[field])
            changed_fields.append(field)
    if not changed_fields:
        return current

    current.full_clean(validate_unique=False, validate_constraints=False)
    current.save(update_fields=[*changed_fields, "updated_at"])
    if "assignee" in changed_fields and current.status != ContributionRequest.Status.DRAFT:
        create_notification(
            recipient=original_assignee,
            organisation=current.organisation,
            decision=current.decision,
            kind=Notification.Kind.ASSIGNMENT,
            title="Contribution reassigned",
            message=f"{actor.email} reassigned “{current.title}” to {current.assignee.email}.",
            url=f"/decisions/{current.decision_id}/contributions#request-{current.id}",
            metadata={"contribution_request_id": str(current.id), "new_assignee_id": str(current.assignee_id)},
            dedup_key=f"contribution-reassigned-from:{current.id}:{original_assignee.id}:{current.updated_at.isoformat()}",
        )
        _notify_assignment(
            request=current, actor=actor, event_key=f"reassigned-{current.updated_at.timestamp()}"
        )

    record_event(
        action="contributions.request_updated",
        object_type="contribution_request",
        object_id=str(current.id),
        actor=actor,
        organisation=current.organisation,
        metadata={
            "decision_id": str(current.decision_id),
            "changed_fields": changed_fields,
            "assignee_id": str(current.assignee_id),
            "reviewer_id": str(current.reviewer_id) if current.reviewer_id else None,
        },
    )
    return current


def _notify_assignment(
    *, request: ContributionRequest, actor: User, event_key: str = "opened"
) -> None:
    create_notification(
        recipient=request.assignee,
        organisation=request.organisation,
        decision=request.decision,
        kind=Notification.Kind.ASSIGNMENT,
        title="Contribution requested",
        message=f"{actor.email} assigned “{request.title}” on “{request.decision.title}”.",
        url=f"/decisions/{request.decision_id}/contributions#request-{request.id}",
        metadata={"contribution_request_id": str(request.id), "due_at": request.due_at.isoformat() if request.due_at else None},
        dedup_key=f"contribution-request-{event_key}:{request.id}",
    )
    preference = ContributionPreference.objects.filter(
        organisation=request.organisation,
        user=request.assignee,
        email_enabled=True,
        digest_cadence=ContributionPreference.DigestCadence.IMMEDIATE,
    ).first()
    if preference:
        try:
            send_mail(
                subject=f"CrowdSmarter contribution request - {request.title}",
                message=(
                    f"{actor.email} assigned a contribution on {request.decision.title}.\n\n"
                    f"{request.title}\n{request.instructions}\n\n"
                    f"Open: {settings.FRONTEND_BASE_URL}/decisions/{request.decision_id}/contributions"
                ),
                from_email=notification_sender_email(),
                recipient_list=[request.assignee.email],
                fail_silently=False,
            )
        except Exception:
            # Email delivery must never roll back the stored assignment or in-app notification.
            pass


@transaction.atomic
def open_request(*, actor: User, request: ContributionRequest) -> ContributionRequest:
    current = ContributionRequest.objects.select_for_update().select_related(
        "decision", "organisation", "assignee"
    ).get(id=request.id)
    if not can_manage_contributions(actor=actor, decision=current.decision):
        raise PermissionDenied("Only accountable decision authorities may open this request.")
    if current.status != ContributionRequest.Status.DRAFT:
        raise ContributionServiceError("Only a draft request can be opened.")
    current.status = ContributionRequest.Status.OPEN
    current.opened_at = timezone.now()
    current.full_clean(validate_unique=False, validate_constraints=False)
    current.save(update_fields=["status", "opened_at", "updated_at"])
    _notify_assignment(request=current, actor=actor)
    record_event(
        action="contributions.request_opened",
        object_type="contribution_request",
        object_id=str(current.id),
        actor=actor,
        organisation=current.organisation,
        metadata={"decision_id": str(current.decision_id)},
    )
    return current


@transaction.atomic
def start_request(*, actor: User, request: ContributionRequest) -> ContributionRequest:
    current = ContributionRequest.objects.select_for_update().select_related("decision", "organisation").get(id=request.id)
    if not can_work_on_request(actor=actor, request=current):
        raise PermissionDenied("Only the assigned contributor may start this request.")
    if current.status not in {ContributionRequest.Status.OPEN, ContributionRequest.Status.RETURNED}:
        raise ContributionServiceError("This request cannot be started from its current state.")
    current.status = ContributionRequest.Status.IN_PROGRESS
    current.save(update_fields=["status", "updated_at"])
    record_event(
        action="contributions.request_started",
        object_type="contribution_request",
        object_id=str(current.id),
        actor=actor,
        organisation=current.organisation,
        metadata={"decision_id": str(current.decision_id)},
    )
    return current


@transaction.atomic
def save_draft(
    *, actor: User, request: ContributionRequest, body: str, references: str = ""
) -> ContributionSubmission:
    current = ContributionRequest.objects.select_for_update().select_related("decision", "organisation").get(id=request.id)
    if not can_work_on_request(actor=actor, request=current):
        raise PermissionDenied("Only the assigned contributor may save this draft.")
    draft = ContributionSubmission.objects.filter(
        request=current,
        author=actor,
        status=ContributionSubmission.Status.DRAFT,
    ).first()
    if draft is None:
        sequence = (ContributionSubmission.objects.filter(request=current).aggregate(value=Max("sequence"))["value"] or 0) + 1
        draft = ContributionSubmission(
            organisation=current.organisation,
            decision=current.decision,
            request=current,
            author=actor,
            sequence=sequence,
            body=body,
            references=references,
        )
    else:
        draft.body = body
        draft.references = references
    draft.full_clean(validate_unique=False, validate_constraints=False)
    draft.save()
    if current.status in {ContributionRequest.Status.OPEN, ContributionRequest.Status.RETURNED}:
        current.status = ContributionRequest.Status.IN_PROGRESS
        current.save(update_fields=["status", "updated_at"])
    record_event(
        action="contributions.draft_saved",
        object_type="contribution_submission",
        object_id=str(draft.id),
        actor=actor,
        organisation=current.organisation,
        metadata={"decision_id": str(current.decision_id), "request_id": str(current.id), "sequence": draft.sequence},
    )
    return draft


@transaction.atomic
def submit_request(
    *, actor: User, request: ContributionRequest, body: str | None = None, references: str = ""
) -> ContributionSubmission:
    current = ContributionRequest.objects.select_for_update(of=("self",)).select_related(
        "decision", "organisation", "reviewer", "requested_by"
    ).get(id=request.id)
    if not can_work_on_request(actor=actor, request=current):
        raise PermissionDenied("Only the assigned contributor may submit this request.")
    draft = ContributionSubmission.objects.filter(
        request=current,
        author=actor,
        status=ContributionSubmission.Status.DRAFT,
    ).first()
    if draft is None:
        if not body or not body.strip():
            raise ContributionServiceError("Save or provide a substantive response before submitting.")
        draft = save_draft(actor=actor, request=current, body=body, references=references)
        draft = ContributionSubmission.objects.select_for_update().get(id=draft.id)
    elif body is not None:
        draft.body = body
        draft.references = references
    draft.status = ContributionSubmission.Status.SUBMITTED
    draft.submitted_at = timezone.now()
    draft.full_clean(validate_unique=False, validate_constraints=False)
    draft.save(update_fields=["body", "references", "status", "submitted_at", "updated_at"])
    current.status = ContributionRequest.Status.SUBMITTED
    current.submitted_at = draft.submitted_at
    current.reviewed_at = None
    current.completed_at = None
    current.save(update_fields=["status", "submitted_at", "reviewed_at", "completed_at", "updated_at"])
    recipients = [current.reviewer or current.requested_by]
    notify_users(
        recipients=recipients,
        organisation=current.organisation,
        decision=current.decision,
        kind=Notification.Kind.ASSIGNMENT,
        title="Contribution submitted",
        message=f"{actor.email} submitted “{current.title}” for review.",
        url=f"/decisions/{current.decision_id}/contributions#request-{current.id}",
        metadata={"contribution_request_id": str(current.id), "submission_id": str(draft.id)},
        dedup_key_prefix=f"contribution-submitted:{draft.id}",
        exclude_user_id=actor.id,
    )
    record_event(
        action="contributions.request_submitted",
        object_type="contribution_submission",
        object_id=str(draft.id),
        actor=actor,
        organisation=current.organisation,
        metadata={"decision_id": str(current.decision_id), "request_id": str(current.id), "sequence": draft.sequence},
    )
    return draft


@transaction.atomic
def start_review(*, actor: User, request: ContributionRequest) -> ContributionRequest:
    current = ContributionRequest.objects.select_for_update().select_related("decision", "organisation").get(id=request.id)
    if not can_review_request(actor=actor, request=current):
        raise PermissionDenied("You are not authorised to review this contribution.")
    if current.status != ContributionRequest.Status.SUBMITTED:
        raise ContributionServiceError("Only a submitted contribution can enter review.")
    current.status = ContributionRequest.Status.UNDER_REVIEW
    current.save(update_fields=["status", "updated_at"])
    record_event(
        action="contributions.review_started",
        object_type="contribution_request",
        object_id=str(current.id),
        actor=actor,
        organisation=current.organisation,
        metadata={"decision_id": str(current.decision_id)},
    )
    return current


@transaction.atomic
def review_submission(
    *, actor: User, request: ContributionRequest, outcome: str, note: str
) -> ContributionReview:
    current = ContributionRequest.objects.select_for_update().select_related(
        "decision", "organisation", "assignee"
    ).get(id=request.id)
    if not can_review_request(actor=actor, request=current):
        raise PermissionDenied("You are not authorised to review this contribution.")
    if current.status not in {ContributionRequest.Status.SUBMITTED, ContributionRequest.Status.UNDER_REVIEW}:
        raise ContributionServiceError("Only a submitted contribution can be reviewed.")
    submission = current.submissions.filter(status=ContributionSubmission.Status.SUBMITTED).order_by("-sequence").first()
    if submission is None:
        raise ContributionServiceError("No submitted revision is available for review.")
    if outcome not in ContributionReview.Outcome.values:
        raise ContributionServiceError("Select a valid review outcome.")
    review = ContributionReview(
        organisation=current.organisation,
        decision=current.decision,
        request=current,
        submission=submission,
        reviewer=actor,
        outcome=outcome,
        note=note,
    )
    review.full_clean(validate_unique=False, validate_constraints=False)
    review.save()
    now = timezone.now()
    current.reviewed_at = now
    if outcome == ContributionReview.Outcome.ACCEPTED:
        current.status = ContributionRequest.Status.ACCEPTED
        current.completed_at = now
    elif outcome == ContributionReview.Outcome.RETURNED:
        current.status = ContributionRequest.Status.RETURNED
        current.completed_at = None
    else:
        current.status = ContributionRequest.Status.UNDER_REVIEW
    current.save(update_fields=["status", "reviewed_at", "completed_at", "updated_at"])
    create_notification(
        recipient=current.assignee,
        organisation=current.organisation,
        decision=current.decision,
        kind=Notification.Kind.ASSIGNMENT,
        title=f"Contribution {review.get_outcome_display().lower()}",
        message=f"{actor.email} reviewed “{current.title}”: {review.note}",
        url=f"/decisions/{current.decision_id}/contributions#request-{current.id}",
        metadata={"contribution_request_id": str(current.id), "review_id": str(review.id), "outcome": outcome},
        dedup_key=f"contribution-review:{review.id}",
    )
    record_event(
        action=f"contributions.review_{outcome}",
        object_type="contribution_review",
        object_id=str(review.id),
        actor=actor,
        organisation=current.organisation,
        metadata={"decision_id": str(current.decision_id), "request_id": str(current.id), "submission_id": str(submission.id)},
    )
    return review


@transaction.atomic
def cancel_request(*, actor: User, request: ContributionRequest, reason: str) -> ContributionRequest:
    current = ContributionRequest.objects.select_for_update().select_related(
        "decision", "organisation", "assignee"
    ).get(id=request.id)
    if not can_manage_contributions(actor=actor, decision=current.decision):
        raise PermissionDenied("Only accountable decision authorities may cancel this request.")
    if current.is_terminal:
        raise ContributionServiceError("This request is already complete or cancelled.")
    current.status = ContributionRequest.Status.CANCELLED
    current.cancelled_at = timezone.now()
    current.save(update_fields=["status", "cancelled_at", "updated_at"])
    create_notification(
        recipient=current.assignee,
        organisation=current.organisation,
        decision=current.decision,
        kind=Notification.Kind.ASSIGNMENT,
        title="Contribution request cancelled",
        message=f"{actor.email} cancelled “{current.title}”. {reason.strip()}",
        url=f"/decisions/{current.decision_id}/contributions",
        metadata={"contribution_request_id": str(current.id), "reason": reason.strip()},
        dedup_key=f"contribution-cancelled:{current.id}",
    )
    record_event(
        action="contributions.request_cancelled",
        object_type="contribution_request",
        object_id=str(current.id),
        actor=actor,
        organisation=current.organisation,
        metadata={"decision_id": str(current.decision_id), "reason": reason.strip()},
    )
    return current


@transaction.atomic
def create_session(
    *, actor: User, decision: Decision, title: str, objective: str, agenda: str = "",
    participation_guidance: str = "", facilitator_id: UUID | None = None,
    starts_at=None, ends_at=None, participant_ids: list[UUID] | None = None,
) -> FacilitationSession:
    current = Decision.objects.select_for_update().select_related("organisation").get(id=decision.id)
    if not can_manage_contributions(actor=actor, decision=current):
        raise PermissionDenied("Only accountable decision authorities may create facilitation sessions.")
    facilitator = _reviewer(decision=current, user_id=facilitator_id or actor.id)
    assert facilitator is not None
    session = FacilitationSession(
        organisation=current.organisation,
        decision=current,
        title=title,
        objective=objective,
        agenda=agenda,
        participation_guidance=participation_guidance,
        facilitator=facilitator,
        starts_at=starts_at,
        ends_at=ends_at,
        created_by=actor,
    )
    session.full_clean(validate_unique=False, validate_constraints=False)
    session.save()
    for user_id in list(dict.fromkeys(participant_ids or [])):
        user = _active_participant(decision=current, user_id=user_id)
        SessionParticipant.objects.create(
            session=session,
            organisation=current.organisation,
            user=user,
            added_by=actor,
        )
    notify_users(
        recipients=[item.user for item in session.participants.select_related("user")],
        organisation=current.organisation,
        decision=current,
        kind=Notification.Kind.ASSIGNMENT,
        title="Facilitation session scheduled",
        message=f"{actor.email} scheduled “{session.title}” for “{current.title}”.",
        url=f"/decisions/{current.id}/contributions#session-{session.id}",
        metadata={"facilitation_session_id": str(session.id)},
        dedup_key_prefix=f"facilitation-session:{session.id}",
        exclude_user_id=actor.id,
    )
    record_event(
        action="contributions.session_created",
        object_type="facilitation_session",
        object_id=str(session.id),
        actor=actor,
        organisation=current.organisation,
        metadata={"decision_id": str(current.id), "participant_count": session.participants.count()},
    )
    return session


@transaction.atomic
def update_session_status(*, actor: User, session: FacilitationSession, status: str) -> FacilitationSession:
    current = FacilitationSession.objects.select_for_update().select_related("decision", "organisation").get(id=session.id)
    if current.decision.status not in WRITABLE_STATUSES:
        raise ContributionServiceError("Facilitation history is read-only after the decision leaves contribution and review.")
    if not can_manage_contributions(actor=actor, decision=current.decision) and current.facilitator_id != actor.id:
        raise PermissionDenied("Only the facilitator or accountable authority may update this session.")
    if status not in FacilitationSession.Status.values:
        raise ContributionServiceError("Select a valid session status.")
    transitions = {
        FacilitationSession.Status.PLANNED: {
            FacilitationSession.Status.OPEN,
            FacilitationSession.Status.CANCELLED,
        },
        FacilitationSession.Status.OPEN: {
            FacilitationSession.Status.CLOSED,
            FacilitationSession.Status.CANCELLED,
        },
        FacilitationSession.Status.CLOSED: set(),
        FacilitationSession.Status.CANCELLED: set(),
    }
    if status not in transitions[current.status]:
        raise ContributionServiceError(
            f"A {current.get_status_display().lower()} session cannot move to {status}."
        )
    current.status = status
    current.closed_at = timezone.now() if status == FacilitationSession.Status.CLOSED else None
    current.full_clean(validate_unique=False, validate_constraints=False)
    current.save(update_fields=["status", "closed_at", "updated_at"])
    record_event(
        action=f"contributions.session_{status}",
        object_type="facilitation_session",
        object_id=str(current.id),
        actor=actor,
        organisation=current.organisation,
        metadata={"decision_id": str(current.decision_id)},
    )
    return current


@transaction.atomic
def update_preference(
    *, preference: ContributionPreference, digest_cadence: str, email_enabled: bool,
    due_reminders_enabled: bool, reminder_days_before: int,
) -> ContributionPreference:
    current = ContributionPreference.objects.select_for_update().get(id=preference.id)
    current.digest_cadence = digest_cadence
    current.email_enabled = email_enabled
    current.due_reminders_enabled = due_reminders_enabled
    current.reminder_days_before = reminder_days_before
    current.full_clean(validate_unique=False, validate_constraints=False)
    current.save(update_fields=[
        "digest_cadence", "email_enabled", "due_reminders_enabled",
        "reminder_days_before", "updated_at",
    ])
    return current


def deliver_due_reminders(*, now=None) -> int:
    """Create deduplicated in-app reminders for due-soon and overdue assignments."""
    current_time = now or timezone.now()
    delivered = 0
    preferences = ContributionPreference.objects.filter(due_reminders_enabled=True).select_related("user", "organisation")
    for preference in preferences:
        deadline = current_time + timedelta(days=preference.reminder_days_before)
        requests = ContributionRequest.objects.filter(
            organisation=preference.organisation,
            assignee=preference.user,
            due_at__isnull=False,
            due_at__lte=deadline,
            status__in=[
                ContributionRequest.Status.OPEN,
                ContributionRequest.Status.IN_PROGRESS,
                ContributionRequest.Status.RETURNED,
            ],
        )
        for request in requests.select_related("decision"):
            day_key = current_time.date().isoformat()
            before = Notification.objects.filter(
                recipient=preference.user,
                dedup_key=f"contribution-due:{request.id}:{day_key}",
            ).exists()
            create_notification(
                recipient=preference.user,
                organisation=request.organisation,
                decision=request.decision,
                kind=Notification.Kind.REVIEW_DUE,
                title="Contribution overdue" if request.due_at < current_time else "Contribution due soon",
                message=f"“{request.title}” is due {request.due_at.strftime('%d %b %Y %H:%M UTC')}.",
                url=f"/decisions/{request.decision_id}/contributions#request-{request.id}",
                metadata={"contribution_request_id": str(request.id), "due_at": request.due_at.isoformat()},
                dedup_key=f"contribution-due:{request.id}:{day_key}",
            )
            if not before:
                delivered += 1
    return delivered


def deliver_email_digests(*, now=None) -> int:
    """Send optional daily or weekly contribution digests through the configured email backend."""
    current_time = now or timezone.now()
    delivered = 0
    preferences = ContributionPreference.objects.filter(
        email_enabled=True,
        digest_cadence__in=[ContributionPreference.DigestCadence.DAILY, ContributionPreference.DigestCadence.WEEKLY],
        user__is_active=True,
    ).select_related("user", "organisation")
    for preference in preferences:
        interval = timedelta(days=1 if preference.digest_cadence == ContributionPreference.DigestCadence.DAILY else 7)
        if preference.last_digest_at and current_time - preference.last_digest_at < interval:
            continue
        requests = list(
            ContributionRequest.objects.filter(
                organisation=preference.organisation,
                assignee=preference.user,
            ).exclude(status__in=[ContributionRequest.Status.ACCEPTED, ContributionRequest.Status.CANCELLED])
            .select_related("decision")
            .order_by("due_at", "-priority")[:50]
        )
        if not requests:
            preference.last_digest_at = current_time
            preference.save(update_fields=["last_digest_at", "updated_at"])
            continue
        lines = [
            f"Your CrowdSmarter contribution digest for {preference.organisation.name}",
            "",
        ]
        for item in requests:
            due = item.due_at.strftime("%d %b %Y %H:%M UTC") if item.due_at else "No due date"
            lines.append(f"- {item.title} - {item.get_status_display()} - {due}")
        lines.extend(["", f"Open CrowdSmarter: {settings.FRONTEND_BASE_URL}/contributions"])
        try:
            send_mail(
                subject=f"CrowdSmarter contribution digest - {preference.organisation.name}",
                message="\n".join(lines),
                from_email=notification_sender_email(),
                recipient_list=[preference.user.email],
                fail_silently=False,
            )
        except Exception:
            logger.exception(
                "Contribution digest delivery failed",
                extra={
                    "organisation_id": str(preference.organisation_id),
                    "user_id": str(preference.user_id),
                },
            )
            continue
        preference.last_digest_at = current_time
        preference.save(update_fields=["last_digest_at", "updated_at"])
        delivered += 1
    return delivered


@transaction.atomic
def update_session_attendance(*, actor: User, participant: SessionParticipant, attendance: str) -> SessionParticipant:
    current = SessionParticipant.objects.select_for_update().select_related(
        "session__decision", "session__organisation", "user"
    ).get(id=participant.id)
    session = current.session
    if session.decision.status not in WRITABLE_STATUSES:
        raise ContributionServiceError("Facilitation attendance is read-only after the decision leaves contribution and review.")
    if not can_manage_contributions(actor=actor, decision=session.decision) and session.facilitator_id != actor.id:
        raise PermissionDenied("Only the facilitator or accountable authority may record attendance.")
    if attendance not in SessionParticipant.Attendance.values:
        raise ContributionServiceError("Select a valid attendance state.")
    current.attendance = attendance
    current.full_clean(validate_unique=False, validate_constraints=False)
    current.save(update_fields=["attendance", "updated_at"])
    record_event(
        action="contributions.session_attendance_updated",
        object_type="session_participant",
        object_id=str(current.id),
        actor=actor,
        organisation=session.organisation,
        metadata={
            "decision_id": str(session.decision_id),
            "session_id": str(session.id),
            "user_id": str(current.user_id),
            "attendance": attendance,
        },
    )
    return current
