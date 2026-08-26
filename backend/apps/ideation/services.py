"""Open session workflows: create/open/close, join, submit, vote, shortlist, promote."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.services import record_event
from apps.decision_options.services import create_option
from apps.decisions.models import Decision
from apps.decisions.policies import CREATOR_ROLES
from apps.organisations.models import Membership, Organisation
from apps.workspaces.models import Workspace

from .models import Idea, IdeaComment, IdeaTeamMember, IdeaVote, OpenSession, SessionParticipant
from .tokens import digest_token, generate_public_slug, generate_token

MAX_TEAM_MEMBERS = 12


class IdeationServiceError(ValidationError):
    """Expected open-session workflow failure."""


def _active_membership(*, actor: User, organisation_id: Any) -> Membership:
    try:
        return Membership.objects.get(
            organisation_id=organisation_id,
            user=actor,
            status=Membership.Status.ACTIVE,
        )
    except Membership.DoesNotExist as exc:
        raise PermissionDenied("You are not an active member of this organisation.") from exc


def _require_organiser(*, actor: User, session: OpenSession) -> None:
    membership = _active_membership(actor=actor, organisation_id=session.organisation_id)
    if membership.role not in CREATOR_ROLES:
        raise PermissionDenied("Your role cannot manage open sessions.")


@transaction.atomic
def create_session(
    *,
    actor: User,
    organisation: Organisation,
    decision: Decision | None = None,
    default_workspace: Workspace | None = None,
    title: str,
    prompt: str,
    description: str = "",
    voting_enabled: bool = True,
    submission_deadline: Any | None = None,
    requires_guardian_consent: bool = False,
    team_submissions_enabled: bool = False,
) -> OpenSession:
    membership = _active_membership(actor=actor, organisation_id=organisation.id)
    if membership.role not in CREATOR_ROLES:
        raise PermissionDenied("Your role cannot create open sessions.")
    if decision is not None and decision.organisation_id != organisation.id:
        raise IdeationServiceError({"decision": "The decision must belong to this organisation."})
    if default_workspace is not None and default_workspace.organisation_id != organisation.id:
        raise IdeationServiceError(
            {"default_workspace": "The workspace must belong to this organisation."}
        )
    if default_workspace is None:
        default_workspace = Workspace.objects.filter(
            organisation=organisation, is_default=True
        ).first()
    session = OpenSession(
        organisation=organisation,
        decision=decision,
        default_workspace=default_workspace,
        title=title,
        prompt=prompt,
        description=description,
        public_slug=generate_public_slug(),
        voting_enabled=voting_enabled,
        submission_deadline=submission_deadline,
        requires_guardian_consent=requires_guardian_consent,
        team_submissions_enabled=team_submissions_enabled,
        created_by=actor,
    )
    session.full_clean(validate_unique=False, validate_constraints=False)
    session.save()
    record_event(
        action="open_session.created",
        object_type="open_session",
        object_id=str(session.id),
        actor=actor,
        organisation=organisation,
        metadata={"title": session.title, "decision_id": str(decision.id) if decision else None},
    )
    return session


@transaction.atomic
def open_session(*, actor: User, session: OpenSession) -> OpenSession:
    _require_organiser(actor=actor, session=session)
    if session.status == OpenSession.Status.OPEN:
        return session
    session.status = OpenSession.Status.OPEN
    session.save(update_fields=["status", "updated_at"])
    record_event(
        action="open_session.opened",
        object_type="open_session",
        object_id=str(session.id),
        actor=actor,
        organisation=session.organisation,
    )
    return session


@transaction.atomic
def close_session(*, actor: User, session: OpenSession) -> OpenSession:
    _require_organiser(actor=actor, session=session)
    if session.status == OpenSession.Status.CLOSED:
        return session
    session.status = OpenSession.Status.CLOSED
    session.save(update_fields=["status", "updated_at"])
    record_event(
        action="open_session.closed",
        object_type="open_session",
        object_id=str(session.id),
        actor=actor,
        organisation=session.organisation,
    )
    return session


@transaction.atomic
def identify_participant(
    *,
    session: OpenSession,
    name: str,
    email: str,
    school_name: str = "",
    age_bracket: str = "",
    guardian_name: str = "",
    guardian_email: str = "",
    guardian_consent_given: bool = False,
) -> tuple[SessionParticipant, str]:
    """Get-or-create a lightweight identity for this session by email, returning a fresh bearer token.

    When the email matches a verified ApplicantAccount, the participant record is
    linked to it automatically, which is what lets that person's applications
    surface together on the cross-round "My applications" portal.

    When the session requires guardian consent and the declared age bracket is
    a minor one, a guardian name, guardian email, and explicit consent are
    required before the identity can be registered at all - this is the
    safeguard gate for student competitions open to under-18s.
    """
    normalised_email = email.strip().lower()
    raw_token = generate_token()

    if session.requires_guardian_consent and age_bracket in SessionParticipant.MINOR_AGE_BRACKETS:
        if not (guardian_name.strip() and guardian_email.strip() and guardian_consent_given):
            raise IdeationServiceError(
                {
                    "guardian_consent_given": (
                        "A parent or guardian must record consent before a participant "
                        "under 18 can join this session."
                    )
                }
            )

    from apps.applicants.models import ApplicantAccount

    linked_account = ApplicantAccount.objects.filter(
        email=normalised_email, email_verified_at__isnull=False
    ).first()
    consent_timestamp = timezone.now() if guardian_consent_given else None

    try:
        participant = SessionParticipant.objects.get(session=session, email=normalised_email)
        participant.token_digest = digest_token(raw_token)
        if name.strip():
            participant.name = name
        if linked_account is not None:
            participant.account = linked_account
        if school_name.strip():
            participant.school_name = school_name
        if age_bracket:
            participant.age_bracket = age_bracket
        if guardian_name.strip():
            participant.guardian_name = guardian_name
        if guardian_email.strip():
            participant.guardian_email = guardian_email
        if consent_timestamp is not None:
            participant.guardian_consent_given_at = consent_timestamp
        participant.full_clean(validate_unique=False, validate_constraints=False)
        participant.save(
            update_fields=[
                "name",
                "token_digest",
                "account",
                "school_name",
                "age_bracket",
                "guardian_name",
                "guardian_email",
                "guardian_consent_given_at",
                "updated_at",
            ]
        )
    except SessionParticipant.DoesNotExist:
        participant = SessionParticipant(
            session=session,
            name=name,
            email=normalised_email,
            token_digest=digest_token(raw_token),
            account=linked_account,
            school_name=school_name,
            age_bracket=age_bracket,
            guardian_name=guardian_name,
            guardian_email=guardian_email,
            guardian_consent_given_at=consent_timestamp,
        )
        participant.full_clean(validate_unique=False, validate_constraints=False)
        try:
            participant.save()
        except IntegrityError as exc:
            raise IdeationServiceError({"email": "Could not register that email for this session."}) from exc
    return participant, raw_token


def participant_from_token(*, session: OpenSession, raw_token: str) -> SessionParticipant:
    try:
        return SessionParticipant.objects.get(session=session, token_digest=digest_token(raw_token))
    except SessionParticipant.DoesNotExist as exc:
        raise PermissionDenied("This session link has expired or is invalid.") from exc


@transaction.atomic
def submit_idea(
    *,
    session: OpenSession,
    participant: SessionParticipant | None = None,
    user: User | None = None,
    title: str,
    description: str = "",
    category: str = "",
    requested_amount: Any | None = None,
    team_name: str = "",
    team_members: list[dict] | None = None,
) -> Idea:
    if session.status != OpenSession.Status.OPEN:
        raise IdeationServiceError("This session is not currently accepting submissions.")
    idea = Idea(
        session=session,
        title=title,
        description=description,
        category=category,
        requested_amount=requested_amount,
        team_name=team_name,
        submitted_by_participant=participant,
        submitted_by_user=user,
    )
    idea.full_clean(validate_unique=False, validate_constraints=False)
    idea.save()
    for member in (team_members or [])[:MAX_TEAM_MEMBERS]:
        team_member = IdeaTeamMember(idea=idea, name=member.get("name", ""), role=member.get("role", ""))
        team_member.full_clean(validate_unique=False, validate_constraints=False)
        team_member.save()
    return idea


@transaction.atomic
def cast_vote(
    *,
    idea: Idea,
    participant: SessionParticipant | None = None,
    user: User | None = None,
) -> IdeaVote:
    if idea.session.status != OpenSession.Status.OPEN:
        raise IdeationServiceError("This session is not currently accepting votes.")
    if not idea.session.voting_enabled:
        raise IdeationServiceError("Voting is not enabled for this session.")
    existing = IdeaVote.objects.filter(idea=idea, participant=participant, user=user).first()
    if existing:
        return existing
    vote = IdeaVote(idea=idea, participant=participant, user=user)
    vote.full_clean(validate_unique=False, validate_constraints=False)
    try:
        vote.save()
    except IntegrityError as exc:
        raise IdeationServiceError("You have already voted for this idea.") from exc
    return vote


@transaction.atomic
def remove_vote(
    *,
    idea: Idea,
    participant: SessionParticipant | None = None,
    user: User | None = None,
) -> None:
    IdeaVote.objects.filter(idea=idea, participant=participant, user=user).delete()


@transaction.atomic
def shortlist_idea(*, actor: User, idea: Idea, shortlisted: bool) -> Idea:
    _require_organiser(actor=actor, session=idea.session)
    if idea.status == Idea.Status.PROMOTED:
        raise IdeationServiceError("A promoted idea cannot be shortlisted or unshortlisted.")
    idea.status = Idea.Status.SHORTLISTED if shortlisted else Idea.Status.SUBMITTED
    idea.full_clean(validate_unique=False, validate_constraints=False)
    idea.save(update_fields=["status", "updated_at"])
    return idea


@transaction.atomic
def archive_idea(*, actor: User, idea: Idea, archived: bool) -> Idea:
    _require_organiser(actor=actor, session=idea.session)
    if idea.status == Idea.Status.PROMOTED:
        raise IdeationServiceError("A promoted idea cannot be archived.")
    idea.status = Idea.Status.ARCHIVED if archived else Idea.Status.SUBMITTED
    idea.full_clean(validate_unique=False, validate_constraints=False)
    idea.save(update_fields=["status", "updated_at"])
    return idea


@transaction.atomic
def promote_idea_to_decision(*, actor: User, idea: Idea, decision: Decision | None = None):
    """Turn a shortlisted idea into a real, accountable DecisionOption.

    Deliberately does not duplicate create_option's own permission check
    (apps.decisions.reasoning_policies.can_contribute_reasoning) - it already
    enforces whether this actor may add an option to this decision in its
    current state, and that failure should surface as-is, not be masked here.

    When decision is None, a new grant_round-templated Decision is created in
    the session's default_workspace instead of requiring an existing one.
    """
    _require_organiser(actor=actor, session=idea.session)
    if idea.status == Idea.Status.PROMOTED:
        raise IdeationServiceError("This idea has already been promoted.")
    if decision is None:
        if idea.session.default_workspace_id is None:
            raise IdeationServiceError(
                "This session has no default workspace to create a new grant round in."
            )
        from apps.decisions.services import create_decision

        decision = create_decision(
            actor=actor,
            workspace=idea.session.default_workspace,
            title=idea.title,
            purpose=idea.description,
            template_key="grant_round",
        )
    elif decision.organisation_id != idea.session.organisation_id:
        raise IdeationServiceError({"decision": "The decision must belong to this session's organisation."})
    option = create_option(
        actor=actor,
        decision=decision,
        title=idea.title,
        description=idea.description,
        estimated_cost=idea.requested_amount,
    )
    idea.status = Idea.Status.PROMOTED
    idea.promoted_to_option = option
    idea.full_clean(validate_unique=False, validate_constraints=False)
    idea.save(update_fields=["status", "promoted_to_option", "updated_at"])
    record_event(
        action="open_session.idea_promoted",
        object_type="idea",
        object_id=str(idea.id),
        actor=actor,
        organisation=idea.session.organisation,
        metadata={"decision_id": str(decision.id), "option_id": str(option.id), "title": idea.title},
    )
    return option


@transaction.atomic
def post_comment(
    *,
    idea: Idea,
    body: str,
    participant: SessionParticipant | None = None,
    user: User | None = None,
) -> IdeaComment:
    if idea.session.status != OpenSession.Status.OPEN:
        raise IdeationServiceError("This session is not currently accepting comments.")
    comment = IdeaComment(idea=idea, body=body, participant=participant, user=user)
    comment.full_clean(validate_unique=False, validate_constraints=False)
    comment.save()
    return comment


def comments_for_idea(*, idea: Idea) -> QuerySet[IdeaComment]:
    return IdeaComment.objects.filter(idea=idea).select_related("participant", "user")


def list_sessions(*, actor: User, organisation: Organisation):
    _active_membership(actor=actor, organisation_id=organisation.id)
    return (
        OpenSession.objects.filter(organisation=organisation)
        .select_related("decision", "created_by")
        .annotate(idea_count=Count("ideas", distinct=True))
    )


def ideas_for_session(*, session: OpenSession) -> QuerySet[Idea]:
    return (
        Idea.objects.filter(session=session)
        .select_related("submitted_by_participant", "submitted_by_user", "promoted_to_option")
        .prefetch_related("comments__participant", "comments__user")
        .annotate(vote_count=Count("votes", distinct=True))
        .order_by("-vote_count", "-created_at")
    )


def voted_idea_ids(
    *,
    session: OpenSession,
    participant: SessionParticipant | None = None,
    user: User | None = None,
) -> set[Any]:
    if participant is None and user is None:
        return set()
    return set(
        IdeaVote.objects.filter(
            idea__session=session, participant=participant, user=user
        ).values_list("idea_id", flat=True)
    )


def session_for_organiser(*, actor: User, session_id: Any) -> OpenSession:
    """Fetch a session scoped to the actor's own organisations, never revealing another tenant's."""
    visible = OpenSession.objects.filter(organisation__in=Organisation.objects.for_user(actor))
    return get_object_or_404(
        visible.select_related("organisation", "decision", "created_by").annotate(
            idea_count=Count("ideas", distinct=True)
        ),
        id=session_id,
    )


PUBLICLY_VISIBLE_STATUSES = {OpenSession.Status.OPEN, OpenSession.Status.CLOSED, OpenSession.Status.ARCHIVED}


def public_session_by_slug(*, public_slug: str) -> OpenSession:
    session = get_object_or_404(
        OpenSession.objects.select_related("organisation", "decision"),
        public_slug=public_slug,
    )
    if session.status not in PUBLICLY_VISIBLE_STATUSES:
        raise Http404("This session is not open yet.")
    return session
