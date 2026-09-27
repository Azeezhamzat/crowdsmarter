"""Preview-only retention reporting for safeguarded tenant deletion requests."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from django.utils import timezone

from .models import Organisation, OrganisationDeletionRequest


def retention_report(*, as_of: datetime | None = None) -> list[dict[str, Any]]:
    """Return deletion candidates and blockers without mutating customer data."""
    current_time = as_of or timezone.now()
    requests = OrganisationDeletionRequest.objects.filter(
        status=OrganisationDeletionRequest.Status.PENDING
    ).select_related("organisation", "requested_by")
    report: list[dict[str, Any]] = []
    for item in requests.order_by("earliest_deletion_at", "id"):
        blockers: list[str] = []
        if item.organisation.status != Organisation.Status.DEACTIVATED:
            blockers.append("organisation_is_active")
        due = item.earliest_deletion_at <= current_time
        report.append(
            {
                "request_id": str(item.id),
                "organisation_id": str(item.organisation_id),
                "organisation_name": item.organisation.name,
                "retention_days": item.organisation.retention_days,
                "earliest_deletion_at": item.earliest_deletion_at.isoformat(),
                "due": due,
                "eligible_for_manual_review": due and not blockers,
                "blockers": blockers,
            }
        )
    return report
