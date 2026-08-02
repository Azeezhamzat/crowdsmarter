import pytest
from django.core.exceptions import ValidationError

from apps.evidence.models import Evidence


@pytest.mark.django_db
def test_evidence_requires_attributable_source(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    item = Evidence(
        organisation=decision.organisation,
        decision=decision,
        title="Unattributed claim",
        summary="A claim without any reference is not auditable.",
        source_type=Evidence.SourceType.OTHER,
        stance=Evidence.Stance.CONTEXT,
        created_by=decision.owner,
    )

    with pytest.raises(ValidationError):
        item.full_clean()


@pytest.mark.django_db
def test_evidence_option_must_belong_to_decision(decision_factory):  # type: ignore[no-untyped-def]
    from apps.decision_options.models import DecisionOption

    decision = decision_factory()
    other_decision = decision_factory()
    option = DecisionOption.objects.create(
        organisation=other_decision.organisation,
        decision=other_decision,
        title="Other decision option",
        description="This option belongs elsewhere.",
        proposed_by=other_decision.owner,
        created_by=other_decision.owner,
    )
    item = Evidence(
        organisation=decision.organisation,
        decision=decision,
        option=option,
        title="Cross-decision evidence",
        summary="This relationship must be rejected.",
        source_type=Evidence.SourceType.INTERNAL_DATA,
        source_reference="Internal dataset 12",
        stance=Evidence.Stance.SUPPORTS,
        created_by=decision.owner,
    )

    with pytest.raises(ValidationError):
        item.full_clean()
