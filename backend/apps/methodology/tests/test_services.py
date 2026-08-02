import pytest

from apps.decisions.services import create_decision
from apps.methodology.models import DecisionMethodUsage
from apps.methodology.services import approve_method_version, create_method


@pytest.mark.django_db
def test_approved_method_can_start_decision_without_predeciding_outcome(decision_factory):  # type: ignore[no-untyped-def]
    baseline = decision_factory()
    owner = baseline.owner
    method = create_method(
        actor=owner,
        organisation=baseline.organisation,
        name="Evidence-balanced choice",
        summary="A governed prompt set that does not select an outcome.",
        question_prompt="State the choice.",
        purpose_prompt="State the intended value.",
        context_prompt="Describe the context.",
        scope_prompt="Define the scope.",
        contribution_prompt="Request balanced contributions.",
        required_fields=["decision_question", "purpose"],
        checklist=["Challenging evidence is represented."],
    )
    version = method.versions.get(version=1)
    approve_method_version(actor=owner, version=version)

    decision = create_decision(
        actor=owner,
        workspace=baseline.workspace,
        title="Choose a monitoring approach",
        decision_question="Which approach should be piloted?",
        method_version_id=version.id,
        template_key="blank",
    )

    assert decision.source_method_version_id == version.id
    assert decision.status == "draft"
    assert not hasattr(decision, "selected_option")
    assert DecisionMethodUsage.objects.filter(decision=decision, applied_by=owner).exists()
