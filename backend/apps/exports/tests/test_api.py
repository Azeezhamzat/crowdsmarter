import io
import json
import zipfile
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.invitations.models import OrganisationInvitation
from apps.organisations.models import Membership


@pytest.mark.django_db
def test_owner_can_download_complete_export_without_secrets(
    api_client, user_factory, organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory(email="owner@example.com")
    organisation = organisation_factory(owner=owner)
    decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    OrganisationInvitation.objects.create(
        organisation=organisation,
        email="invitee@example.com",
        role=Membership.Role.CONTRIBUTOR,
        token_digest="a" * 64,
        invited_by=owner,
        expires_at=timezone.now() + timedelta(days=7),
    )
    api_client.force_authenticate(owner)

    response = api_client.get(
        reverse("exports:organisation-complete", kwargs={"organisation_id": organisation.id})
    )
    assert response.status_code == 200
    assert response["Content-Type"] == "application/zip"
    archive_bytes = bytes(response.content)
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        names = set(archive.namelist())
        assert "manifest.json" in names
        assert "json/decisions.json" in names
        assert "csv/evidence.csv" in names
        assert "json/invitations.json" in names
        assert "token_digest" not in archive.read("json/invitations.json").decode()
        assert "password" not in archive.read("json/users.json").decode()


@pytest.mark.django_db
def test_contributor_cannot_download_complete_organisation_export(
    api_client, user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    contributor = user_factory()
    organisation = organisation_factory(owner=owner)
    Membership.objects.create(
        organisation=organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
    )
    api_client.force_authenticate(contributor)
    response = api_client.get(
        reverse("exports:organisation-complete", kwargs={"organisation_id": organisation.id})
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_visible_member_can_download_decision_dossier(
    api_client, user_factory, decision_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory(
        decision_question="Which option should we select?",
        purpose="Preserve the complete reasoning record.",
    )
    viewer = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=viewer,
        role=Membership.Role.VIEWER,
    )
    api_client.force_authenticate(viewer)
    response = api_client.get(
        reverse("exports:decision-dossier", kwargs={"decision_id": decision.id})
    )
    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(bytes(response.content))) as archive:
        assert "summary.txt" in archive.namelist()
        assert "json/decision.json" in archive.namelist()
        assert decision.title in archive.read("summary.txt").decode()


@pytest.mark.django_db
def test_outsider_cannot_discover_decision_through_export(
    api_client, user_factory, decision_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    outsider = user_factory()
    api_client.force_authenticate(outsider)
    response = api_client.get(
        reverse("exports:decision-dossier", kwargs={"decision_id": decision.id})
    )
    assert response.status_code == 404

@pytest.mark.django_db
def test_organisation_export_contains_foresight_metadata_and_private_file(
    api_client, organisation_factory
):  # type: ignore[no-untyped-def]
    from django.core.files.uploadedfile import SimpleUploadedFile

    from apps.foresight.services import attach_source_file, create_source

    organisation = organisation_factory()
    owner = organisation.created_by
    source = create_source(
        actor=owner,
        organisation=organisation,
        title="Emerging regulation report",
        source_type="government",
        reference="REG-2026-01",
        credibility="high",
        credibility_rationale="Published by the responsible regulator.",
    )
    attachment = attach_source_file(
        actor=owner,
        source=source,
        upload=SimpleUploadedFile(
            "regulation.pdf",
            b"%PDF-1.4 simulated regulation",
            content_type="application/pdf",
        ),
    )
    api_client.force_authenticate(owner)

    response = api_client.get(
        reverse("exports:organisation-complete", kwargs={"organisation_id": organisation.id})
    )

    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(bytes(response.content))) as archive:
        names = set(archive.namelist())
        assert "json/foresight_sources.json" in names
        assert "json/foresight_source_attachments.json" in names
        assert any(
            name.startswith(f"attachments/foresight/{source.id}/{attachment.id}.")
            for name in names
        )

@pytest.mark.django_db
def test_organisation_export_preserves_systems_mapping_and_feedback_loop_order(
    api_client, organisation_factory
):  # type: ignore[no-untyped-def]
    from apps.foresight.mapping_services import (
        create_canvas,
        create_driver,
        create_feedback_loop,
    )

    organisation = organisation_factory()
    owner = organisation.created_by
    canvas = create_canvas(
        actor=owner,
        organisation=organisation,
        title="Adaptive capacity system",
        focal_question="How does adaptive capacity reinforce future resilience?",
        scope="The organisation and its implementation ecosystem.",
        horizon_year=2035,
    )
    capability = create_driver(
        actor=owner,
        canvas=canvas,
        title="Internal adaptive capability",
        description="Capability affects the speed and quality of organisational adaptation.",
        driver_type="driver",
        steep_category="social",
        impact=4,
        uncertainty=3,
    )
    confidence = create_driver(
        actor=owner,
        canvas=canvas,
        title="Stakeholder confidence",
        description="Confidence influences willingness to invest in further adaptation.",
        driver_type="driver",
        steep_category="economic",
        impact=4,
        uncertainty=4,
    )
    loop = create_feedback_loop(
        actor=owner,
        canvas=canvas,
        name="Adaptive confidence loop",
        description="Capability builds confidence, which enables further capability investment.",
        loop_type="reinforcing",
        driver_ids=[confidence.id, capability.id],
        rationale="The loop captures the team's explicit interpretation of the system.",
    )
    api_client.force_authenticate(owner)

    response = api_client.get(
        reverse(
            "exports:organisation-complete",
            kwargs={"organisation_id": organisation.id},
        )
    )

    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(bytes(response.content))) as archive:
        names = set(archive.namelist())
        assert "json/foresight_canvases.json" in names
        assert "json/foresight_drivers.json" in names
        assert "json/foresight_feedback_loops.json" in names
        assert "json/foresight_feedback_loop_drivers.json" in names
        links = json.loads(
            archive.read("json/foresight_feedback_loop_drivers.json").decode()
        )
        ordered = sorted(
            (item for item in links if item["feedback_loop"] == str(loop.id)),
            key=lambda item: item["position"],
        )
        assert [item["driver"] for item in ordered] == [
            str(confidence.id),
            str(capability.id),
        ]
