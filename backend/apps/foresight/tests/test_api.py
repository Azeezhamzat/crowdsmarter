from apps.audit.models import AuditEvent

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse


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
        {"file": SimpleUploadedFile("report.pdf", b"%PDF-1.4 simulated", content_type="application/pdf")},
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

    assert api_client.get(
        reverse("foresight:overview", kwargs={"organisation_id": organisation.id})
    ).status_code == 404
