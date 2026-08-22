"""Public applicant-portal API: magic-link request/consume, applications, progress reports."""

from __future__ import annotations

import re

import pytest
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.applicants.models import ApplicantAccount
from apps.decision_options.services import set_outcome
from apps.ideation import services as ideation_services
from apps.ideation.services import promote_idea_to_decision


def _csrf_client() -> tuple[APIClient, str]:
    client = APIClient(enforce_csrf_checks=True)
    csrf_token = client.get(reverse("accounts:csrf")).cookies["csrftoken"].value
    return client, csrf_token


def _extract_token(email_body: str) -> str:
    match = re.search(r"token=([^\s]+)", email_body)
    assert match is not None
    return match.group(1)


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_magic_link_request_and_consume_flow():  # type: ignore[no-untyped-def]
    client, csrf_token = _csrf_client()
    response = client.post(
        reverse("applicants:magic-link-request"),
        {"email": "amina@example.com", "name": "Amina"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert response.status_code == 202
    assert len(mail.outbox) == 1
    assert ApplicantAccount.objects.filter(email="amina@example.com").exists()

    raw_token = _extract_token(mail.outbox[0].body)
    consume = client.post(
        reverse("applicants:magic-link-consume"),
        {"token": raw_token},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert consume.status_code == 200
    assert consume.json()["email"] == "amina@example.com"
    applicant_token = consume.json()["applicant_token"]

    my_apps = client.get(
        reverse("applicants:my-applications"),
        HTTP_X_APPLICANT_TOKEN=applicant_token,
    )
    assert my_apps.status_code == 200
    assert my_apps.json()["applications"] == []


@pytest.mark.django_db
def test_my_applications_requires_token():  # type: ignore[no-untyped-def]
    client = APIClient()
    response = client.get(reverse("applicants:my-applications"))
    assert response.status_code == 403


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_progress_report_flow_end_to_end(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    session = ideation_services.create_session(
        actor=owner, organisation=organisation, title="Grants round", prompt="Fund it"
    )
    ideation_services.open_session(actor=owner, session=session)

    client, csrf_token = _csrf_client()
    client.post(
        reverse("applicants:magic-link-request"),
        {"email": "amina@example.com"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    raw_token = _extract_token(mail.outbox[-1].body)
    consume = client.post(
        reverse("applicants:magic-link-consume"),
        {"token": raw_token},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    applicant_token = consume.json()["applicant_token"]

    participant, _ = ideation_services.identify_participant(
        session=session, name="Amina", email="amina@example.com"
    )
    idea = ideation_services.submit_idea(
        session=session, participant=participant, title="Well project", description="Drill a community well."
    )

    from apps.decisions.services import create_decision
    from apps.workspaces.models import Workspace

    workspace = Workspace.objects.filter(organisation=organisation, is_default=True).first()
    decision = create_decision(actor=owner, workspace=workspace, title="Grants", purpose="p", template_key="grant_round")
    option = promote_idea_to_decision(actor=owner, idea=idea, decision=decision)
    set_outcome(actor=owner, option=option, outcome_status="funded", awarded_amount=500, outcome_note="")

    my_apps = client.get(
        reverse("applicants:my-applications"),
        HTTP_X_APPLICANT_TOKEN=applicant_token,
    )
    assert my_apps.status_code == 200
    applications = my_apps.json()["applications"]
    assert len(applications) == 1
    assert applications[0]["can_submit_progress_report"] is True

    report = client.post(
        reverse("applicants:progress-report-create", kwargs={"idea_id": idea.id}),
        {"body": "We drilled the well."},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
        HTTP_X_APPLICANT_TOKEN=applicant_token,
    )
    assert report.status_code == 201
    assert report.json()["applications"][0]["progress_reports"][0]["body"] == "We drilled the well."
