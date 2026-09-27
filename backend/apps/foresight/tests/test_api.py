import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.audit.models import AuditEvent
from apps.foresight.models import Source
from apps.foresight.services import create_source


@pytest.mark.django_db
def test_foresight_api_create_list_and_private_download(api_client, organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    api_client.force_authenticate(organisation.created_by)
    sources_url = reverse("foresight:sources", kwargs={"organisation_id": organisation.id})
    source_response = api_client.post(
        sources_url,
        {
            "title": "Government futures report",
            "source_type": "government",
            "source_url": "https://example.gov/futures",
            "reference": "",
            "credibility": "high",
        },
        format="json",
    )
    assert source_response.status_code == 201

    source_id = source_response.json()["id"]
    upload_url = reverse("foresight:source-attachment-upload", kwargs={"source_id": source_id})
    upload_response = api_client.post(
        upload_url,
        {
            "file": SimpleUploadedFile(
                "report.pdf", b"%PDF-1.4 simulated", content_type="application/pdf"
            )
        },
        format="multipart",
    )
    assert upload_response.status_code == 201
    download = api_client.get(
        reverse(
            "foresight:source-attachment-download",
            kwargs={"attachment_id": upload_response.json()["id"]},
        )
    )
    assert download.status_code == 200
    assert download["Cache-Control"] == "private, no-store"
    assert AuditEvent.objects.filter(
        organisation=organisation,
        action="foresight.source.attachment_downloaded",
        object_id=str(upload_response.json()["id"]),
    ).exists()

    signals_url = reverse("foresight:signals", kwargs={"organisation_id": organisation.id})
    signal_response = api_client.post(
        signals_url,
        {
            "source_id": source_id,
            "title": "Policy emphasis on anticipatory governance is increasing",
            "summary": "New public-sector guidance places more emphasis on strategic foresight.",
            "future_implication": "Organisations may need auditable foresight-to-decision practices.",
            "steep_category": "political",
            "time_horizon": "near",
            "maturity": "emerging",
            "polarity": "opportunity",
            "impact": 4,
            "uncertainty": 3,
        },
        format="json",
    )
    assert signal_response.status_code == 201
    assert api_client.get(signals_url).json()[0]["priority_score"] == 12


@pytest.mark.django_db
def test_foresight_api_is_tenant_isolated(api_client, user_factory, organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    api_client.force_authenticate(user_factory())

    assert (
        api_client.get(
            reverse("foresight:overview", kwargs={"organisation_id": organisation.id})
        ).status_code
        == 404
    )


@pytest.mark.django_db
def test_research_claim_api_tracks_evidence_decision_and_review_gate(
    api_client, organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    actor = organisation.created_by
    api_client.force_authenticate(actor)
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=actor,
        title="Choose a facilitation delivery model",
    )
    supporting = create_source(
        actor=actor,
        organisation=organisation,
        title="Independent participation evaluation",
        source_type=Source.SourceType.RESEARCH,
        source_url="https://example.org/evaluation",
        credibility=Source.Credibility.HIGH,
    )
    contrary = create_source(
        actor=actor,
        organisation=organisation,
        title="Implementation constraints report",
        source_type=Source.SourceType.GOVERNMENT,
        source_url="https://example.gov/constraints",
        credibility=Source.Credibility.HIGH,
    )

    claims_url = reverse("foresight:research-claims", kwargs={"organisation_id": organisation.id})
    create_response = api_client.post(
        claims_url,
        {
            "statement": "Hybrid facilitation improves access when offline input is preserved.",
            "state": "supported",
            "recommendation": "build",
            "relevance": "facilitation",
            "evidence_summary": "Two independent sources address access and delivery constraints.",
            "limitations": "No CrowdSmarter outcome study exists yet.",
            "reversal_conditions": "Remove the workflow if pilots show no access improvement.",
            "expected_outcome": "More participant input reaches the decision record.",
            "authority_score": 3,
            "directness_score": 3,
            "recency_score": 2,
            "triangulation_score": 2,
            "linked_decision_id": str(decision.id),
            "review_due_on": "2026-12-01",
            "lifecycle_status": "active",
        },
        format="json",
    )
    assert create_response.status_code == 201
    claim_id = create_response.json()["id"]
    assert create_response.json()["evidence_score"] == 10
    assert create_response.json()["linked_decision"]["id"] == str(decision.id)
    assert create_response.json()["last_reviewed_at"] is not None

    link_url = reverse("foresight:research-claim-sources", kwargs={"claim_id": claim_id})
    support_response = api_client.post(
        link_url,
        {
            "source_id": str(supporting.id),
            "relationship": "supports",
            "note": "Directly evaluates the participation mechanism.",
        },
        format="json",
    )
    assert support_response.status_code == 200
    contrary_response = api_client.post(
        link_url,
        {
            "source_id": str(contrary.id),
            "relationship": "contradicts",
            "note": "Documents delivery constraints that may limit the effect.",
        },
        format="json",
    )
    assert contrary_response.status_code == 200
    assert contrary_response.json()["support_count"] == 1
    assert contrary_response.json()["contrary_count"] == 1
    assert len(contrary_response.json()["source_links"]) == 2

    detail_url = reverse("foresight:research-claim-detail", kwargs={"claim_id": claim_id})
    patch_response = api_client.patch(
        detail_url,
        {"recommendation": "monitor", "triangulation_score": 1},
        format="json",
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["recommendation"] == "monitor"
    assert patch_response.json()["evidence_score"] == 9

    overview = api_client.get(
        reverse("foresight:overview", kwargs={"organisation_id": organisation.id})
    ).json()
    assert overview["claim_count"] == 1
    assert overview["claims_with_evidence_gaps"] == 0
    assert (
        AuditEvent.objects.filter(
            organisation=organisation,
            action="foresight.research_claim.source_linked",
            object_id=claim_id,
        ).count()
        == 2
    )


@pytest.mark.django_db
def test_research_claim_rejects_cross_tenant_source(api_client, organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    other = organisation_factory()
    actor = organisation.created_by
    foreign_source = create_source(
        actor=other.created_by,
        organisation=other,
        title="Other tenant source",
        source_type=Source.SourceType.INTERNAL,
        reference="Other-1",
    )
    api_client.force_authenticate(actor)
    claim = api_client.post(
        reverse("foresight:research-claims", kwargs={"organisation_id": organisation.id}),
        {"statement": "A tenant-isolated claim", "lifecycle_status": "active"},
        format="json",
    ).json()

    response = api_client.post(
        reverse("foresight:research-claim-sources", kwargs={"claim_id": claim["id"]}),
        {"source_id": str(foreign_source.id), "relationship": "supports"},
        format="json",
    )

    assert response.status_code == 400
