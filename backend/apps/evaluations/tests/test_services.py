import pytest
from django.core.exceptions import PermissionDenied

from apps.decision_options.services import create_option
from apps.evaluations.models import (
    EvaluationExercise,
    EvaluationRound,
    EvaluationSubmission,
    ForecastQuestion,
    LiquidVote,
    PrioritisationPortfolio,
)
from apps.evaluations.services import (
    EvaluationServiceError,
    add_candidate,
    add_portfolio_criterion,
    cast_liquid_vote,
    cast_opinion_vote,
    create_criterion,
    create_exercise,
    create_forecast_question,
    create_minority_report,
    create_opinion_statement,
    create_portfolio,
    create_round,
    evaluation_results,
    forecasting_leaderboard,
    liquid_democracy_tally,
    opinion_clustering_analysis,
    portfolio_recommendation,
    resolve_forecast_question,
    save_portfolio_assessment,
    save_submission,
    scoring_options_for_exercise,
    submit_forecast,
    transition_round,
    update_exercise,
    update_portfolio,
)
from apps.organisations.models import Membership
from apps.participants.models import ConflictOfInterest, Participant
from apps.participants.services import declare_conflict


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
        organisation=organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=owner,
        title="Grant round",
    )
    contributor_participant = Participant.objects.create(
        organisation=organisation,
        decision=decision,
        user=contributor,
        role=Participant.Role.CONTRIBUTOR,
        added_by=owner,
    )
    conflicted_option = create_option(
        actor=owner,
        decision=decision,
        title="Applicant with a conflict",
        description="Desc.",
    )
    clean_option = create_option(
        actor=owner,
        decision=decision,
        title="Applicant without a conflict",
        description="Desc.",
    )
    declare_conflict(
        actor=contributor,
        participant=contributor_participant,
        scope=ConflictOfInterest.Scope.OPTION,
        option=conflicted_option,
        reason="I sit on their board.",
    )
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Reviewer scorecard",
        purpose="Score applications.",
        method="scorecard",
        quorum_count=1,
    )
    value = create_criterion(
        actor=owner,
        exercise=exercise,
        title="Impact",
        description="Expected impact.",
        weight=1,
        scale_min=1,
        scale_max=5,
        higher_is_better=True,
        order=0,
    )
    round_item = create_round(actor=owner, exercise=exercise, title="Round one")
    transition_round(actor=owner, round=round_item, status=EvaluationRound.Status.OPEN)

    save_submission(
        actor=contributor,
        round=round_item,
        confidence=4,
        overall_rationale="Scored both.",
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
            organisation=organisation,
            user=user,
            role=Membership.Role.CONTRIBUTOR,
            status=Membership.Status.ACTIVE,
        )
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=owner,
        title="Choose a rollout approach",
    )
    for user in (owner, first_evaluator, second_evaluator):
        Participant.objects.get_or_create(
            organisation=organisation,
            decision=decision,
            user=user,
            defaults={"role": Participant.Role.CONTRIBUTOR, "added_by": owner},
        )
    contested = create_option(
        actor=owner, decision=decision, title="Contested option", description="Divides opinion."
    )
    agreed = create_option(
        actor=owner, decision=decision, title="Agreed option", description="Everyone agrees."
    )
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Dispersion test scorecard",
        purpose="Check dispersion reporting.",
        method="scorecard",
        anonymity="attributed",
        blind_results_until_close=False,
        quorum_count=2,
        approval_threshold=60,
        objection_threshold=20,
    )
    value = create_criterion(
        actor=owner,
        exercise=exercise,
        title="Value",
        description="Expected value.",
        weight=1,
        scale_min=1,
        scale_max=5,
        higher_is_better=True,
        order=0,
    )
    round_item = create_round(actor=owner, exercise=exercise)
    transition_round(actor=owner, round=round_item, status=EvaluationRound.Status.OPEN)

    save_submission(
        actor=owner,
        confidence=5,
        overall_rationale="Strong preference.",
        round=round_item,
        responses=[
            {"option_id": contested.id, "criterion_id": value.id, "score": 5},
            {"option_id": agreed.id, "criterion_id": value.id, "score": 3},
        ],
    )
    save_submission(
        actor=first_evaluator,
        confidence=5,
        overall_rationale="Opposite preference.",
        round=round_item,
        responses=[
            {"option_id": contested.id, "criterion_id": value.id, "score": 1},
            {"option_id": agreed.id, "criterion_id": value.id, "score": 3},
        ],
    )
    save_submission(
        actor=second_evaluator,
        confidence=5,
        overall_rationale="Also agrees.",
        round=round_item,
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
def test_tornado_orders_criteria_by_impact_on_the_leader(organisation_factory, decision_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=owner,
        title="Choose a delivery model",
    )
    leader = create_option(
        actor=owner, decision=decision, title="Leading option", description="Currently ahead."
    )
    other = create_option(
        actor=owner, decision=decision, title="Other option", description="Currently behind."
    )
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Tornado test scorecard",
        purpose="Check tornado ordering.",
        method="scorecard",
        anonymity="attributed",
        blind_results_until_close=False,
        quorum_count=1,
        approval_threshold=60,
        objection_threshold=20,
    )
    heavy = create_criterion(
        actor=owner,
        exercise=exercise,
        title="Heavily weighted",
        description="A criterion with a large weight.",
        weight=3,
        scale_min=1,
        scale_max=5,
        higher_is_better=True,
        order=0,
    )
    light = create_criterion(
        actor=owner,
        exercise=exercise,
        title="Lightly weighted",
        description="A criterion with a small weight.",
        weight=1,
        scale_min=1,
        scale_max=5,
        higher_is_better=True,
        order=1,
    )
    round_item = create_round(actor=owner, exercise=exercise)
    transition_round(actor=owner, round=round_item, status=EvaluationRound.Status.OPEN)
    save_submission(
        actor=owner,
        confidence=4,
        overall_rationale="",
        round=round_item,
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
def test_uncertainty_narrative_flags_an_unstable_ranking(organisation_factory, decision_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=owner,
        title="Choose between near-tied options",
    )
    first = create_option(
        actor=owner, decision=decision, title="First option", description="One profile."
    )
    second = create_option(
        actor=owner, decision=decision, title="Second option", description="A different profile."
    )
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Near-tie scorecard",
        purpose="Check narrative instability wording.",
        method="scorecard",
        anonymity="attributed",
        blind_results_until_close=False,
        quorum_count=1,
        approval_threshold=60,
        objection_threshold=20,
    )
    balanced = create_criterion(
        actor=owner,
        exercise=exercise,
        title="Balanced criterion",
        description="Both options score the same here.",
        weight=1,
        scale_min=1,
        scale_max=5,
        higher_is_better=True,
        order=0,
    )
    tilted = create_criterion(
        actor=owner,
        exercise=exercise,
        title="Tilted criterion",
        description="The options diverge here.",
        weight=1,
        scale_min=1,
        scale_max=5,
        higher_is_better=True,
        order=1,
    )
    round_item = create_round(actor=owner, exercise=exercise)
    transition_round(actor=owner, round=round_item, status=EvaluationRound.Status.OPEN)
    save_submission(
        actor=owner,
        confidence=4,
        overall_rationale="",
        round=round_item,
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
        organisation=organisation,
        user=second_evaluator,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=owner,
        title="Choose a clear but contested leader",
    )
    Participant.objects.create(
        organisation=organisation,
        decision=decision,
        user=second_evaluator,
        role=Participant.Role.CONTRIBUTOR,
        added_by=owner,
    )
    leader = create_option(
        actor=owner, decision=decision, title="Clear leader", description="Wins comfortably."
    )
    trailing = create_option(
        actor=owner, decision=decision, title="Clear trailer", description="Loses comfortably."
    )
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Stable but contested scorecard",
        purpose="Check narrative stability + disagreement wording.",
        method="scorecard",
        anonymity="attributed",
        blind_results_until_close=False,
        quorum_count=2,
        approval_threshold=60,
        objection_threshold=20,
    )
    value = create_criterion(
        actor=owner,
        exercise=exercise,
        title="Value",
        description="Expected value.",
        weight=1,
        scale_min=1,
        scale_max=5,
        higher_is_better=True,
        order=0,
    )
    round_item = create_round(actor=owner, exercise=exercise)
    transition_round(actor=owner, round=round_item, status=EvaluationRound.Status.OPEN)
    save_submission(
        actor=owner,
        confidence=5,
        overall_rationale="",
        round=round_item,
        responses=[
            {"option_id": leader.id, "criterion_id": value.id, "score": 5},
            {"option_id": trailing.id, "criterion_id": value.id, "score": 1},
        ],
    )
    save_submission(
        actor=second_evaluator,
        confidence=5,
        overall_rationale="",
        round=round_item,
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
def test_vote_result_reports_dissent_rate(organisation_factory, decision_factory, user_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    dissenter = user_factory(email="dissenter@example.com")
    agreer = user_factory(email="agreer@example.com")
    for user in (dissenter, agreer):
        Membership.objects.create(
            organisation=organisation,
            user=user,
            role=Membership.Role.CONTRIBUTOR,
            status=Membership.Status.ACTIVE,
        )
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=owner,
        title="Consent to the mobilisation plan",
    )
    for user in (dissenter, agreer):
        Participant.objects.create(
            organisation=organisation,
            decision=decision,
            user=user,
            role=Participant.Role.CONTRIBUTOR,
            added_by=owner,
        )
    option = create_option(actor=owner, decision=decision, title="Plan", description="The plan.")
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Consent round",
        purpose="Test dissent.",
        method="consent",
        anonymity="attributed",
        blind_results_until_close=False,
        quorum_count=3,
        approval_threshold=60,
        objection_threshold=20,
    )
    round_item = create_round(actor=owner, exercise=exercise)
    transition_round(actor=owner, round=round_item, status=EvaluationRound.Status.OPEN)

    save_submission(
        actor=owner,
        confidence=4,
        overall_rationale="",
        round=round_item,
        responses=[{"option_id": option.id, "vote": "consent"}],
    )
    save_submission(
        actor=agreer,
        confidence=4,
        overall_rationale="",
        round=round_item,
        responses=[{"option_id": option.id, "vote": "consent"}],
    )
    save_submission(
        actor=dissenter,
        confidence=4,
        overall_rationale="A reasoned objection.",
        round=round_item,
        responses=[{"option_id": option.id, "vote": "object"}],
    )

    result = evaluation_results(round=round_item, viewer=owner)
    row = result["options"][0]
    assert row["dissent_rate"] == pytest.approx(33.33, abs=0.01)


@pytest.mark.django_db
def test_observer_cannot_submit_evaluation(organisation_factory, decision_factory, user_factory):  # type: ignore[no-untyped-def]
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
    option = create_option(
        actor=owner, decision=decision, title="Option", description="One option."
    )
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
    first = decision_factory(
        workspace=organisation.workspaces.get(is_default=True), owner=owner, title="Programme A"
    )
    second = decision_factory(
        workspace=organisation.workspaces.get(is_default=True), owner=owner, title="Programme B"
    )
    third = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=owner,
        title="Mandatory compliance",
    )
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
    candidate_a = add_candidate(
        actor=owner,
        portfolio=portfolio,
        decision_id=first.id,
        budget_required=60,
        capacity_required=6,
        mandatory=False,
        rationale="",
    )
    candidate_b = add_candidate(
        actor=owner,
        portfolio=portfolio,
        decision_id=second.id,
        budget_required=55,
        capacity_required=5,
        mandatory=False,
        rationale="",
    )
    mandatory = add_candidate(
        actor=owner,
        portfolio=portfolio,
        decision_id=third.id,
        budget_required=20,
        capacity_required=2,
        mandatory=True,
        rationale="Regulatory obligation",
    )
    portfolio = update_portfolio(
        actor=owner, portfolio=portfolio, fields={"status": PrioritisationPortfolio.Status.OPEN}
    )
    for candidate, score in [(candidate_a, 90), (candidate_b, 80), (mandatory, 45)]:
        candidate.refresh_from_db()
        save_portfolio_assessment(
            actor=assessor,
            candidate=candidate,
            criterion_id=criterion.id,
            score=score,
            confidence=4,
            rationale="Independent assessment",
        )
    result = portfolio_recommendation(portfolio=portfolio)
    recommended = {item["decision_id"] for item in result["candidates"] if item["recommended"]}
    assert str(third.id) in recommended
    assert str(first.id) in recommended
    assert str(second.id) not in recommended
    assert result["recommended_budget"] == 80


@pytest.mark.django_db
def test_approval_requires_complete_method_specific_ballots(organisation_factory, decision_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=owner,
        title="Choose a mobilisation model",
    )
    first = create_option(actor=owner, decision=decision, title="Local", description="Local model")
    second = create_option(
        actor=owner, decision=decision, title="Central", description="Central model"
    )
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


@pytest.mark.django_db
def test_ranked_choice_instant_runoff_picks_majority_winner_after_elimination(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    voters = [owner]
    for index in range(2, 6):
        voter = user_factory(email=f"voter{index}@example.com")
        Membership.objects.create(
            organisation=organisation,
            user=voter,
            role=Membership.Role.CONTRIBUTOR,
            status=Membership.Status.ACTIVE,
        )
        voters.append(voter)
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=owner,
        title="Pick one community grant",
    )
    for voter in voters[1:]:
        Participant.objects.create(
            organisation=organisation,
            decision=decision,
            user=voter,
            role=Participant.Role.CONTRIBUTOR,
            added_by=owner,
        )
    option_a = create_option(
        actor=owner, decision=decision, title="Option A", description="Water access."
    )
    option_b = create_option(
        actor=owner, decision=decision, title="Option B", description="School meals."
    )
    option_c = create_option(
        actor=owner, decision=decision, title="Option C", description="Solar lighting."
    )

    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Community pick",
        purpose="Choose one grant.",
        method="ranked_choice",
        anonymity="attributed",
        blind_results_until_close=False,
        quorum_count=1,
        approval_threshold=60,
        objection_threshold=20,
    )
    round_item = create_round(actor=owner, exercise=exercise)
    transition_round(actor=owner, round=round_item, status=EvaluationRound.Status.OPEN)

    # Ballots: 2x[A,B,C], 2x[B,C,A], 1x[C,A,B]
    ballots = [
        [option_a, option_b, option_c],
        [option_a, option_b, option_c],
        [option_b, option_c, option_a],
        [option_b, option_c, option_a],
        [option_c, option_a, option_b],
    ]
    for voter, ballot in zip(voters, ballots, strict=False):
        save_submission(
            actor=voter,
            round=round_item,
            confidence=3,
            overall_rationale="",
            responses=[
                {"option_id": option.id, "rank": rank}
                for rank, option in enumerate(ballot, start=1)
            ],
        )

    result = evaluation_results(round=round_item, viewer=owner)
    assert result["method"] == "ranked_choice"
    order = [row["option_id"] for row in result["options"]]
    assert order == [str(option_a.id), str(option_b.id), str(option_c.id)]
    assert result["options"][0]["final_rank"] == 1
    assert result["options"][0]["eliminated_in_round"] is None
    assert result["options"][2]["eliminated_in_round"] == 1
    assert len(result["ranked_choice_rounds"]) == 2
    assert result["ranked_choice_rounds"][0]["eliminated_option_id"] == str(option_c.id)


@pytest.mark.django_db
def test_ranked_choice_rejects_incomplete_or_repeated_ranks(organisation_factory, decision_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=owner,
        title="Pick a grant",
    )
    first = create_option(actor=owner, decision=decision, title="First", description="d")
    second = create_option(actor=owner, decision=decision, title="Second", description="d")
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Ranked pick",
        purpose="p",
        method="ranked_choice",
        anonymity="attributed",
        blind_results_until_close=False,
        quorum_count=1,
        approval_threshold=60,
        objection_threshold=20,
    )
    round_item = create_round(actor=owner, exercise=exercise)
    transition_round(actor=owner, round=round_item, status=EvaluationRound.Status.OPEN)

    with pytest.raises(EvaluationServiceError):
        save_submission(
            actor=owner,
            round=round_item,
            confidence=3,
            overall_rationale="",
            responses=[{"option_id": first.id, "rank": 1}, {"option_id": second.id, "rank": 1}],
        )
    with pytest.raises(EvaluationServiceError):
        save_submission(
            actor=owner,
            round=round_item,
            confidence=3,
            overall_rationale="",
            responses=[
                {"option_id": first.id, "vote": "approve"},
                {"option_id": second.id, "rank": 2},
            ],
        )


@pytest.mark.django_db
def test_blind_applicant_identity_hides_titles_until_managers_or_close(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    contributor = user_factory(email="blind-reviewer@example.com")
    Membership.objects.create(
        organisation=organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=owner,
        title="Blind review round",
    )
    Participant.objects.create(
        organisation=organisation,
        decision=decision,
        user=contributor,
        role=Participant.Role.CONTRIBUTOR,
        added_by=owner,
    )
    create_option(actor=owner, decision=decision, title="Alpha Farms Cooperative", description="d")
    create_option(actor=owner, decision=decision, title="Beta Youth Trust", description="d")
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Blind scorecard",
        purpose="p",
        method="scorecard",
        anonymity="attributed",
        blind_results_until_close=False,
        blind_applicant_identity=True,
        quorum_count=1,
        approval_threshold=60,
        objection_threshold=20,
    )

    manager_view = scoring_options_for_exercise(exercise=exercise, viewer=owner)
    assert all(not row["blinded"] for row in manager_view)
    assert {row["title"] for row in manager_view} == {"Alpha Farms Cooperative", "Beta Youth Trust"}

    reviewer_view = scoring_options_for_exercise(exercise=exercise, viewer=contributor)
    assert all(row["blinded"] for row in reviewer_view)
    assert {row["title"] for row in reviewer_view} == {"Application A", "Application B"}

    exercise.status = EvaluationExercise.Status.CLOSED
    exercise.save(update_fields=["status", "updated_at"])
    closed_view = scoring_options_for_exercise(exercise=exercise, viewer=contributor)
    assert all(not row["blinded"] for row in closed_view)


def _open_forecasting_exercise(*, owner, decision, **overrides):
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title=overrides.pop("title", "Calibration tournament"),
        purpose=overrides.pop("purpose", "Forecast outcomes before they happen."),
        method="forecasting",
        quorum_count=overrides.pop("quorum_count", 1),
        **overrides,
    )
    return update_exercise(
        actor=owner, exercise=exercise, fields={"status": EvaluationExercise.Status.OPEN}
    )


@pytest.mark.django_db
def test_create_forecast_question_requires_forecasting_method(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Scorecard",
        purpose="p",
        method="scorecard",
        quorum_count=1,
    )
    with pytest.raises(EvaluationServiceError):
        create_forecast_question(actor=owner, exercise=exercise, question_text="Will X happen?")


@pytest.mark.django_db
def test_create_forecast_question_permission_denied_for_non_manager(
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
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    Participant.objects.create(
        organisation=organisation,
        decision=decision,
        user=contributor,
        role=Participant.Role.CONTRIBUTOR,
        added_by=owner,
    )
    exercise = _open_forecasting_exercise(owner=owner, decision=decision)
    with pytest.raises(PermissionDenied):
        create_forecast_question(
            actor=contributor, exercise=exercise, question_text="Will X happen?"
        )


@pytest.mark.django_db
def test_create_forecast_question_rejected_once_exercise_closed(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = _open_forecasting_exercise(owner=owner, decision=decision)
    exercise = update_exercise(
        actor=owner, exercise=exercise, fields={"status": EvaluationExercise.Status.CLOSED}
    )
    with pytest.raises(EvaluationServiceError):
        create_forecast_question(actor=owner, exercise=exercise, question_text="Will X happen?")


@pytest.mark.django_db
def test_update_exercise_forecasting_status_transitions_follow_governed_sequence(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Forecasting",
        purpose="p",
        method="forecasting",
        quorum_count=1,
    )
    with pytest.raises(EvaluationServiceError):
        update_exercise(
            actor=owner, exercise=exercise, fields={"status": EvaluationExercise.Status.CLOSED}
        )
    exercise = update_exercise(
        actor=owner, exercise=exercise, fields={"status": EvaluationExercise.Status.OPEN}
    )
    exercise = update_exercise(
        actor=owner, exercise=exercise, fields={"status": EvaluationExercise.Status.CLOSED}
    )
    exercise = update_exercise(
        actor=owner, exercise=exercise, fields={"status": EvaluationExercise.Status.ARCHIVED}
    )
    assert exercise.status == EvaluationExercise.Status.ARCHIVED


@pytest.mark.django_db
def test_create_round_rejects_forecasting_exercise(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = _open_forecasting_exercise(owner=owner, decision=decision)
    with pytest.raises(EvaluationServiceError):
        create_round(actor=owner, exercise=exercise, title="Round one")


@pytest.mark.django_db
def test_submit_forecast_happy_path_and_revision_overwrites_prior_probability(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = _open_forecasting_exercise(owner=owner, decision=decision)
    question = create_forecast_question(
        actor=owner, exercise=exercise, question_text="Will the pilot launch on time?"
    )

    forecast = submit_forecast(actor=owner, question=question, probability=20)
    assert forecast.probability == 20

    revised = submit_forecast(actor=owner, question=question, probability=90)
    assert revised.id == forecast.id
    assert revised.probability == 90
    assert question.forecasts.count() == 1


@pytest.mark.django_db
def test_submit_forecast_rejects_non_participant(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    outsider = user_factory(email="outsider@example.com")
    Membership.objects.create(
        organisation=organisation,
        user=outsider,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = _open_forecasting_exercise(owner=owner, decision=decision)
    question = create_forecast_question(
        actor=owner, exercise=exercise, question_text="Will X happen?"
    )
    with pytest.raises(PermissionDenied):
        submit_forecast(actor=outsider, question=question, probability=50)


@pytest.mark.django_db
def test_submit_forecast_rejects_observer(
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
    exercise = _open_forecasting_exercise(owner=owner, decision=decision)
    question = create_forecast_question(
        actor=owner, exercise=exercise, question_text="Will X happen?"
    )
    with pytest.raises(PermissionDenied):
        submit_forecast(actor=observer, question=question, probability=50)


@pytest.mark.django_db
def test_submit_forecast_rejects_when_question_already_resolved(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = _open_forecasting_exercise(owner=owner, decision=decision)
    question = create_forecast_question(
        actor=owner, exercise=exercise, question_text="Will X happen?"
    )
    resolve_forecast_question(actor=owner, question=question, outcome=True)
    with pytest.raises(EvaluationServiceError):
        submit_forecast(actor=owner, question=question, probability=50)


@pytest.mark.django_db
def test_submit_forecast_rejects_when_exercise_not_open(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Forecasting",
        purpose="p",
        method="forecasting",
        quorum_count=1,
    )
    # A draft exercise cannot accept forecast questions in the first place, so open it
    # briefly to create the question, then close it back down before forecasting.
    exercise = update_exercise(
        actor=owner, exercise=exercise, fields={"status": EvaluationExercise.Status.OPEN}
    )
    question = create_forecast_question(
        actor=owner, exercise=exercise, question_text="Will X happen?"
    )
    exercise = update_exercise(
        actor=owner, exercise=exercise, fields={"status": EvaluationExercise.Status.CLOSED}
    )
    with pytest.raises(EvaluationServiceError):
        submit_forecast(actor=owner, question=question, probability=50)


@pytest.mark.django_db
def test_resolve_forecast_question_computes_brier_scores(
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
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    Participant.objects.create(
        organisation=organisation,
        decision=decision,
        user=contributor,
        role=Participant.Role.CONTRIBUTOR,
        added_by=owner,
    )
    exercise = _open_forecasting_exercise(owner=owner, decision=decision)
    question = create_forecast_question(
        actor=owner, exercise=exercise, question_text="Will the grant renew?"
    )
    submit_forecast(actor=owner, question=question, probability=80)
    submit_forecast(actor=contributor, question=question, probability=30)

    resolved = resolve_forecast_question(actor=owner, question=question, outcome=True)

    assert resolved.status == ForecastQuestion.Status.RESOLVED
    assert resolved.outcome is True
    assert resolved.resolved_by == owner

    owner_forecast = resolved.forecasts.get(forecaster=owner)
    contributor_forecast = resolved.forecasts.get(forecaster=contributor)
    assert float(owner_forecast.brier_score) == pytest.approx(0.04)
    assert float(contributor_forecast.brier_score) == pytest.approx(0.49)


@pytest.mark.django_db
def test_resolve_forecast_question_with_zero_forecasts(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = _open_forecasting_exercise(owner=owner, decision=decision)
    question = create_forecast_question(
        actor=owner, exercise=exercise, question_text="Will X happen?"
    )
    resolved = resolve_forecast_question(actor=owner, question=question, outcome=False)
    assert resolved.status == ForecastQuestion.Status.RESOLVED
    assert resolved.forecasts.count() == 0


@pytest.mark.django_db
def test_resolve_forecast_question_twice_raises(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = _open_forecasting_exercise(owner=owner, decision=decision)
    question = create_forecast_question(
        actor=owner, exercise=exercise, question_text="Will X happen?"
    )
    resolve_forecast_question(actor=owner, question=question, outcome=True)
    with pytest.raises(EvaluationServiceError):
        resolve_forecast_question(actor=owner, question=question, outcome=False)


@pytest.mark.django_db
def test_resolve_forecast_question_permission_denied_for_non_manager(
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
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    Participant.objects.create(
        organisation=organisation,
        decision=decision,
        user=contributor,
        role=Participant.Role.CONTRIBUTOR,
        added_by=owner,
    )
    exercise = _open_forecasting_exercise(owner=owner, decision=decision)
    question = create_forecast_question(
        actor=owner, exercise=exercise, question_text="Will X happen?"
    )
    with pytest.raises(PermissionDenied):
        resolve_forecast_question(actor=contributor, question=question, outcome=True)


@pytest.mark.django_db
def test_forecasting_leaderboard_orders_by_mean_brier_score_across_multiple_questions(
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
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    Participant.objects.create(
        organisation=organisation,
        decision=decision,
        user=contributor,
        role=Participant.Role.CONTRIBUTOR,
        added_by=owner,
    )
    exercise = _open_forecasting_exercise(owner=owner, decision=decision)

    question_one = create_forecast_question(
        actor=owner, exercise=exercise, question_text="Will milestone one land on time?"
    )
    submit_forecast(actor=owner, question=question_one, probability=90)
    submit_forecast(actor=contributor, question=question_one, probability=20)
    resolve_forecast_question(actor=owner, question=question_one, outcome=True)
    # owner brier: 0.01, contributor brier: 0.64

    question_two = create_forecast_question(
        actor=owner, exercise=exercise, question_text="Will milestone two land on time?"
    )
    submit_forecast(actor=owner, question=question_two, probability=90)
    submit_forecast(actor=contributor, question=question_two, probability=20)
    resolve_forecast_question(actor=owner, question=question_two, outcome=False)
    # owner brier: 0.81, contributor brier: 0.04
    # owner mean = 0.41, contributor mean = 0.34 -> contributor is better calibrated overall,
    # even though the owner "won" the very first question - this is the point of the metric.

    leaderboard = forecasting_leaderboard(organisation=organisation)

    assert [row["email"] for row in leaderboard] == [contributor.email, owner.email]
    assert leaderboard[0]["mean_brier_score"] == pytest.approx(0.34)
    assert leaderboard[0]["resolved_question_count"] == 2
    assert leaderboard[0]["rank"] == 1
    assert leaderboard[1]["mean_brier_score"] == pytest.approx(0.41)
    assert leaderboard[1]["rank"] == 2


@pytest.mark.django_db
def test_forecasting_leaderboard_excludes_other_organisations_and_unresolved_questions(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    other_organisation = organisation_factory()
    owner = organisation.created_by
    other_owner = other_organisation.created_by

    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = _open_forecasting_exercise(owner=owner, decision=decision)
    resolved_question = create_forecast_question(
        actor=owner, exercise=exercise, question_text="Will X happen?"
    )
    submit_forecast(actor=owner, question=resolved_question, probability=70)
    resolve_forecast_question(actor=owner, question=resolved_question, outcome=True)

    unresolved_question = create_forecast_question(
        actor=owner, exercise=exercise, question_text="Will Y happen?"
    )
    submit_forecast(actor=owner, question=unresolved_question, probability=40)

    other_decision = decision_factory(
        workspace=other_organisation.workspaces.get(is_default=True), owner=other_owner
    )
    other_exercise = _open_forecasting_exercise(owner=other_owner, decision=other_decision)
    other_question = create_forecast_question(
        actor=other_owner, exercise=other_exercise, question_text="Will Z happen?"
    )
    submit_forecast(actor=other_owner, question=other_question, probability=10)
    resolve_forecast_question(actor=other_owner, question=other_question, outcome=True)

    leaderboard = forecasting_leaderboard(organisation=organisation)

    assert len(leaderboard) == 1
    assert leaderboard[0]["email"] == owner.email
    assert leaderboard[0]["resolved_question_count"] == 1
    assert leaderboard[0]["mean_brier_score"] == pytest.approx(0.09)


@pytest.mark.django_db
def test_forecasting_leaderboard_empty_when_no_resolved_questions(
    organisation_factory,
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    assert forecasting_leaderboard(organisation=organisation) == []


def _open_quadratic_exercise(*, owner, decision, **overrides):
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title=overrides.pop("title", "Community priorities"),
        purpose=overrides.pop("purpose", "Spend your voice credits on what matters most."),
        method="quadratic",
        quorum_count=overrides.pop("quorum_count", 1),
        **overrides,
    )
    round_item = create_round(actor=owner, exercise=exercise)
    transition_round(actor=owner, round=round_item, status=EvaluationRound.Status.OPEN)
    return exercise, round_item


@pytest.mark.django_db
def test_quadratic_ballot_rejects_ballot_that_would_exceed_budget(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    option_a = create_option(actor=owner, decision=decision, title="Option A", description="d")
    option_b = create_option(actor=owner, decision=decision, title="Option B", description="d")
    exercise, round_item = _open_quadratic_exercise(owner=owner, decision=decision)
    assert exercise.voice_credit_budget == 100

    with pytest.raises(EvaluationServiceError):
        save_submission(
            actor=owner,
            round=round_item,
            confidence=4,
            overall_rationale="",
            responses=[
                {"option_id": option_a.id, "quadratic_votes": 10},  # costs 100
                {"option_id": option_b.id, "quadratic_votes": 1},  # costs 1, total 101
            ],
        )
    assert not EvaluationSubmission.objects.filter(round=round_item, submitted_by=owner).exists()


@pytest.mark.django_db
def test_quadratic_ballot_accepts_ballot_exactly_at_budget(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    option = create_option(actor=owner, decision=decision, title="Option A", description="d")
    exercise, round_item = _open_quadratic_exercise(owner=owner, decision=decision)

    submission = save_submission(
        actor=owner,
        round=round_item,
        confidence=4,
        overall_rationale="",
        responses=[{"option_id": option.id, "quadratic_votes": 10}],  # costs exactly 100
    )
    assert submission.responses.get().quadratic_votes == 10


@pytest.mark.django_db
def test_quadratic_ballot_rejects_zero_vote_response(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    option = create_option(actor=owner, decision=decision, title="Option A", description="d")
    exercise, round_item = _open_quadratic_exercise(owner=owner, decision=decision)

    with pytest.raises(EvaluationServiceError):
        save_submission(
            actor=owner,
            round=round_item,
            confidence=4,
            overall_rationale="",
            responses=[{"option_id": option.id, "quadratic_votes": 0}],
        )


@pytest.mark.django_db
def test_quadratic_ballot_allows_partial_ballot_without_covering_every_option(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    option_a = create_option(actor=owner, decision=decision, title="Option A", description="d")
    create_option(actor=owner, decision=decision, title="Option B", description="d")
    create_option(actor=owner, decision=decision, title="Option C", description="d")
    exercise, round_item = _open_quadratic_exercise(owner=owner, decision=decision)

    submission = save_submission(
        actor=owner,
        round=round_item,
        confidence=4,
        overall_rationale="",
        responses=[{"option_id": option_a.id, "quadratic_votes": 3}],
        submit=True,
    )
    assert submission.status == EvaluationSubmission.Status.SUBMITTED
    assert submission.responses.count() == 1


@pytest.mark.django_db
def test_quadratic_results_report_net_votes_support_oppose_and_exclude_conflicted_reviewer(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    contributor = user_factory(email="contributor@example.com")
    conflicted = user_factory(email="conflicted@example.com")
    for user in (contributor, conflicted):
        Membership.objects.create(
            organisation=organisation,
            user=user,
            role=Membership.Role.CONTRIBUTOR,
            status=Membership.Status.ACTIVE,
        )
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    for user in (contributor, conflicted):
        Participant.objects.create(
            organisation=organisation,
            decision=decision,
            user=user,
            role=Participant.Role.CONTRIBUTOR,
            added_by=owner,
        )
    option_a = create_option(actor=owner, decision=decision, title="Fund the library", description="d")
    option_b = create_option(actor=owner, decision=decision, title="Fund the park", description="d")
    exercise, round_item = _open_quadratic_exercise(
        owner=owner, decision=decision, blind_results_until_close=False
    )

    conflicted_participant = Participant.objects.get(decision=decision, user=conflicted)
    declare_conflict(
        actor=conflicted,
        participant=conflicted_participant,
        scope=ConflictOfInterest.Scope.DECISION,
        reason="I run the library.",
    )

    save_submission(
        actor=owner,
        round=round_item,
        confidence=4,
        overall_rationale="",
        responses=[{"option_id": option_a.id, "quadratic_votes": 5}],  # cost 25
    )
    save_submission(
        actor=contributor,
        round=round_item,
        confidence=4,
        overall_rationale="",
        responses=[
            {"option_id": option_a.id, "quadratic_votes": -3},  # cost 9
            {"option_id": option_b.id, "quadratic_votes": 1},  # cost 1
        ],
    )
    save_submission(
        actor=conflicted,
        round=round_item,
        confidence=4,
        overall_rationale="",
        responses=[{"option_id": option_a.id, "quadratic_votes": 10}],  # excluded entirely
    )

    result = evaluation_results(round=round_item, viewer=owner)
    rows = {row["option_id"]: row for row in result["options"]}

    row_a = rows[str(option_a.id)]
    assert row_a["net_votes"] == 2  # 5 - 3, conflicted reviewer's 10 excluded
    assert row_a["support_votes"] == 5
    assert row_a["oppose_votes"] == 3
    assert row_a["voter_count"] == 2
    assert row_a["credits_spent"] == 34
    assert row_a["excluded_response_count"] == 1
    assert row_a["conflicted_reviewer_emails"] == [conflicted.email]

    row_b = rows[str(option_b.id)]
    assert row_b["net_votes"] == 1
    assert row_b["credits_spent"] == 1

    assert result["options"][0]["option_id"] == str(option_a.id)
    assert "leads with a net" in result["uncertainty_narrative"]


def _open_liquid_democracy_exercise(*, owner, decision, **overrides):
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title=overrides.pop("title", "Community delegation"),
        purpose=overrides.pop("purpose", "Vote directly or delegate to someone you trust."),
        method="liquid_democracy",
        quorum_count=overrides.pop("quorum_count", 1),
        **overrides,
    )
    return update_exercise(
        actor=owner, exercise=exercise, fields={"status": EvaluationExercise.Status.OPEN}
    )


def _add_eligible_participant(*, organisation, decision, owner, user):
    Membership.objects.create(
        organisation=organisation,
        user=user,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    Participant.objects.create(
        organisation=organisation,
        decision=decision,
        user=user,
        role=Participant.Role.CONTRIBUTOR,
        added_by=owner,
    )


@pytest.mark.django_db
def test_cast_liquid_vote_direct_vote_happy_path(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    option = create_option(actor=owner, decision=decision, title="Option A", description="d")
    exercise = _open_liquid_democracy_exercise(owner=owner, decision=decision)

    vote = cast_liquid_vote(actor=owner, exercise=exercise, option_id=option.id)
    assert vote.option_id == option.id
    assert vote.delegate_to_id is None


@pytest.mark.django_db
def test_cast_liquid_vote_delegation_happy_path(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    contributor = user_factory(email="delegate@example.com")
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    _add_eligible_participant(organisation=organisation, decision=decision, owner=owner, user=contributor)
    exercise = _open_liquid_democracy_exercise(owner=owner, decision=decision)

    vote = cast_liquid_vote(actor=owner, exercise=exercise, delegate_to_id=contributor.id)
    assert vote.delegate_to_id == contributor.id
    assert vote.option_id is None


@pytest.mark.django_db
def test_cast_liquid_vote_direct_vote_overrides_prior_delegation(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    contributor = user_factory(email="delegate@example.com")
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    _add_eligible_participant(organisation=organisation, decision=decision, owner=owner, user=contributor)
    option = create_option(actor=owner, decision=decision, title="Option A", description="d")
    exercise = _open_liquid_democracy_exercise(owner=owner, decision=decision)

    cast_liquid_vote(actor=owner, exercise=exercise, delegate_to_id=contributor.id)
    vote = cast_liquid_vote(actor=owner, exercise=exercise, option_id=option.id)

    assert vote.option_id == option.id
    assert vote.delegate_to_id is None
    assert LiquidVote.objects.filter(exercise=exercise, voter=owner).count() == 1


@pytest.mark.django_db
def test_cast_liquid_vote_rejects_neither_or_both_choices(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    contributor = user_factory(email="delegate@example.com")
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    _add_eligible_participant(organisation=organisation, decision=decision, owner=owner, user=contributor)
    option = create_option(actor=owner, decision=decision, title="Option A", description="d")
    exercise = _open_liquid_democracy_exercise(owner=owner, decision=decision)

    with pytest.raises(EvaluationServiceError):
        cast_liquid_vote(actor=owner, exercise=exercise)
    with pytest.raises(EvaluationServiceError):
        cast_liquid_vote(
            actor=owner, exercise=exercise, option_id=option.id, delegate_to_id=contributor.id
        )


@pytest.mark.django_db
def test_cast_liquid_vote_rejects_self_delegation(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = _open_liquid_democracy_exercise(owner=owner, decision=decision)

    with pytest.raises(EvaluationServiceError):
        cast_liquid_vote(actor=owner, exercise=exercise, delegate_to_id=owner.id)


@pytest.mark.django_db
def test_cast_liquid_vote_rejects_delegation_to_ineligible_participant(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    observer = user_factory(email="observer@example.com")
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    Membership.objects.create(
        organisation=organisation,
        user=observer,
        role=Membership.Role.VIEWER,
        status=Membership.Status.ACTIVE,
    )
    Participant.objects.create(
        organisation=organisation,
        decision=decision,
        user=observer,
        role=Participant.Role.OBSERVER,
        added_by=owner,
    )
    exercise = _open_liquid_democracy_exercise(owner=owner, decision=decision)

    with pytest.raises(EvaluationServiceError):
        cast_liquid_vote(actor=owner, exercise=exercise, delegate_to_id=observer.id)


@pytest.mark.django_db
def test_cast_liquid_vote_rejects_delegation_that_would_create_a_cycle(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    contributor = user_factory(email="contributor@example.com")
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    _add_eligible_participant(organisation=organisation, decision=decision, owner=owner, user=contributor)
    exercise = _open_liquid_democracy_exercise(owner=owner, decision=decision)

    cast_liquid_vote(actor=owner, exercise=exercise, delegate_to_id=contributor.id)
    with pytest.raises(EvaluationServiceError):
        cast_liquid_vote(actor=contributor, exercise=exercise, delegate_to_id=owner.id)


@pytest.mark.django_db
def test_cast_liquid_vote_rejects_when_exercise_not_open(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    option = create_option(actor=owner, decision=decision, title="Option A", description="d")
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Liquid democracy",
        purpose="p",
        method="liquid_democracy",
        quorum_count=1,
    )
    with pytest.raises(EvaluationServiceError):
        cast_liquid_vote(actor=owner, exercise=exercise, option_id=option.id)


@pytest.mark.django_db
def test_cast_liquid_vote_permission_denied_for_non_participant(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    outsider = user_factory(email="outsider@example.com")
    Membership.objects.create(
        organisation=organisation,
        user=outsider,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    option = create_option(actor=owner, decision=decision, title="Option A", description="d")
    exercise = _open_liquid_democracy_exercise(owner=owner, decision=decision)

    with pytest.raises(PermissionDenied):
        cast_liquid_vote(actor=outsider, exercise=exercise, option_id=option.id)


@pytest.mark.django_db
def test_liquid_democracy_tally_empty_when_no_votes(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = _open_liquid_democracy_exercise(owner=owner, decision=decision)

    tally = liquid_democracy_tally(exercise=exercise)
    assert tally["options"] == []
    assert tally["direct_voters"] == []
    assert tally["abstained_count"] == 0
    assert tally["total_vote_count"] == 0


@pytest.mark.django_db
def test_liquid_democracy_tally_resolves_chains_and_counts_delegated_votes_per_direct_voter(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    option_a = create_option(actor=owner, decision=decision, title="Option A", description="d")
    option_b = create_option(actor=owner, decision=decision, title="Option B", description="d")

    direct_a = user_factory(email="direct-a@example.com")
    direct_b = user_factory(email="direct-b@example.com")
    delegator_1 = user_factory(email="delegator-1@example.com")  # -> owner -> direct_a
    delegator_2 = user_factory(email="delegator-2@example.com")  # -> direct_a directly
    delegator_3 = user_factory(email="delegator-3@example.com")  # -> direct_b
    for user in (direct_a, direct_b, delegator_1, delegator_2, delegator_3):
        _add_eligible_participant(organisation=organisation, decision=decision, owner=owner, user=user)

    exercise = _open_liquid_democracy_exercise(owner=owner, decision=decision)

    cast_liquid_vote(actor=direct_a, exercise=exercise, option_id=option_a.id)
    cast_liquid_vote(actor=direct_b, exercise=exercise, option_id=option_b.id)
    cast_liquid_vote(actor=owner, exercise=exercise, delegate_to_id=direct_a.id)
    cast_liquid_vote(actor=delegator_1, exercise=exercise, delegate_to_id=owner.id)  # 2-hop chain
    cast_liquid_vote(actor=delegator_2, exercise=exercise, delegate_to_id=direct_a.id)  # 1-hop
    cast_liquid_vote(actor=delegator_3, exercise=exercise, delegate_to_id=direct_b.id)  # 1-hop

    tally = liquid_democracy_tally(exercise=exercise)

    assert tally["total_vote_count"] == 6
    assert tally["abstained_count"] == 0

    rows = {row["option_id"]: row for row in tally["options"]}
    row_a = rows[str(option_a.id)]
    assert row_a["direct_vote_count"] == 1
    assert row_a["delegated_vote_count"] == 3  # owner, delegator_1 (via owner), delegator_2
    assert row_a["total_vote_count"] == 4

    row_b = rows[str(option_b.id)]
    assert row_b["direct_vote_count"] == 1
    assert row_b["delegated_vote_count"] == 1
    assert row_b["total_vote_count"] == 2

    assert tally["options"][0]["option_id"] == str(option_a.id)  # sorted by total votes desc

    direct_voters = {row["voter_id"]: row for row in tally["direct_voters"]}
    assert direct_voters[str(direct_a.id)]["delegated_vote_count"] == 3
    assert direct_voters[str(direct_b.id)]["delegated_vote_count"] == 1


@pytest.mark.django_db
def test_liquid_democracy_tally_treats_a_stored_cycle_as_abstention_without_hanging(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    """A cycle can't be cast through the service (it's rejected up front), but the
    tally must still resolve one safely - e.g. if one arose from a race, or the
    guard has a gap we haven't found yet. This constructs one directly via the
    ORM, bypassing cast_liquid_vote entirely, to prove the tally never crashes
    or loops on it."""
    organisation = organisation_factory()
    owner = organisation.created_by
    user_b = user_factory(email="user-b@example.com")
    user_c = user_factory(email="user-c@example.com")
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    for user in (user_b, user_c):
        _add_eligible_participant(organisation=organisation, decision=decision, owner=owner, user=user)
    exercise = _open_liquid_democracy_exercise(owner=owner, decision=decision)

    LiquidVote.objects.create(
        organisation=exercise.organisation, exercise=exercise, voter=owner, delegate_to=user_b
    )
    LiquidVote.objects.create(
        organisation=exercise.organisation, exercise=exercise, voter=user_b, delegate_to=user_c
    )
    LiquidVote.objects.create(
        organisation=exercise.organisation, exercise=exercise, voter=user_c, delegate_to=owner
    )

    tally = liquid_democracy_tally(exercise=exercise)

    assert tally["options"] == []
    assert tally["direct_voters"] == []
    assert tally["abstained_count"] == 3
    assert tally["total_vote_count"] == 3


@pytest.mark.django_db
def test_liquid_democracy_tally_treats_dead_end_chain_as_abstention(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    never_voted = user_factory(email="never-voted@example.com")
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    _add_eligible_participant(
        organisation=organisation, decision=decision, owner=owner, user=never_voted
    )
    exercise = _open_liquid_democracy_exercise(owner=owner, decision=decision)

    cast_liquid_vote(actor=owner, exercise=exercise, delegate_to_id=never_voted.id)

    tally = liquid_democracy_tally(exercise=exercise)
    assert tally["options"] == []
    assert tally["abstained_count"] == 1
    assert tally["total_vote_count"] == 1


@pytest.mark.django_db
def test_liquid_democracy_tally_resolves_a_chain_exactly_at_the_depth_cap(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    option = create_option(actor=owner, decision=decision, title="Option A", description="d")
    direct_voter = user_factory(email="direct@example.com")
    delegators = [owner] + [user_factory(email=f"chain{i}@example.com") for i in range(9)]
    for user in delegators[1:] + [direct_voter]:
        _add_eligible_participant(organisation=organisation, decision=decision, owner=owner, user=user)
    exercise = _open_liquid_democracy_exercise(owner=owner, decision=decision)

    # 10 delegators (delegators[0..9]) each pointing to the next, the last pointing
    # to direct_voter, who casts a direct vote - exactly 10 delegation hops.
    assert len(delegators) == 10
    for voter, target in zip(delegators, delegators[1:] + [direct_voter], strict=True):
        cast_liquid_vote(actor=voter, exercise=exercise, delegate_to_id=target.id)
    cast_liquid_vote(actor=direct_voter, exercise=exercise, option_id=option.id)

    tally = liquid_democracy_tally(exercise=exercise)
    assert tally["abstained_count"] == 0
    row = tally["options"][0]
    assert row["direct_vote_count"] == 1
    assert row["delegated_vote_count"] == 10
    direct_row = tally["direct_voters"][0]
    assert direct_row["delegated_vote_count"] == 10


@pytest.mark.django_db
def test_liquid_democracy_tally_abstains_a_chain_one_hop_beyond_the_depth_cap(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    option = create_option(actor=owner, decision=decision, title="Option A", description="d")
    direct_voter = user_factory(email="direct@example.com")
    delegators = [owner] + [user_factory(email=f"chain{i}@example.com") for i in range(10)]
    for user in delegators[1:] + [direct_voter]:
        _add_eligible_participant(organisation=organisation, decision=decision, owner=owner, user=user)
    exercise = _open_liquid_democracy_exercise(owner=owner, decision=decision)

    # 11 delegators before the direct voter. Only delegators[0] is 11 hops away
    # from the direct voter - one beyond the cap - so only it abstains; everyone
    # else in the chain is closer and still resolves. The cap is a per-voter
    # distance limit, not an all-or-nothing property of the whole chain.
    assert len(delegators) == 11
    for voter, target in zip(delegators, delegators[1:] + [direct_voter], strict=True):
        cast_liquid_vote(actor=voter, exercise=exercise, delegate_to_id=target.id)
    cast_liquid_vote(actor=direct_voter, exercise=exercise, option_id=option.id)

    tally = liquid_democracy_tally(exercise=exercise)
    assert tally["abstained_count"] == 1
    row = tally["options"][0]
    assert row["direct_vote_count"] == 1
    assert row["delegated_vote_count"] == 10


@pytest.mark.django_db
def test_cast_liquid_vote_rejects_wrong_method(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    option = create_option(actor=owner, decision=decision, title="Option A", description="d")
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Scorecard",
        purpose="p",
        method="scorecard",
        quorum_count=1,
    )
    with pytest.raises(EvaluationServiceError):
        cast_liquid_vote(actor=owner, exercise=exercise, option_id=option.id)


@pytest.mark.django_db
def test_cast_liquid_vote_rejects_unknown_option_or_delegate(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    import uuid

    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = _open_liquid_democracy_exercise(owner=owner, decision=decision)

    with pytest.raises(EvaluationServiceError):
        cast_liquid_vote(actor=owner, exercise=exercise, option_id=uuid.uuid4())
    with pytest.raises(EvaluationServiceError):
        cast_liquid_vote(actor=owner, exercise=exercise, delegate_to_id=uuid.uuid4())


@pytest.mark.django_db
def test_cast_liquid_vote_allows_delegation_into_a_chain_with_an_unrelated_existing_cycle(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    """B and C already delegate to each other in a 2-cycle that has nothing to do
    with A. A delegating to B should still be allowed - it isn't A's cycle, and
    the tally already knows how to abstain the B/C pair safely regardless."""
    organisation = organisation_factory()
    owner = organisation.created_by
    user_b = user_factory(email="user-b@example.com")
    user_c = user_factory(email="user-c@example.com")
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    for user in (user_b, user_c):
        _add_eligible_participant(organisation=organisation, decision=decision, owner=owner, user=user)
    exercise = _open_liquid_democracy_exercise(owner=owner, decision=decision)

    LiquidVote.objects.create(
        organisation=exercise.organisation, exercise=exercise, voter=user_b, delegate_to=user_c
    )
    LiquidVote.objects.create(
        organisation=exercise.organisation, exercise=exercise, voter=user_c, delegate_to=user_b
    )

    vote = cast_liquid_vote(actor=owner, exercise=exercise, delegate_to_id=user_b.id)
    assert vote.delegate_to_id == user_b.id

    tally = liquid_democracy_tally(exercise=exercise)
    assert tally["abstained_count"] == 3  # owner, user_b, and user_c all resolve to nothing


def _open_opinion_clustering_exercise(*, owner, decision, **overrides):
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title=overrides.pop("title", "Community opinion mapping"),
        purpose=overrides.pop("purpose", "Find where the group agrees and where it splits."),
        method="opinion_clustering",
        quorum_count=overrides.pop("quorum_count", 1),
        **overrides,
    )
    return update_exercise(
        actor=owner, exercise=exercise, fields={"status": EvaluationExercise.Status.OPEN}
    )


@pytest.mark.django_db
def test_create_opinion_statement_requires_opinion_clustering_method(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Scorecard",
        purpose="p",
        method="scorecard",
        quorum_count=1,
    )
    with pytest.raises(EvaluationServiceError):
        create_opinion_statement(actor=owner, exercise=exercise, text="A statement.")


@pytest.mark.django_db
def test_create_opinion_statement_rejects_when_exercise_not_open(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Opinion clustering",
        purpose="p",
        method="opinion_clustering",
        quorum_count=1,
    )
    with pytest.raises(EvaluationServiceError):
        create_opinion_statement(actor=owner, exercise=exercise, text="A statement.")


@pytest.mark.django_db
def test_create_opinion_statement_permission_denied_for_non_participant(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    outsider = user_factory(email="outsider@example.com")
    Membership.objects.create(
        organisation=organisation,
        user=outsider,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = _open_opinion_clustering_exercise(owner=owner, decision=decision)
    with pytest.raises(PermissionDenied):
        create_opinion_statement(actor=outsider, exercise=exercise, text="A statement.")


@pytest.mark.django_db
def test_cast_opinion_vote_happy_path_and_revision(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = _open_opinion_clustering_exercise(owner=owner, decision=decision)
    statement = create_opinion_statement(actor=owner, exercise=exercise, text="A statement.")

    vote = cast_opinion_vote(actor=owner, statement=statement, choice="agree")
    assert vote.choice == "agree"

    revised = cast_opinion_vote(actor=owner, statement=statement, choice="disagree")
    assert revised.id == vote.id
    assert revised.choice == "disagree"
    assert statement.votes.count() == 1


@pytest.mark.django_db
def test_cast_opinion_vote_rejects_when_exercise_not_open(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = _open_opinion_clustering_exercise(owner=owner, decision=decision)
    statement = create_opinion_statement(actor=owner, exercise=exercise, text="A statement.")
    update_exercise(actor=owner, exercise=exercise, fields={"status": EvaluationExercise.Status.CLOSED})

    with pytest.raises(EvaluationServiceError):
        cast_opinion_vote(actor=owner, statement=statement, choice="agree")


@pytest.mark.django_db
def test_opinion_clustering_analysis_insufficient_data_with_no_statements(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = _open_opinion_clustering_exercise(owner=owner, decision=decision)

    result = opinion_clustering_analysis(exercise=exercise)
    assert result["insufficient_data"] is True
    assert result["statements"] == []


@pytest.mark.django_db
def test_opinion_clustering_analysis_insufficient_data_when_no_statement_has_both_sides(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    contributor = user_factory(email="contributor@example.com")
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    _add_eligible_participant(organisation=organisation, decision=decision, owner=owner, user=contributor)
    exercise = _open_opinion_clustering_exercise(owner=owner, decision=decision)
    statement = create_opinion_statement(
        actor=owner, exercise=exercise, text="Everyone agrees on this."
    )
    cast_opinion_vote(actor=owner, statement=statement, choice="agree")
    cast_opinion_vote(actor=contributor, statement=statement, choice="agree")

    result = opinion_clustering_analysis(exercise=exercise)
    assert result["insufficient_data"] is True


@pytest.mark.django_db
def test_opinion_clustering_analysis_classifies_statements_and_excludes_unclustered_voters(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    p1 = organisation.created_by
    p2 = user_factory(email="p2@example.com")
    p3 = user_factory(email="p3@example.com")
    p4 = user_factory(email="p4@example.com")
    p5 = user_factory(email="p5@example.com")  # never votes on the pivot
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=p1)
    for user in (p2, p3, p4, p5):
        _add_eligible_participant(organisation=organisation, decision=decision, owner=p1, user=user)
    exercise = _open_opinion_clustering_exercise(owner=p1, decision=decision)

    # S1: 4 votes, split 2/2 - the most-voted statement with both sides, so it
    # becomes the pivot. cluster_a = {p1, p3} (agree), cluster_b = {p2, p4} (disagree).
    s1 = create_opinion_statement(actor=p1, exercise=exercise, text="S1: the pivot")
    cast_opinion_vote(actor=p1, statement=s1, choice="agree")
    cast_opinion_vote(actor=p2, statement=s1, choice="disagree")
    cast_opinion_vote(actor=p3, statement=s1, choice="agree")
    cast_opinion_vote(actor=p4, statement=s1, choice="disagree")

    # S2: bridging - both clusters agree. p5 also votes here but isn't in either
    # cluster (never voted on S1), so p5's vote must not affect the tally.
    s2 = create_opinion_statement(actor=p1, exercise=exercise, text="S2: bridging")
    cast_opinion_vote(actor=p1, statement=s2, choice="agree")
    cast_opinion_vote(actor=p3, statement=s2, choice="agree")
    cast_opinion_vote(actor=p2, statement=s2, choice="agree")
    cast_opinion_vote(actor=p5, statement=s2, choice="disagree")

    # S3: divisive - clusters take opposite stances.
    s3 = create_opinion_statement(actor=p1, exercise=exercise, text="S3: divisive")
    cast_opinion_vote(actor=p1, statement=s3, choice="agree")
    cast_opinion_vote(actor=p3, statement=s3, choice="agree")
    cast_opinion_vote(actor=p2, statement=s3, choice="disagree")

    # S4: mixed - cluster_a is split down the middle, so neither side is a clean
    # consensus or a clean split.
    s4 = create_opinion_statement(actor=p1, exercise=exercise, text="S4: mixed")
    cast_opinion_vote(actor=p1, statement=s4, choice="agree")
    cast_opinion_vote(actor=p3, statement=s4, choice="disagree")
    cast_opinion_vote(actor=p2, statement=s4, choice="agree")

    result = opinion_clustering_analysis(exercise=exercise)

    assert result["insufficient_data"] is False
    assert result["pivot_statement_id"] == str(s1.id)
    assert result["cluster_a_size"] == 2
    assert result["cluster_b_size"] == 2

    rows = {row["statement_id"]: row for row in result["statements"]}
    assert rows[str(s1.id)]["classification"] == "divisive"  # the pivot is always divisive
    assert rows[str(s2.id)]["classification"] == "bridging"
    assert rows[str(s2.id)]["cluster_a_vote_count"] == 2
    assert rows[str(s2.id)]["cluster_b_vote_count"] == 1  # p5's vote is excluded
    assert rows[str(s3.id)]["classification"] == "divisive"
    assert rows[str(s4.id)]["classification"] == "mixed"

    assert set(result["bridging_statement_ids"]) == {str(s2.id)}
    assert set(result["divisive_statement_ids"]) == {str(s1.id), str(s3.id)}


@pytest.mark.django_db
def test_cast_opinion_vote_permission_denied_for_non_participant(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    outsider = user_factory(email="outsider@example.com")
    Membership.objects.create(
        organisation=organisation,
        user=outsider,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = _open_opinion_clustering_exercise(owner=owner, decision=decision)
    statement = create_opinion_statement(actor=owner, exercise=exercise, text="A statement.")
    with pytest.raises(PermissionDenied):
        cast_opinion_vote(actor=outsider, statement=statement, choice="agree")


@pytest.mark.django_db
def test_opinion_clustering_analysis_reports_no_data_when_a_cluster_never_voted(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    p1 = organisation.created_by
    p2 = user_factory(email="p2@example.com")
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=p1)
    _add_eligible_participant(organisation=organisation, decision=decision, owner=p1, user=p2)
    exercise = _open_opinion_clustering_exercise(owner=p1, decision=decision)

    pivot = create_opinion_statement(actor=p1, exercise=exercise, text="The pivot")
    cast_opinion_vote(actor=p1, statement=pivot, choice="agree")
    cast_opinion_vote(actor=p2, statement=pivot, choice="disagree")

    only_a_votes = create_opinion_statement(actor=p1, exercise=exercise, text="Only p1 voted")
    cast_opinion_vote(actor=p1, statement=only_a_votes, choice="agree")

    result = opinion_clustering_analysis(exercise=exercise)
    rows = {row["statement_id"]: row for row in result["statements"]}
    row = rows[str(only_a_votes.id)]
    assert row["classification"] == "no_data"
    assert row["cluster_a_agree_rate"] == 1.0
    assert row["cluster_b_agree_rate"] is None
