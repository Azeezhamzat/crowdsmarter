import pytest
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.audit.models import AuditEvent
from apps.foresight.models import Signal, Source
from apps.foresight.services import (
    add_signal_to_watchlist,
    attach_source_file,
    create_signal,
    create_source,
    create_watchlist,
    link_signal_to_decision,
)
from apps.organisations.models import Membership


@pytest.mark.django_db
def test_contributor_builds_traceable_signal_workflow(
    user_factory, organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    contributor = user_factory()
    Membership.objects.create(
        organisation=organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
    )
    source = create_source(
        actor=contributor,
        organisation=organisation,
        title="Emerging field robotics report",
        source_type=Source.SourceType.RESEARCH,
        source_url="https://example.com/robotics",
        credibility=Source.Credibility.HIGH,
    )
    signal = create_signal(
        actor=contributor,
        organisation=organisation,
        source_id=source.id,
        title="Low-cost field robots are moving into smallholder markets",
        summary="New vendors are releasing lower-cost field robotics platforms.",
        future_implication="Labour models and technology-access assumptions may change.",
        steep_category=Signal.SteepCategory.TECHNOLOGICAL,
        time_horizon=Signal.TimeHorizon.MEDIUM,
        maturity=Signal.Maturity.EMERGING,
        polarity=Signal.Polarity.BOTH,
        impact=4,
        uncertainty=4,
    )
    watchlist = create_watchlist(
        actor=contributor,
        organisation=organisation,
        name="Agricultural automation",
        description="Monitor changes affecting field labour and automation.",
    )
    add_signal_to_watchlist(actor=contributor, watchlist=watchlist, signal_id=signal.id)

    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=organisation.created_by,
        title="Future field operations model",
    )
    link_signal_to_decision(
        actor=contributor,
        signal=signal,
        decision_id=decision.id,
        relevance="The signal changes assumptions about future labour availability.",
    )

    signal.refresh_from_db()
    assert signal.priority_score == 16
    assert signal.watchlists.filter(id=watchlist.id).exists()
    assert signal.decision_links.filter(decision=decision).exists()
    assert AuditEvent.objects.filter(organisation=organisation, action__startswith="foresight.").count() == 5


@pytest.mark.django_db
def test_private_source_attachment_records_hash_and_metadata(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    source = create_source(
        actor=organisation.created_by,
        organisation=organisation,
        title="Internal scanning note",
        source_type=Source.SourceType.INTERNAL,
        reference="Scanning note 11",
    )
    upload = SimpleUploadedFile(
        "signal-note.txt",
        b"Observed changes in field monitoring behaviour.",
        content_type="text/plain",
    )

    attachment = attach_source_file(
        actor=organisation.created_by,
        source=source,
        upload=upload,
    )

    assert attachment.size_bytes > 0
    assert len(attachment.sha256) == 64
    assert attachment.original_name == "signal-note.txt"


@pytest.mark.django_db
def test_viewer_cannot_create_signal(user_factory, organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    viewer = user_factory()
    Membership.objects.create(
        organisation=organisation,
        user=viewer,
        role=Membership.Role.VIEWER,
    )

    with pytest.raises(PermissionDenied):
        create_signal(
            actor=viewer,
            organisation=organisation,
            title="Not permitted",
            summary="Viewers cannot create signals.",
            future_implication="The service must enforce this outside the API.",
            steep_category=Signal.SteepCategory.SOCIAL,
            time_horizon=Signal.TimeHorizon.NEAR,
            maturity=Signal.Maturity.WEAK,
            impact=2,
            uncertainty=3,
        )
