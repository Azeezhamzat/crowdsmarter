import pytest
from django.core.exceptions import PermissionDenied

from apps.decision_options.services import create_option
from apps.organisations.models import Membership
from apps.participants.models import ConflictOfInterest, Participant
from apps.participants.services import declare_conflict

from apps.evaluations.models import EvaluationRound, PrioritisationPortfolio
from apps.evaluations.services import (
    add_candidate,
    add_portfolio_criterion,
    create_criterion,
    create_exercise,
    create_minority_report,
    create_portfolio,
    create_round,
    evaluation_results,
    portfolio_recommendation,
    save_portfolio_assessment,
    save_submission,
    transition_round,
    update_portfolio,
)


@pytest.mark.django_db
def test_blind_scorecard_reveals_weighted_results_and_preserves_minority_report(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    contributor = user_factory(email="contributor@example.com")
    Membership.objects.create(
        organisation=organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=owner,
        title="Choose a regional adaptation programme",
    )
    Participant.objects.create(
        organisation=organisation,
        decision=decision,
        user=contributor,
        role=Participant.Role.CONTRIBUTOR,
        added_by=owner,
    )
    distributed = create_option(
        actor=owner,
        decision=decision,
        title="Distributed programme",
        description="Fund locally governed adaptation projects.",
    )
    central = create_option(
        actor=owner,
        decision=decision,
        title="Central programme",
        description="Deliver one centrally managed programme.",
    )
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Independent option scorecard",
        purpose="Compare value and delivery risk before authority finalises the decision.",
        method="scorecard",
        anonymity="peer_anonymous",
        blind_results_until_close=True,
        quorum_count=2,
        approval_threshold=60,
        objection_threshold=20,
    )
    value = create_criterion(
        actor=owner,
        exercise=exercise,
        title="Strategic value",
        description="Expected contribution to the decision purpose.",
        weight=3,
        scale_min=1,
        scale_max=5,
        higher_is_better=True,
        order=0,
    )
    risk = create_criterion(
        actor=owner,
        exercise=exercise,
        title="Delivery risk",
        description="Implementation difficulty and exposure.",
        weight=1,
        scale_min=1,
        scale_max=5,
        higher_is_better=False,
        order=1,
    )
    round_item = create_round(actor=owner, exercise=exercise, title="Round one")
    transition_round(actor=owner, round=round_item, status=EvaluationRound.Status.OPEN)

    save_submission(
        actor=owner,
        round=round_item,
        confidence=4,
        overall_rationale="Distributed delivery offers stronger local ownership.",
        responses=[
            {"option_id": distributed.id, "criterion_id": value.id, "score": 5},
            {"option_id": distributed.id, "criterion_id": risk.id, "score": 2},
            {"option_id": central.id, "criterion_id": value.id, "score": 3},
            {"option_id": central.id, "criterion_id": risk.id, "score": 4},
        ],
    )
    save_submission(
        actor=contributor,
        round=round_item,
        confidence=3,
        overall_rationale="The distributed option is more resilient if coordination is funded.",
        responses=[
            {"option_id": distributed.id, "criterion_id": value.id, "score": 4},
            {"option_id": distributed.id, "criterion_id": risk.id, "score": 3},
            {"option_id": central.id, "criterion_id": value.id, "score": 2},
            {"option_id": central.id, "criterion_id": risk.id, "score": 3},
        ],
    )

    assert evaluation_results(round=round_item, viewer=owner)["hidden"] is True
    transition_round(
        actor=owner,
        round=round_item,
        status=EvaluationRound.Status.CLOSED,
        feedback_summary="Participants agreed on value but differed about coordination risk.",
    )
    round_item.refresh_from_db()
    result = evaluation_results(round=round_item, viewer=owner)
    assert result["hidden"] is False
    assert result["quorum_met"] is True
    assert result["options"][0]["option_id"] == str(distributed.id)
    assert result["criterion_sensitivity"]

    report = create_minority_report(
        actor=contributor,
        exercise=exercise,
        round_id=round_item.id,
        title="Conditions for the central option",
        analysis="Central delivery could outperform if local administrative capacity is unavailable.",
        recommendation="Retain a central fallback trigger in the implementation plan.",
    )
    assert report.author == contributor
    assert exercise.minority_reports.count() == 1


@pytest.mark.django_db
def test_conflicted_reviewer_response_excluded_from_scorecard_results(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    contributor = user_factory(email="contributor@example.com")
    Membership.objects.create(
        organisation=organisation, user=contributor, role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True), owner=owner,
        title="Grant round",
    )
    contributor_participant = Participant.objects.create(
        organisation=organisation, decision=decision, user=contributor,
        role=Participant.Role.CONTRIBUTOR, added_by=owner,
    )
    conflicted_option = create_option(
        actor=owner, decision=decision, title="Applicant with a conflict", description="Desc.",
    )
    clean_option = create_option(
        actor=owner, decision=decision, title="Applicant without a conflict", description="Desc.",
    )
    declare_conflict(
        actor=contributor, participant=contributor_participant,
        scope=ConflictOfInterest.Scope.OPTION, option=conflicted_option,
        reason="I sit on their board.",
    )
    exercise = create_exercise(
        actor=owner, decision=decision, owner_id=owner.id,
        title="Reviewer scorecard", purpose="Score applications.", method="scorecard",
        quorum_count=1,
    )
    value = create_criterion(
        actor=owner, exercise=exercise, title="Impact", description="Expected impact.",
        weight=1, scale_min=1, scale_max=5, higher_is_better=True, order=0,
    )
    round_item = create_round(actor=owner, exercise=exercise, title="Round one")
    transition_round(actor=owner, round=round_item, status=EvaluationRound.Status.OPEN)

    save_submission(
        actor=contributor, round=round_item, confidence=4, overall_rationale="Scored both.",
        responses=[
            {"option_id": conflicted_option.id, "criterion_id": value.id, "score": 5},
            {"option_id": clean_option.id, "criterion_id": value.id, "score": 3},
        ],
    )
    transition_round(actor=owner, round=round_item, status=EvaluationRound.Status.CLOSED)
    round_item.refresh_from_db()

    result = evaluation_results(round=round_item, viewer=owner)
    rows = {row["option_id"]: row for row in result["options"]}

    assert str(clean_option.id) in rows
    assert rows[str(clean_option.id)]["excluded_response_count"] == 0
    # The conflicted reviewer's only response to conflicted_option is excluded,
    # so it never accumulates a score and drops out of the results entirely.
    assert str(conflicted_option.id) not in rows


@pytest.mark.django_db
def test_scorecard_result_reports_dispersion_and_disagreement_label(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    first_evaluator = user_factory(email="first@example.com")
    second_evaluator = user_factory(email="second@example.com")
    for user in (first_evaluator, second_evaluator):
        Membership.objects.create(
            organisation=organisation, user=user,
            role=Membership.Role.CONTRIBUTOR, status=Membership.Status.ACTIVE,
        )
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True), owner=owner,
        title="Choose a rollout approach",
    )
    for user in (owner, first_evaluator, second_evaluator):
        Participant.objects.get_or_create(
            organisation=organisation, decision=decision, user=user,
            defaults={"role": Participant.Role.CONTRIBUTOR, "added_by": owner},
        )
    contested = create_option(actor=owner, decision=decision, title="Contested option", description="Divides opinion.")
    agreed = create_option(actor=owner, decision=decision, title="Agreed option", description="Everyone agrees.")
    exercise = create_exercise(
        actor=owner, decision=decision, owner_id=owner.id,
        title="Dispersion test scorecard", purpose="Check dispersion reporting.",
        method="scorecard", anonymity="attributed", blind_results_until_close=False,
        quorum_count=2, approval_threshold=60, objection_threshold=20,
    )
    value = create_criterion(
        actor=owner, exercise=exercise, title="Value", description="Expected value.",
        weight=1, scale_min=1, scale_max=5, higher_is_better=True, order=0,
    )
    round_item = create_round(actor=owner, exercise=exercise)
    transition_round(actor=owner, round=round_item, status=EvaluationRound.Status.OPEN)

    save_submission(
        actor=owner, confidence=5, overall_rationale="Strong preference.", round=round_item,
        responses=[
            {"option_id": contested.id, "criterion_id": value.id, "score": 5},
            {"option_id": agreed.id, "criterion_id": value.id, "score": 3},
        ],
    )
    save_submission(
        actor=first_evaluator, confidence=5, overall_rationale="Opposite preference.", round=round_item,
        responses=[
            {"option_id": contested.id, "criterion_id": value.id, "score": 1},
            {"option_id": agreed.id, "criterion_id": value.id, "score": 3},
        ],
    )
    save_submission(
        actor=second_evaluator, confidence=5, overall_rationale="Also agrees.", round=round_item,
        responses=[
            {"option_id": contested.id, "criterion_id": value.id, "score": 3},
            {"option_id": agreed.id, "criterion_id": value.id, "score": 3},
        ],
    )

    result = evaluation_results(round=round_item, viewer=owner)
    by_option = {row["option_id"]: row for row in result["options"]}

    contested_row = by_option[str(contested.id)]
    assert contested_row["disagreement"] == "high"
    assert contested_row["score_stdev"] > 0
    assert contested_row["score_min"] == 0
    assert contested_row["score_max"] == 100

    agreed_row = by_option[str(agreed.id)]
    assert agreed_row["disagreement"] == "low"
    assert agreed_row["score_stdev"] == 0


@pytest.mark.django_db
def test_tornado_orders_criteria_by_impact_on_the_leader(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True), owner=owner,
        title="Choose a delivery model",
    )
    leader = create_option(actor=owner, decision=decision, title="Leading option", description="Currently ahead.")
    other = create_option(actor=owner, decision=decision, title="Other option", description="Currently behind.")
    exercise = create_exercise(
        actor=owner, decision=decision, owner_id=owner.id,
        title="Tornado test scorecard", purpose="Check tornado ordering.",
        method="scorecard", anonymity="attributed", blind_results_until_close=False,
        quorum_count=1, approval_threshold=60, objection_threshold=20,
    )
    heavy = create_criterion(
        actor=owner, exercise=exercise, title="Heavily weighted",
        description="A criterion with a large weight.", weight=3,
        scale_min=1, scale_max=5, higher_is_better=True, order=0,
    )
    light = create_criterion(
        actor=owner, exercise=exercise, title="Lightly weighted",
        description="A criterion with a small weight.", weight=1,
        scale_min=1, scale_max=5, higher_is_better=True, order=1,
    )
    round_item = create_round(actor=owner, exercise=exercise)
    transition_round(actor=owner, round=round_item, status=EvaluationRound.Status.OPEN)
    save_submission(
        actor=owner, confidence=4, overall_rationale="", round=round_item,
        responses=[
            {"option_id": leader.id, "criterion_id": heavy.id, "score": 5},
            {"option_id": leader.id, "criterion_id": light.id, "score": 1},
            {"option_id": other.id, "criterion_id": heavy.id, "score": 1},
            {"option_id": other.id, "criterion_id": light.id, "score": 5},
        ],
    )

    result = evaluation_results(round=round_item, viewer=owner)
    assert result["options"][0]["option_id"] == str(leader.id)
    tornado = result["tornado"]
    assert tornado["option_id"] == str(leader.id)
    assert tornado["option_title"] == "Leading option"
    assert len(tornado["criteria"]) == 2
    assert tornado["criteria"][0]["criterion_id"] == str(heavy.id)
    assert tornado["criteria"][0]["impact"] >= tornado["criteria"][1]["impact"]


@pytest.mark.django_db
def test_uncertainty_narrative_flags_an_unstable_ranking(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True), owner=owner,
        title="Choose between near-tied options",
    )
    first = create_option(actor=owner, decision=decision, title="First option", description="One profile.")
    second = create_option(actor=owner, decision=decision, title="Second option", description="A different profile.")
    exercise = create_exercise(
        actor=owner, decision=decision, owner_id=owner.id,
        title="Near-tie scorecard", purpose="Check narrative instability wording.",
        method="scorecard", anonymity="attributed", blind_results_until_close=False,
        quorum_count=1, approval_threshold=60, objection_threshold=20,
    )
    balanced = create_criterion(
        actor=owner, exercise=exercise, title="Balanced criterion",
        description="Both options score the same here.", weight=1,
        scale_min=1, scale_max=5, higher_is_better=True, order=0,
    )
    tilted = create_criterion(
        actor=owner, exercise=exercise, title="Tilted criterion",
        description="The options diverge here.", weight=1,
        scale_min=1, scale_max=5, higher_is_better=True, order=1,
    )
    round_item = create_round(actor=owner, exercise=exercise)
    transition_round(actor=owner, round=round_item, status=EvaluationRound.Status.OPEN)
    save_submission(
        actor=owner, confidence=4, overall_rationale="", round=round_item,
        responses=[
            {"option_id": first.id, "criterion_id": balanced.id, "score": 3},
            {"option_id": first.id, "criterion_id": tilted.id, "score": 3},
            {"option_id": second.id, "criterion_id": balanced.id, "score": 4},
            {"option_id": second.id, "criterion_id": tilted.id, "score": 2},
        ],
    )

    result = evaluation_results(round=round_item, viewer=owner)
    assert "directional" in result["uncertainty_narrative"]


@pytest.mark.django_db
def test_uncertainty_narrative_notes_stability_and_disagreement(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    second_evaluator = user_factory(email="tornado-second@example.com")
    Membership.objects.create(
        organisation=organisation, user=second_evaluator,
        role=Membership.Role.CONTRIBUTOR, status=Membership.Status.ACTIVE,
    )
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True), owner=owner,
        title="Choose a clear but contested leader",
    )
    Participant.objects.create(
        organisation=organisation, decision=decision, user=second_evaluator,
        role=Participant.Role.CONTRIBUTOR, added_by=owner,
    )
    leader = create_option(actor=owner, decision=decision, title="Clear leader", description="Wins comfortably.")
    trailing = create_option(actor=owner, decision=decision, title="Clear trailer", description="Loses comfortably.")
    exercise = create_exercise(
        actor=owner, decision=decision, owner_id=owner.id,
        title="Stable but contested scorecard", purpose="Check narrative stability + disagreement wording.",
        method="scorecard", anonymity="attributed", blind_results_until_close=False,
        quorum_count=2, approval_threshold=60, objection_threshold=20,
    )
    value = create_criterion(
        actor=owner, exercise=exercise, title="Value", description="Expected value.",
        weight=1, scale_min=1, scale_max=5, higher_is_better=True, order=0,
    )
    round_item = create_round(actor=owner, exercise=exercise)
    transition_round(actor=owner, round=round_item, status=EvaluationRound.Status.OPEN)
    save_submission(
        actor=owner, confidence=5, overall_rationale="", round=round_item,
        responses=[
            {"option_id": leader.id, "criterion_id": value.id, "score": 5},
            {"option_id": trailing.id, "criterion_id": value.id, "score": 1},
        ],
    )
    save_submission(
        actor=second_evaluator, confidence=5, overall_rationale="", round=round_item,
        responses=[
            {"option_id": leader.id, "criterion_id": value.id, "score": 1},
            {"option_id": trailing.id, "criterion_id": value.id, "score": 1},
        ],
    )

    result = evaluation_results(round=round_item, viewer=owner)
    assert result["options"][0]["option_id"] == str(leader.id)
    assert result["options"][0]["disagreement"] == "high"
    assert "stays first" in result["uncertainty_narrative"]
    assert "disagreement" in result["uncertainty_narrative"]


@pytest.mark.django_db
def test_vote_result_reports_dissent_rate(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    dissenter = user_factory(email="dissenter@example.com")
    agreer = user_factory(email="agreer@example.com")
    for user in (dissenter, agreer):
        Membership.objects.create(
            organisation=organisation, user=user,
            role=Membership.Role.CONTRIBUTOR, status=Membership.Status.ACTIVE,
        )
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True), owner=owner,
        title="Consent to the mobilisation plan",
    )
    for user in (dissenter, agreer):
        Participant.objects.create(
            organisation=organisation, decision=decision, user=user,
            role=Participant.Role.CONTRIBUTOR, added_by=owner,
        )
    option = create_option(actor=owner, decision=decision, title="Plan", description="The plan.")
    exercise = create_exercise(
        actor=owner, decision=decision, owner_id=owner.id,
        title="Consent round", purpose="Test dissent.", method="consent",
        anonymity="attributed", blind_results_until_close=False,
        quorum_count=3, approval_threshold=60, objection_threshold=20,
    )
    round_item = create_round(actor=owner, exercise=exercise)
    transition_round(actor=owner, round=round_item, status=EvaluationRound.Status.OPEN)

    save_submission(actor=owner, confidence=4, overall_rationale="", round=round_item, responses=[{"option_id": option.id, "vote": "consent"}])
    save_submission(actor=agreer, confidence=4, overall_rationale="", round=round_item, responses=[{"option_id": option.id, "vote": "consent"}])
    save_submission(actor=dissenter, confidence=4, overall_rationale="A reasoned objection.", round=round_item, responses=[{"option_id": option.id, "vote": "object"}])

    result = evaluation_results(round=round_item, viewer=owner)
    row = result["options"][0]
    assert row["dissent_rate"] == pytest.approx(33.33, abs=0.01)


@pytest.mark.django_db
def test_observer_cannot_submit_evaluation(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    observer = user_factory(email="observer@example.com")
    Membership.objects.create(
        organisation=organisation,
        user=observer,
        role=Membership.Role.VIEWER,
        status=Membership.Status.ACTIVE,
    )
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    Participant.objects.create(
        organisation=organisation,
        decision=decision,
        user=observer,
        role=Participant.Role.OBSERVER,
        added_by=owner,
    )
    option = create_option(actor=owner, decision=decision, title="Option", description="One option.")
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Approval round",
        purpose="Test approval.",
        method="approval",
        anonymity="attributed",
        blind_results_until_close=True,
        quorum_count=1,
        approval_threshold=60,
        objection_threshold=20,
    )
    round_item = create_round(actor=owner, exercise=exercise)
    transition_round(actor=owner, round=round_item, status="open")
    with pytest.raises(PermissionDenied):
        save_submission(
            actor=observer,
            round=round_item,
            confidence=3,
            overall_rationale="",
            responses=[{"option_id": option.id, "vote": "approve"}],
        )


@pytest.mark.django_db
def test_constraint_recommendation_respects_budget_and_capacity(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    assessor = user_factory(email="assessor@example.com")
    Membership.objects.create(
        organisation=organisation,
        user=assessor,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    first = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner, title="Programme A")
    second = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner, title="Programme B")
    third = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner, title="Mandatory compliance")
    portfolio = create_portfolio(
        actor=owner,
        organisation=organisation,
        owner_id=owner.id,
        title="2027 strategic portfolio",
        purpose="Allocate finite investment and delivery capacity.",
        budget_limit=100,
        capacity_limit=10,
        blind_results_until_close=False,
    )
    criterion = add_portfolio_criterion(
        actor=owner,
        portfolio=portfolio,
        title="Strategic contribution",
        description="Contribution to strategic outcomes.",
        weight=1,
        higher_is_better=True,
        order=0,
    )
    candidate_a = add_candidate(actor=owner, portfolio=portfolio, decision_id=first.id, budget_required=60, capacity_required=6, mandatory=False, rationale="")
    candidate_b = add_candidate(actor=owner, portfolio=portfolio, decision_id=second.id, budget_required=55, capacity_required=5, mandatory=False, rationale="")
    mandatory = add_candidate(actor=owner, portfolio=portfolio, decision_id=third.id, budget_required=20, capacity_required=2, mandatory=True, rationale="Regulatory obligation")
    portfolio = update_portfolio(actor=owner, portfolio=portfolio, fields={"status": PrioritisationPortfolio.Status.OPEN})
    for candidate, score in [(candidate_a, 90), (candidate_b, 80), (mandatory, 45)]:
        candidate.refresh_from_db()
        save_portfolio_assessment(actor=assessor, candidate=candidate, criterion_id=criterion.id, score=score, confidence=4, rationale="Independent assessment")
    result = portfolio_recommendation(portfolio=portfolio)
    recommended = {item["decision_id"] for item in result["candidates"] if item["recommended"]}
    assert str(third.id) in recommended
    assert str(first.id) in recommended
    assert str(second.id) not in recommended
    assert result["recommended_budget"] == 80

@pytest.mark.django_db
def test_approval_requires_complete_method_specific_ballots(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=owner,
        title="Choose a mobilisation model",
    )
    first = create_option(actor=owner, decision=decision, title="Local", description="Local model")
    second = create_option(actor=owner, decision=decision, title="Central", description="Central model")
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Approval ballot",
        purpose="Test broad support.",
        method="approval",
        anonymity="peer_anonymous",
        blind_results_until_close=True,
        quorum_count=1,
        approval_threshold=60,
        objection_threshold=20,
    )
    round_item = create_round(actor=owner, exercise=exercise)
    transition_round(actor=owner, round=round_item, status=EvaluationRound.Status.OPEN)

    from apps.evaluations.services import EvaluationServiceError

    with pytest.raises(EvaluationServiceError):
        save_submission(
            actor=owner,
            round=round_item,
            confidence=4,
            overall_rationale="Incomplete ballot.",
            responses=[{"option_id": first.id, "vote": "approve"}],
        )
    with pytest.raises(EvaluationServiceError):
        save_submission(
            actor=owner,
            round=round_item,
            confidence=4,
            overall_rationale="Wrong method semantics.",
            responses=[
                {"option_id": first.id, "vote": "concern"},
                {"option_id": second.id, "vote": "approve"},
            ],
        )

    submission = save_submission(
        actor=owner,
        round=round_item,
        confidence=4,
        overall_rationale="Complete approval ballot.",
        responses=[
            {"option_id": first.id, "vote": "approve"},
            {"option_id": second.id, "vote": "abstain"},
        ],
    )
    assert submission.responses.count() == 2


@pytest.mark.django_db
def test_blind_portfolio_seals_aggregates_and_requires_closure_for_selection(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    assessor = user_factory(email="portfolio-assessor@example.com")
    Membership.objects.create(
        organisation=organisation,
        user=assessor,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=owner,
        title="Community resilience programme",
    )
    portfolio = create_portfolio(
        actor=owner,
        organisation=organisation,
        owner_id=owner.id,
        title="Blind strategic portfolio",
        purpose="Protect independent assessments.",
        budget_limit=100,
        capacity_limit=10,
        anonymity="peer_anonymous",
        blind_results_until_close=True,
    )
    criterion = add_portfolio_criterion(
        actor=owner,
        portfolio=portfolio,
        title="Strategic value",
        description="Contribution to outcomes.",
        weight=1,
        higher_is_better=True,
        order=0,
    )
    candidate = add_candidate(
        actor=owner,
        portfolio=portfolio,
        decision_id=decision.id,
        budget_required=40,
        capacity_required=4,
        mandatory=False,
        rationale="Candidate programme.",
    )
    portfolio = update_portfolio(
        actor=owner,
        portfolio=portfolio,
        fields={"status": PrioritisationPortfolio.Status.OPEN},
    )
    candidate.refresh_from_db()
    save_portfolio_assessment(
        actor=assessor,
        candidate=candidate,
        criterion_id=criterion.id,
        score=85,
        confidence=4,
        rationale="Strong strategic fit.",
    )
    assert portfolio_recommendation(portfolio=portfolio)["hidden"] is True

    from apps.evaluations.services import EvaluationServiceError, set_selection

    with pytest.raises(EvaluationServiceError):
        set_selection(
            actor=owner,
            candidate=candidate,
            selected=True,
            priority_order=1,
            approved_budget=40,
            approved_capacity=4,
            rationale="Too early.",
        )

    portfolio = update_portfolio(
        actor=owner,
        portfolio=portfolio,
        fields={"status": PrioritisationPortfolio.Status.CLOSED},
    )
    visible = portfolio_recommendation(portfolio=portfolio)
    assert visible["hidden"] is False
    assert visible["candidates"][0]["recommended"] is True
