import pytest
from django.core.exceptions import PermissionDenied

from apps.decision_options.services import create_option
from apps.evaluations.models import (
    EvaluationExercise,
    EvaluationRound,
    ForecastQuestion,
    PrioritisationPortfolio,
)
from apps.evaluations.services import (
    EvaluationServiceError,
    add_candidate,
    add_portfolio_criterion,
    create_criterion,
    create_exercise,
    create_forecast_question,
    create_minority_report,
    create_portfolio,
    create_round,
    evaluation_results,
    forecasting_leaderboard,
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
