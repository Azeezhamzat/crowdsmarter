from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.organisations.models import Organisation, OrganisationDeletionRequest
from apps.organisations.retention import retention_report
from apps.organisations.tasks import report_due_retention_reviews


@pytest.mark.django_db
def test_retention_report_is_preview_only_and_flags_due_request(organisation_factory, capsys):  # type: ignore[no-untyped-def]
    organisation = organisation_factory(retention_days=60)
    Organisation.objects.filter(id=organisation.id).update(
        status=Organisation.Status.DEACTIVATED,
        deactivated_at=timezone.now() - timedelta(days=61),
        deactivated_by=organisation.created_by,
    )
    request = OrganisationDeletionRequest.objects.create(
        organisation=organisation,
        requested_by=organisation.created_by,
        reason="The owner approved a controlled tenant deletion review.",
        earliest_deletion_at=timezone.now() - timedelta(days=1),
    )

    rows = retention_report()

    assert rows[0]["request_id"] == str(request.id)
    assert rows[0]["eligible_for_manual_review"] is True
    assert OrganisationDeletionRequest.objects.filter(id=request.id).exists()
    call_command("retention_report", "--json")
    assert str(request.id) in capsys.readouterr().out
    assert Organisation.objects.filter(id=organisation.id).exists()
    assert report_due_retention_reviews.run() == 1
