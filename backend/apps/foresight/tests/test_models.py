import pytest
from django.core.exceptions import ValidationError

from apps.foresight.models import Signal, Source


@pytest.mark.django_db
def test_source_requires_attributable_location(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    source = Source(
        organisation=organisation,
        title="Unattributed source",
        source_type=Source.SourceType.OTHER,
        created_by=organisation.created_by,
    )

    with pytest.raises(ValidationError):
        source.full_clean()


@pytest.mark.django_db
def test_signal_source_must_share_organisation(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    other = organisation_factory()
    source = Source.objects.create(
        organisation=other,
        title="Other tenant source",
        source_type=Source.SourceType.RESEARCH,
        source_url="https://example.com/research",
        created_by=other.created_by,
    )
    signal = Signal(
        organisation=organisation,
        source=source,
        title="Cross-tenant signal",
        summary="This signal attempts to use another tenant's source.",
        future_implication="Tenant isolation must prevent this relationship.",
        steep_category=Signal.SteepCategory.TECHNOLOGICAL,
        time_horizon=Signal.TimeHorizon.MEDIUM,
        maturity=Signal.Maturity.WEAK,
        impact=3,
        uncertainty=4,
        owner=organisation.created_by,
        created_by=organisation.created_by,
    )

    with pytest.raises(ValidationError):
        signal.full_clean()
