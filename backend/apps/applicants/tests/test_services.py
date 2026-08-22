"""Applicant identity, cross-round application listing, and progress reports."""

from __future__ import annotations

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from apps.applicants import services
from apps.applicants.models import ApplicantAccount, MagicLinkToken
from apps.ideation import services as ideation_services


@pytest.mark.django_db
def test_request_magic_link_creates_account_once(organisation_factory):  # type: ignore[no-untyped-def]
    account, raw_token = services.request_magic_link(email="Amina@Example.com ", name="Amina")
    assert account.email == "amina@example.com"
    assert account.email_verified_at is None
    assert MagicLinkToken.objects.filter(account=account).count() == 1

    account2, raw_token2 = services.request_magic_link(email="amina@example.com")
    assert account2.id == account.id
    assert raw_token2 != raw_token
    assert MagicLinkToken.objects.filter(account=account).count() == 2


@pytest.mark.django_db
def test_consume_magic_link_verifies_email_and_issues_portal_token():  # type: ignore[no-untyped-def]
    account, raw_token = services.request_magic_link(email="amina@example.com")
    verified_account, portal_token = services.consume_magic_link(raw_token=raw_token)
    assert verified_account.id == account.id
    assert verified_account.email_verified_at is not None
    assert portal_token

    resolved = services.applicant_account_from_portal_token(raw_token=portal_token)
    assert resolved.id == account.id


@pytest.mark.django_db
def test_consume_magic_link_rejects_reuse_and_expiry():  # type: ignore[no-untyped-def]
    account, raw_token = services.request_magic_link(email="amina@example.com")
    services.consume_magic_link(raw_token=raw_token)
    with pytest.raises(PermissionDenied):
        services.consume_magic_link(raw_token=raw_token)

    token = MagicLinkToken.objects.filter(account=account).exclude(consumed_at__isnull=False).first()
    _, raw_token2 = services.request_magic_link(email="amina@example.com")
    stale = MagicLinkToken.objects.get(account=account, consumed_at__isnull=True)
    stale.expires_at = timezone.now() - timezone.timedelta(minutes=1)
    stale.save(update_fields=["expires_at"])
    with pytest.raises(PermissionDenied):
        services.consume_magic_link(raw_token=raw_token2)


@pytest.mark.django_db
def test_identify_participant_links_verified_applicant_account(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    session = ideation_services.create_session(
        actor=owner,
        organisation=organisation,
        title="Community grants round",
        prompt="What should we fund this quarter?",
    )
    ideation_services.open_session(actor=owner, session=session)

    account, raw_token = services.request_magic_link(email="amina@example.com", name="Amina")
    services.consume_magic_link(raw_token=raw_token)

    participant, _ = ideation_services.identify_participant(
        session=session, name="Amina", email="amina@example.com"
    )
    assert participant.account_id == account.id


@pytest.mark.django_db
def test_applications_for_account_spans_sessions(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    session1 = ideation_services.create_session(
        actor=owner, organisation=organisation, title="Round one", prompt="Prompt one"
    )
    session2 = ideation_services.create_session(
        actor=owner, organisation=organisation, title="Round two", prompt="Prompt two"
    )
    ideation_services.open_session(actor=owner, session=session1)
    ideation_services.open_session(actor=owner, session=session2)

    account, raw_token = services.request_magic_link(email="amina@example.com")
    services.consume_magic_link(raw_token=raw_token)

    participant1, _ = ideation_services.identify_participant(
        session=session1, name="Amina", email="amina@example.com"
    )
    participant2, _ = ideation_services.identify_participant(
        session=session2, name="Amina", email="amina@example.com"
    )
    ideation_services.submit_idea(session=session1, participant=participant1, title="Idea one")
    ideation_services.submit_idea(session=session2, participant=participant2, title="Idea two")

    applications = list(services.applications_for_account(account=account))
    assert {idea.title for idea in applications} == {"Idea one", "Idea two"}


@pytest.mark.django_db
def test_submit_progress_report_requires_funded_ownership(organisation_factory):  # type: ignore[no-untyped-def]
    from apps.decision_options.services import set_outcome
    from apps.ideation.services import promote_idea_to_decision, shortlist_idea

    organisation = organisation_factory()
    owner = organisation.created_by
    session = ideation_services.create_session(
        actor=owner,
        organisation=organisation,
        title="Grants round",
        prompt="Fund community projects",
    )
    ideation_services.open_session(actor=owner, session=session)

    account, raw_token = services.request_magic_link(email="amina@example.com")
    services.consume_magic_link(raw_token=raw_token)
    participant, _ = ideation_services.identify_participant(
        session=session, name="Amina", email="amina@example.com"
    )
    idea = ideation_services.submit_idea(
        session=session, participant=participant, title="Water project", description="Build a well."
    )

    from apps.decisions.services import create_decision
    from apps.workspaces.models import Workspace

    workspace = Workspace.objects.filter(organisation=organisation, is_default=True).first()
    decision = create_decision(actor=owner, workspace=workspace, title="Grants", purpose="p", template_key="grant_round")

    with pytest.raises(ValidationError):
        services.submit_progress_report(account=account, idea=idea, body="Update")

    option = promote_idea_to_decision(actor=owner, idea=idea, decision=decision)
    idea.refresh_from_db()
    with pytest.raises(ValidationError):
        services.submit_progress_report(account=account, idea=idea, body="Update")

    set_outcome(actor=owner, option=option, outcome_status="funded", awarded_amount=500, outcome_note="")
    idea.refresh_from_db()
    report = services.submit_progress_report(account=account, idea=idea, body="We started the well.")
    assert report.idea_id == idea.id
    assert report.account_id == account.id

    other_account, other_token = services.request_magic_link(email="other@example.com")
    services.consume_magic_link(raw_token=other_token)
    with pytest.raises(PermissionDenied):
        services.submit_progress_report(account=other_account, idea=idea, body="Not mine")
