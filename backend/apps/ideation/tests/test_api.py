"""Open session behaviour: public join/submit/vote, and the org-authenticated organiser surface."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.decision_options.models import DecisionOption
from apps.decision_options.services import set_eligibility, set_outcome
from apps.ideation import services
from apps.ideation.models import Idea, IdeaVote, OpenSession, SessionParticipant
from apps.organisations.models import Membership


def _csrf_client() -> tuple[APIClient, str]:
    client = APIClient(enforce_csrf_checks=True)
    csrf_token = client.get(reverse("accounts:csrf")).cookies["csrftoken"].value
    return client, csrf_token


@pytest.mark.django_db
def test_public_session_lifecycle_join_submit_vote(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    session = services.create_session(
        actor=owner,
        organisation=organisation,
        title="Farm resilience ideathon",
        prompt="How should we cut post-harvest loss in half by 2028?",
    )
    services.open_session(actor=owner, session=session)

    client, csrf_token = _csrf_client()
    detail_url = reverse("ideation:public-detail", kwargs={"public_slug": session.public_slug})
    detail = client.get(detail_url)
    assert detail.status_code == 200
    assert detail.json()["title"] == "Farm resilience ideathon"
    assert detail.json()["ideas"] == []

    join = client.post(
        reverse("ideation:public-join", kwargs={"public_slug": session.public_slug}),
        {"name": "Amaka Obi", "email": "amaka@example.com"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert join.status_code == 201
    token = join.json()["participant_token"]
    assert SessionParticipant.objects.filter(session=session, email="amaka@example.com").exists()

    submit = client.post(
        reverse("ideation:public-idea-create", kwargs={"public_slug": session.public_slug}),
        {
            "title": "Solar-powered cold storage co-ops",
            "description": "Shared cold storage for smallholders.",
        },
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
        HTTP_X_PARTICIPANT_TOKEN=token,
    )
    assert submit.status_code == 200
    ideas = submit.json()["ideas"]
    assert len(ideas) == 1
    idea_id = ideas[0]["id"]
    assert ideas[0]["submitted_by_participant"]["name"] == "Amaka Obi"
    assert ideas[0]["vote_count"] == 0
    assert ideas[0]["voted_by_me"] is False

    vote = client.post(
        reverse(
            "ideation:public-idea-vote",
            kwargs={"public_slug": session.public_slug, "idea_id": idea_id},
        ),
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
        HTTP_X_PARTICIPANT_TOKEN=token,
    )
    assert vote.status_code == 200
    voted_idea = vote.json()["ideas"][0]
    assert voted_idea["vote_count"] == 1
    assert voted_idea["voted_by_me"] is True

    unvote = client.delete(
        reverse(
            "ideation:public-idea-vote",
            kwargs={"public_slug": session.public_slug, "idea_id": idea_id},
        ),
        HTTP_X_CSRFTOKEN=csrf_token,
        HTTP_X_PARTICIPANT_TOKEN=token,
    )
    assert unvote.status_code == 200
    assert unvote.json()["ideas"][0]["vote_count"] == 0


@pytest.mark.django_db
def test_public_endpoints_require_csrf(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    session = services.create_session(
        actor=organisation.created_by,
        organisation=organisation,
        title="Open problem analysis",
        prompt="What is slowing down onboarding?",
    )
    services.open_session(actor=organisation.created_by, session=session)
    client = APIClient(enforce_csrf_checks=True)
    response = client.post(
        reverse("ideation:public-join", kwargs={"public_slug": session.public_slug}),
        {"name": "No token", "email": "no-token@example.com"},
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_draft_session_is_not_publicly_visible(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    session = services.create_session(
        actor=organisation.created_by,
        organisation=organisation,
        title="Not yet open",
        prompt="Still being set up.",
    )
    client = APIClient()
    response = client.get(
        reverse("ideation:public-detail", kwargs={"public_slug": session.public_slug})
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_existing_participant_requires_its_current_token(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    session = services.create_session(
        actor=organisation.created_by,
        organisation=organisation,
        title="Ideathon",
        prompt="What should we try next?",
    )
    first, first_token = services.identify_participant(
        session=session, name="Femi", email="Femi@Example.com"
    )
    with pytest.raises(PermissionDenied):
        services.identify_participant(
            session=session,
            name="Attacker",
            email="femi@example.com",
        )
    second, second_token = services.identify_participant(
        session=session,
        name="Femi A.",
        email="femi@example.com",
        existing_token=first_token,
    )
    assert first.id == second.id
    assert SessionParticipant.objects.filter(session=session).count() == 1
    assert second.name == "Femi A."
    assert first_token == second_token
    assert services.participant_from_token(session=session, raw_token=first_token).id == first.id


@pytest.mark.django_db
def test_public_join_cannot_take_over_an_existing_email(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    session = services.create_session(
        actor=organisation.created_by,
        organisation=organisation,
        title="Ideathon",
        prompt="Ideas?",
    )
    services.open_session(actor=organisation.created_by, session=session)
    participant, original_token = services.identify_participant(
        session=session,
        name="Femi",
        email="femi@example.com",
    )
    client, csrf_token = _csrf_client()
    response = client.post(
        reverse("ideation:public-join", kwargs={"public_slug": session.public_slug}),
        {"name": "Attacker", "email": "femi@example.com"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert response.status_code == 403
    participant.refresh_from_db()
    assert participant.name == "Femi"
    assert (
        services.participant_from_token(
            session=session,
            raw_token=original_token,
        ).id
        == participant.id
    )


@pytest.mark.django_db
def test_cast_vote_is_idempotent_per_identity(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    session = services.create_session(
        actor=owner, organisation=organisation, title="Ideathon", prompt="Ideas?"
    )
    services.open_session(actor=owner, session=session)
    participant, _ = services.identify_participant(
        session=session, name="Kwame", email="kwame@example.com"
    )
    idea = services.submit_idea(session=session, participant=participant, title="Idea one")

    services.cast_vote(idea=idea, participant=participant)
    services.cast_vote(idea=idea, participant=participant)
    assert IdeaVote.objects.filter(idea=idea, participant=participant).count() == 1


@pytest.mark.django_db
def test_submission_and_voting_blocked_outside_open_status(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    session = services.create_session(
        actor=owner, organisation=organisation, title="Draft", prompt="Ideas?"
    )
    participant, _ = services.identify_participant(
        session=session, name="Kwame", email="kwame@example.com"
    )
    with pytest.raises(ValidationError):
        services.submit_idea(session=session, participant=participant, title="Too early")


@pytest.mark.django_db
def test_submission_deadline_and_team_policy_are_enforced_server_side(
    organisation_factory,
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    session = services.create_session(
        actor=owner,
        organisation=organisation,
        title="Closed round",
        prompt="Ideas?",
        submission_deadline=timezone.now() - timedelta(minutes=1),
    )
    services.open_session(actor=owner, session=session)
    participant, _ = services.identify_participant(
        session=session,
        name="Ada",
        email="ada@example.com",
    )
    with pytest.raises(ValidationError, match="deadline"):
        services.submit_idea(session=session, participant=participant, title="Late idea")

    session.submission_deadline = timezone.now() + timedelta(hours=1)
    session.save(update_fields=["submission_deadline", "updated_at"])
    with pytest.raises(ValidationError, match="Team submissions"):
        services.submit_idea(
            session=session,
            participant=participant,
            title="Hidden team",
            team_name="Bypass",
            team_members=[{"name": "Ada"}],
        )


@pytest.mark.django_db
def test_idea_requires_exactly_one_submitter_identity(organisation_factory, user_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    session = services.create_session(
        actor=organisation.created_by, organisation=organisation, title="S", prompt="P"
    )
    neither = Idea(session=session, title="No one submitted this")
    with pytest.raises(ValidationError):
        neither.full_clean()

    participant, _ = services.identify_participant(session=session, name="X", email="x@example.com")
    both = Idea(
        session=session,
        title="Two submitters",
        submitted_by_participant=participant,
        submitted_by_user=user_factory(),
    )
    with pytest.raises(ValidationError):
        both.full_clean()


@pytest.mark.django_db
def test_organiser_can_create_list_and_manage_sessions(api_client, organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    api_client.force_authenticate(owner)

    create = api_client.post(
        reverse("ideation:organisation-list-create", kwargs={"organisation_id": organisation.id}),
        {"title": "Q3 ideathon", "prompt": "How do we cut onboarding time in half?"},
        format="json",
    )
    assert create.status_code == 201
    session_id = create.json()["id"]

    listing = api_client.get(
        reverse("ideation:organisation-list-create", kwargs={"organisation_id": organisation.id})
    )
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["idea_count"] == 0

    opened = api_client.post(
        reverse("ideation:organiser-state", kwargs={"session_id": session_id}),
        {"action": "open"},
        format="json",
    )
    assert opened.status_code == 200
    assert opened.json()["status"] == "open"


@pytest.mark.django_db
def test_organiser_endpoints_are_tenant_isolated(api_client, organisation_factory, user_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    session = services.create_session(
        actor=organisation.created_by, organisation=organisation, title="S", prompt="P"
    )
    outsider = user_factory()
    api_client.force_authenticate(outsider)
    response = api_client.get(
        reverse("ideation:organiser-detail", kwargs={"session_id": session.id})
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_shortlist_and_promote_idea_to_real_decision_option(
    api_client, organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    session = services.create_session(
        actor=owner,
        organisation=organisation,
        decision=decision,
        title="Open to this decision",
        prompt="Ideas?",
    )
    services.open_session(actor=owner, session=session)
    participant, _ = services.identify_participant(
        session=session, name="Ada", email="ada@example.com"
    )
    idea = services.submit_idea(
        session=session,
        participant=participant,
        title="A promising option",
        description="Worth trying.",
    )

    api_client.force_authenticate(owner)
    shortlist = api_client.post(
        reverse("ideation:idea-shortlist", kwargs={"session_id": session.id, "idea_id": idea.id}),
        {"shortlisted": True},
        format="json",
    )
    assert shortlist.status_code == 200
    assert shortlist.json()["ideas"][0]["status"] == "shortlisted"

    promote = api_client.post(
        reverse("ideation:idea-promote", kwargs={"session_id": session.id, "idea_id": idea.id}),
        {"decision_id": str(decision.id)},
        format="json",
    )
    assert promote.status_code == 200
    assert promote.json()["ideas"][0]["status"] == "promoted"
    idea.refresh_from_db()
    assert idea.promoted_to_option is not None
    assert DecisionOption.objects.filter(
        id=idea.promoted_to_option_id, title="A promising option"
    ).exists()

    already_promoted = api_client.post(
        reverse("ideation:idea-promote", kwargs={"session_id": session.id, "idea_id": idea.id}),
        {"decision_id": str(decision.id)},
        format="json",
    )
    assert already_promoted.status_code == 400


@pytest.mark.django_db
def test_requested_amount_carries_from_idea_to_promoted_option(
    api_client, organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=owner,
        source_template_key="grant_round",
    )
    session = services.create_session(
        actor=owner,
        organisation=organisation,
        decision=decision,
        title="Round 1",
        prompt="Applications?",
    )
    services.open_session(actor=owner, session=session)
    participant, _ = services.identify_participant(
        session=session, name="Ada", email="ada@example.com"
    )
    idea = services.submit_idea(
        session=session,
        participant=participant,
        title="Community garden expansion",
        description="Expand the shared plots to a second neighbourhood.",
        requested_amount="15000.00",
    )
    assert idea.requested_amount == pytest.approx(15000.00)

    api_client.force_authenticate(owner)
    promote = api_client.post(
        reverse("ideation:idea-promote", kwargs={"session_id": session.id, "idea_id": idea.id}),
        {"decision_id": str(decision.id)},
        format="json",
    )
    assert promote.status_code == 200
    idea.refresh_from_db()
    option = DecisionOption.objects.get(id=idea.promoted_to_option_id)
    assert option.estimated_cost == pytest.approx(15000.00)


@pytest.mark.django_db
def test_public_session_exposes_decision_template_key_but_nothing_else(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=owner,
        title="Internal-only decision title",
        source_template_key="grant_round",
    )
    session = services.create_session(
        actor=owner,
        organisation=organisation,
        decision=decision,
        title="Open round",
        prompt="Applications?",
    )
    services.open_session(actor=owner, session=session)

    client, _ = _csrf_client()
    detail = client.get(
        reverse("ideation:public-detail", kwargs={"public_slug": session.public_slug})
    )
    assert detail.status_code == 200
    body = detail.json()
    assert body["decision_template_key"] == "grant_round"
    assert "Internal-only decision title" not in str(body)

    client, csrf_token = _csrf_client()
    join = client.post(
        reverse("ideation:public-join", kwargs={"public_slug": session.public_slug}),
        {"name": "Ife", "email": "ife@example.com"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    token = join.json()["participant_token"]
    submit = client.post(
        reverse("ideation:public-idea-create", kwargs={"public_slug": session.public_slug}),
        {"title": "Youth mentoring programme", "requested_amount": "5000.00"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
        HTTP_X_PARTICIPANT_TOKEN=token,
    )
    assert submit.status_code == 200
    assert submit.json()["ideas"][0]["requested_amount"] == "5000.00"


@pytest.mark.django_db
def test_public_session_decision_template_key_is_null_without_a_linked_decision(
    organisation_factory,
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    session = services.create_session(
        actor=organisation.created_by, organisation=organisation, title="S", prompt="P"
    )
    services.open_session(actor=organisation.created_by, session=session)

    client, _ = _csrf_client()
    detail = client.get(
        reverse("ideation:public-detail", kwargs={"public_slug": session.public_slug})
    )
    assert detail.json()["decision_template_key"] is None


@pytest.mark.django_db
def test_promote_rejects_a_decision_from_another_organisation(
    api_client, organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    other_organisation = organisation_factory()
    other_decision = decision_factory(workspace=other_organisation.workspaces.get(is_default=True))
    session = services.create_session(actor=owner, organisation=organisation, title="S", prompt="P")
    services.open_session(actor=owner, session=session)
    participant, _ = services.identify_participant(
        session=session, name="Ada", email="ada@example.com"
    )
    idea = services.submit_idea(session=session, participant=participant, title="Idea")

    api_client.force_authenticate(owner)
    response = api_client.post(
        reverse("ideation:idea-promote", kwargs={"session_id": session.id, "idea_id": idea.id}),
        {"decision_id": str(other_decision.id)},
        format="json",
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_only_creator_roles_can_create_a_session(organisation_factory, user_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    viewer = user_factory()
    Membership.objects.create(
        organisation=organisation,
        user=viewer,
        role=Membership.Role.VIEWER,
        status=Membership.Status.ACTIVE,
    )
    with pytest.raises(PermissionDenied):
        services.create_session(actor=viewer, organisation=organisation, title="S", prompt="P")


@pytest.mark.django_db
def test_idea_submission_carries_category(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    session = services.create_session(actor=owner, organisation=organisation, title="S", prompt="P")
    services.open_session(actor=owner, session=session)

    client, csrf_token = _csrf_client()
    join = client.post(
        reverse("ideation:public-join", kwargs={"public_slug": session.public_slug}),
        {"name": "Ada", "email": "ada@example.com"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    token = join.json()["participant_token"]

    submit = client.post(
        reverse("ideation:public-idea-create", kwargs={"public_slug": session.public_slug}),
        {"title": "Solar cold storage", "category": "Infrastructure"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
        HTTP_X_PARTICIPANT_TOKEN=token,
    )
    assert submit.status_code == 200
    assert submit.json()["ideas"][0]["category"] == "Infrastructure"


@pytest.mark.django_db
def test_public_comment_thread_on_an_idea(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    session = services.create_session(actor=owner, organisation=organisation, title="S", prompt="P")
    services.open_session(actor=owner, session=session)
    participant, _ = services.identify_participant(
        session=session, name="Ada", email="ada@example.com"
    )
    idea = services.submit_idea(session=session, participant=participant, title="Idea one")

    client, csrf_token = _csrf_client()
    join = client.post(
        reverse("ideation:public-join", kwargs={"public_slug": session.public_slug}),
        {"name": "Bayo", "email": "bayo@example.com"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    token = join.json()["participant_token"]

    comment = client.post(
        reverse(
            "ideation:public-idea-comment",
            kwargs={"public_slug": session.public_slug, "idea_id": idea.id},
        ),
        {"body": "This overlaps with last year's pilot, worth linking up."},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
        HTTP_X_PARTICIPANT_TOKEN=token,
    )
    assert comment.status_code == 200
    comments = comment.json()["ideas"][0]["comments"]
    assert len(comments) == 1
    assert comments[0]["submitted_by_participant"]["name"] == "Bayo"


@pytest.mark.django_db
def test_organiser_archives_and_unarchives_an_idea(api_client, organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    session = services.create_session(actor=owner, organisation=organisation, title="S", prompt="P")
    services.open_session(actor=owner, session=session)
    participant, _ = services.identify_participant(
        session=session, name="Ada", email="ada@example.com"
    )
    idea = services.submit_idea(session=session, participant=participant, title="Off-topic idea")

    api_client.force_authenticate(owner)
    archive = api_client.post(
        reverse("ideation:idea-archive", kwargs={"session_id": session.id, "idea_id": idea.id}),
        {"archived": True},
        format="json",
    )
    assert archive.status_code == 200
    assert archive.json()["ideas"][0]["status"] == "archived"

    unarchive = api_client.post(
        reverse("ideation:idea-archive", kwargs={"session_id": session.id, "idea_id": idea.id}),
        {"archived": False},
        format="json",
    )
    assert unarchive.status_code == 200
    assert unarchive.json()["ideas"][0]["status"] == "submitted"


@pytest.mark.django_db
def test_promote_without_decision_auto_creates_a_grant_round(
    api_client,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    session = services.create_session(
        actor=owner,
        organisation=organisation,
        title="Open ideathon",
        prompt="Ideas?",
    )
    services.open_session(actor=owner, session=session)
    participant, _ = services.identify_participant(
        session=session, name="Ada", email="ada@example.com"
    )
    idea = services.submit_idea(
        session=session,
        participant=participant,
        title="Solar cold storage co-op",
        description="Shared cold storage for smallholders.",
        requested_amount="8000.00",
    )

    api_client.force_authenticate(owner)
    promote = api_client.post(
        reverse("ideation:idea-promote", kwargs={"session_id": session.id, "idea_id": idea.id}),
        {},
        format="json",
    )

    assert promote.status_code == 200
    idea.refresh_from_db()
    option = DecisionOption.objects.get(id=idea.promoted_to_option_id)
    assert option.title == "Solar cold storage co-op"
    assert option.decision.source_template_key == "grant_round"
    assert option.decision.workspace == organisation.workspaces.get(is_default=True)


@pytest.mark.django_db
def test_promote_without_decision_fails_without_default_workspace(
    api_client,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    from apps.workspaces.models import Workspace

    organisation = organisation_factory()
    owner = organisation.created_by
    Workspace.objects.filter(organisation=organisation).update(is_default=False)
    session = services.create_session(actor=owner, organisation=organisation, title="S", prompt="P")
    assert session.default_workspace_id is None
    services.open_session(actor=owner, session=session)
    participant, _ = services.identify_participant(
        session=session, name="Ada", email="ada@example.com"
    )
    idea = services.submit_idea(session=session, participant=participant, title="Idea")

    with pytest.raises(ValidationError):
        services.promote_idea_to_decision(actor=owner, idea=idea, decision=None)


@pytest.mark.django_db
def test_idea_competition_template_is_registered():  # type: ignore[no-untyped-def]
    from apps.decisions.templates import template_for_key

    template = template_for_key("idea_competition")
    assert template is not None
    assert template.name == "Idea competition or hackathon"


@pytest.mark.django_db
def test_guardian_consent_required_for_declared_minor_when_session_requires_it(
    organisation_factory,
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    session = services.create_session(
        actor=owner,
        organisation=organisation,
        title="Regional student hackathon",
        prompt="Build something that helps your community.",
        requires_guardian_consent=True,
    )
    services.open_session(actor=owner, session=session)

    with pytest.raises(ValidationError):
        services.identify_participant(
            session=session,
            name="Tomiwa",
            email="tomiwa@example.com",
            age_bracket=SessionParticipant.AgeBracket.AGE_13_17,
        )

    with pytest.raises(ValidationError):
        services.identify_participant(
            session=session,
            name="Tomiwa",
            email="tomiwa@example.com",
            age_bracket=SessionParticipant.AgeBracket.AGE_13_17,
            guardian_name="Bisi Adewale",
            guardian_email="bisi@example.com",
            guardian_consent_given=False,
        )

    participant, _ = services.identify_participant(
        session=session,
        name="Tomiwa",
        email="tomiwa@example.com",
        age_bracket=SessionParticipant.AgeBracket.AGE_13_17,
        guardian_name="Bisi Adewale",
        guardian_email="bisi@example.com",
        guardian_consent_given=True,
    )
    assert participant.guardian_consent_given is True
    assert participant.guardian_consent_given_at is not None

    # An 18+ participant never needs guardian consent, even on a session that requires it.
    adult, _ = services.identify_participant(
        session=session,
        name="Kunle",
        email="kunle@example.com",
        age_bracket=SessionParticipant.AgeBracket.AGE_18_PLUS,
    )
    assert adult.guardian_consent_given is False


@pytest.mark.django_db
def test_guardian_consent_not_required_when_session_does_not_request_it(
    organisation_factory,
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    session = services.create_session(
        actor=organisation.created_by,
        organisation=organisation,
        title="Open ideathon",
        prompt="Ideas?",
    )
    participant, _ = services.identify_participant(
        session=session,
        name="Chika",
        email="chika@example.com",
        age_bracket=SessionParticipant.AgeBracket.UNDER_13,
    )
    assert participant.is_declared_minor is True
    assert participant.guardian_consent_given is False


@pytest.mark.django_db
def test_public_join_endpoint_enforces_guardian_consent(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    session = services.create_session(
        actor=owner,
        organisation=organisation,
        title="High school app challenge",
        prompt="What would make school life easier?",
        requires_guardian_consent=True,
    )
    services.open_session(actor=owner, session=session)

    client, csrf_token = _csrf_client()
    rejected = client.post(
        reverse("ideation:public-join", kwargs={"public_slug": session.public_slug}),
        {"name": "Ngozi", "email": "ngozi@example.com", "age_bracket": "age_13_17"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert rejected.status_code == 400

    accepted = client.post(
        reverse("ideation:public-join", kwargs={"public_slug": session.public_slug}),
        {
            "name": "Ngozi",
            "email": "ngozi@example.com",
            "school_name": "Lagos Community High",
            "age_bracket": "age_13_17",
            "guardian_name": "Uche Eze",
            "guardian_email": "uche@example.com",
            "guardian_consent_given": True,
        },
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert accepted.status_code == 201
    participant = SessionParticipant.objects.get(session=session, email="ngozi@example.com")
    assert participant.school_name == "Lagos Community High"
    assert participant.guardian_consent_given is True


@pytest.mark.django_db
def test_team_submission_carries_roster_and_is_public_safe(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    session = services.create_session(
        actor=owner,
        organisation=organisation,
        title="Campus hackathon",
        prompt="Build a tool that helps students collaborate.",
        team_submissions_enabled=True,
    )
    services.open_session(actor=owner, session=session)

    client, csrf_token = _csrf_client()
    join = client.post(
        reverse("ideation:public-join", kwargs={"public_slug": session.public_slug}),
        {"name": "Femi", "email": "femi@example.com"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    token = join.json()["participant_token"]

    submit = client.post(
        reverse("ideation:public-idea-create", kwargs={"public_slug": session.public_slug}),
        {
            "title": "StudyBuddy matcher",
            "team_name": "The Night Owls",
            "team_members": [
                {"name": "Femi", "role": "Team lead"},
                {"name": "Aisha", "role": "Designer"},
            ],
        },
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
        HTTP_X_PARTICIPANT_TOKEN=token,
    )
    assert submit.status_code == 200
    idea = submit.json()["ideas"][0]
    assert idea["team_name"] == "The Night Owls"
    assert [member["name"] for member in idea["team_members"]] == ["Femi", "Aisha"]
    assert idea["team_members"][0]["role"] == "Team lead"
    # Public payload never carries an email for a roster entry.
    assert "email" not in idea["team_members"][0]


@pytest.mark.django_db
def test_team_roster_is_capped_at_twelve_members(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    session = services.create_session(
        actor=owner,
        organisation=organisation,
        title="S",
        prompt="P",
        team_submissions_enabled=True,
    )
    services.open_session(actor=owner, session=session)

    client, csrf_token = _csrf_client()
    join = client.post(
        reverse("ideation:public-join", kwargs={"public_slug": session.public_slug}),
        {"name": "Femi", "email": "femi@example.com"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    token = join.json()["participant_token"]

    too_many = client.post(
        reverse("ideation:public-idea-create", kwargs={"public_slug": session.public_slug}),
        {"title": "Too big a team", "team_members": [{"name": f"Person {i}"} for i in range(13)]},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
        HTTP_X_PARTICIPANT_TOKEN=token,
    )
    assert too_many.status_code == 400


@pytest.mark.django_db
def test_organiser_view_shows_safeguarding_fields_public_view_does_not(
    api_client,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    session = services.create_session(
        actor=owner,
        organisation=organisation,
        title="Middle school robotics challenge",
        prompt="Design a robot that solves a real problem.",
        requires_guardian_consent=True,
    )
    services.open_session(actor=owner, session=session)
    participant, _ = services.identify_participant(
        session=session,
        name="Zainab",
        email="zainab@example.com",
        school_name="Riverside Middle School",
        age_bracket=SessionParticipant.AgeBracket.UNDER_13,
        guardian_name="Amina Bello",
        guardian_email="amina@example.com",
        guardian_consent_given=True,
    )
    services.submit_idea(session=session, participant=participant, title="Recycling sorter bot")

    client, _ = _csrf_client()
    public_detail = client.get(
        reverse("ideation:public-detail", kwargs={"public_slug": session.public_slug})
    )
    public_idea = public_detail.json()["ideas"][0]
    assert "submitter_school" not in public_idea
    assert "submitter_guardian_consent_given" not in public_idea

    api_client.force_authenticate(owner)
    organiser_detail = api_client.get(
        reverse("ideation:organiser-detail", kwargs={"session_id": session.id})
    )
    organiser_idea = organiser_detail.json()["ideas"][0]
    assert organiser_idea["submitter_school"] == "Riverside Middle School"
    assert organiser_idea["submitter_age_bracket"] == "under_13"
    assert organiser_idea["submitter_guardian_consent_given"] is True


@pytest.mark.django_db
def test_organiser_can_create_session_with_student_safeguards(
    api_client,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    api_client.force_authenticate(owner)

    create = api_client.post(
        reverse("ideation:organisation-list-create", kwargs={"organisation_id": organisation.id}),
        {
            "title": "State science fair",
            "prompt": "Present a project that addresses a real community need.",
            "requires_guardian_consent": True,
            "team_submissions_enabled": True,
        },
        format="json",
    )
    assert create.status_code == 201
    session = OpenSession.objects.get(id=create.json()["id"])
    assert session.requires_guardian_consent is True
    assert session.team_submissions_enabled is True


@pytest.mark.django_db
def test_public_feed_does_not_expose_application_review_details(
    api_client,
    organisation_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=owner,
        source_template_key="grant_round",
    )
    session = services.create_session(
        actor=owner,
        organisation=organisation,
        decision=decision,
        title="Grant round",
        prompt="Apply",
    )
    services.open_session(actor=owner, session=session)
    participant, _ = services.identify_participant(
        session=session,
        name="Ada",
        email="ada@example.com",
    )
    idea = services.submit_idea(
        session=session,
        participant=participant,
        title="Community garden",
        description="Expand access to shared growing space.",
    )
    option = services.promote_idea_to_decision(
        actor=owner,
        idea=idea,
        decision=decision,
    )
    set_eligibility(
        actor=owner,
        option=option,
        eligibility_status="eligible",
        eligibility_note="Internal due-diligence note",
    )
    set_outcome(
        actor=owner,
        option=option,
        outcome_status="funded",
        awarded_amount="500.00",
        outcome_note="Applicant-only outcome note",
    )

    client = APIClient()
    public = client.get(
        reverse("ideation:public-detail", kwargs={"public_slug": session.public_slug})
    )
    assert "application_status" not in public.json()["ideas"][0]
    assert "Internal due-diligence note" not in str(public.json())
    assert "Applicant-only outcome note" not in str(public.json())

    api_client.force_authenticate(owner)
    organiser = api_client.get(
        reverse("ideation:organiser-detail", kwargs={"session_id": session.id})
    )
    assert organiser.json()["ideas"][0]["application_status"]["eligibility_note"] == (
        "Internal due-diligence note"
    )
