import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_evaluation_api_is_strict_and_tenant_safe(
    api_client, organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    api_client.force_authenticate(owner)
    response = api_client.post(
        reverse("evaluations:decision-evaluations", kwargs={"decision_id": decision.id}),
        {
            "title": "Blind scorecard",
            "purpose": "Compare alternatives independently.",
            "method": "scorecard",
            "anonymity": "peer_anonymous",
            "blind_results_until_close": True,
            "quorum_count": 1,
            "approval_threshold": 60,
            "objection_threshold": 20,
            "owner_id": str(owner.id),
            "manufactured_consensus": True,
        },
        format="json",
    )
    assert response.status_code == 400
    assert "manufactured_consensus" in response.json()

    api_client.force_authenticate(user_factory())
    hidden = api_client.get(
        reverse("evaluations:decision-evaluations", kwargs={"decision_id": decision.id})
    )
    assert hidden.status_code == 404


@pytest.mark.django_db
def test_prioritisation_api_creates_portfolio(api_client, organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    api_client.force_authenticate(owner)
    response = api_client.post(
        reverse(
            "evaluations:prioritisation-portfolios", kwargs={"organisation_id": organisation.id}
        ),
        {
            "title": "Annual investment portfolio",
            "purpose": "Choose initiatives within the delivery envelope.",
            "budget_limit": "100000.00",
            "capacity_limit": "12.00",
            "owner_id": str(owner.id),
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["recommendation"]["warning"].startswith("This is an explainable")


@pytest.mark.django_db
def test_scoring_options_endpoint_blinds_titles_for_non_managers(
    api_client, organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    from apps.decision_options.services import create_option
    from apps.evaluations.services import create_exercise
    from apps.organisations.models import Membership
    from apps.participants.models import Participant

    organisation = organisation_factory()
    owner = organisation.created_by
    reviewer = user_factory(email="scoring-reviewer@example.com")
    Membership.objects.create(
        organisation=organisation,
        user=reviewer,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    Participant.objects.create(
        organisation=organisation,
        decision=decision,
        user=reviewer,
        role=Participant.Role.CONTRIBUTOR,
        added_by=owner,
    )
    create_option(actor=owner, decision=decision, title="Named Applicant Org", description="d")
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Blind scorecard",
        purpose="p",
        method="scorecard",
        blind_applicant_identity=True,
        quorum_count=1,
    )

    api_client.force_authenticate(reviewer)
    response = api_client.get(
        reverse("evaluations:evaluation-scoring-options", kwargs={"exercise_id": exercise.id})
    )
    assert response.status_code == 200
    assert response.json()[0]["title"] == "Application A"
    assert response.json()[0]["blinded"] is True

    api_client.force_authenticate(owner)
    manager_response = api_client.get(
        reverse("evaluations:evaluation-scoring-options", kwargs={"exercise_id": exercise.id})
    )
    assert manager_response.json()[0]["title"] == "Named Applicant Org"
    assert manager_response.json()[0]["blinded"] is False


@pytest.mark.django_db
def test_forecast_question_api_is_strict_and_tenant_safe(
    api_client, organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    from apps.evaluations.models import EvaluationExercise
    from apps.evaluations.services import create_exercise, update_exercise

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
    exercise = update_exercise(
        actor=owner, exercise=exercise, fields={"status": EvaluationExercise.Status.OPEN}
    )

    api_client.force_authenticate(owner)
    strict_response = api_client.post(
        reverse("evaluations:evaluation-forecast-questions", kwargs={"exercise_id": exercise.id}),
        {"question_text": "Will the pilot launch on time?", "unexpected_field": True},
        format="json",
    )
    assert strict_response.status_code == 400
    assert "unexpected_field" in strict_response.json()

    created = api_client.post(
        reverse("evaluations:evaluation-forecast-questions", kwargs={"exercise_id": exercise.id}),
        {"question_text": "Will the pilot launch on time?"},
        format="json",
    )
    assert created.status_code == 201
    assert created.json()["status"] == "open"

    api_client.force_authenticate(user_factory())
    hidden = api_client.post(
        reverse("evaluations:evaluation-forecast-questions", kwargs={"exercise_id": exercise.id}),
        {"question_text": "Will X happen?"},
        format="json",
    )
    assert hidden.status_code == 404


@pytest.mark.django_db
def test_forecast_submission_hides_other_forecasts_until_resolution(
    api_client, organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    from apps.evaluations.models import EvaluationExercise
    from apps.evaluations.services import create_exercise, create_forecast_question, update_exercise
    from apps.organisations.models import Membership
    from apps.participants.models import Participant

    organisation = organisation_factory()
    owner = organisation.created_by
    contributor = user_factory(email="forecaster@example.com")
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
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Forecasting",
        purpose="p",
        method="forecasting",
        quorum_count=1,
    )
    exercise = update_exercise(
        actor=owner, exercise=exercise, fields={"status": EvaluationExercise.Status.OPEN}
    )
    question = create_forecast_question(
        actor=owner, exercise=exercise, question_text="Will X happen?"
    )

    api_client.force_authenticate(owner)
    owner_response = api_client.put(
        reverse("evaluations:forecast-submit", kwargs={"question_id": question.id}),
        {"probability": "70.00"},
        format="json",
    )
    assert owner_response.status_code == 200
    assert owner_response.json()["probability"] == "70.00"

    api_client.force_authenticate(contributor)
    contributor_response = api_client.put(
        reverse("evaluations:forecast-submit", kwargs={"question_id": question.id}),
        {"probability": "30.00"},
        format="json",
    )
    assert contributor_response.status_code == 200

    detail = api_client.get(
        reverse("evaluations:evaluation-detail", kwargs={"exercise_id": exercise.id})
    )
    question_payload = detail.json()["forecast_questions"][0]
    assert len(question_payload["forecasts"]) == 1
    assert question_payload["forecasts"][0]["respondent"]["user"]["email"] == contributor.email

    api_client.force_authenticate(owner)
    resolve_response = api_client.patch(
        reverse("evaluations:forecast-question-resolve", kwargs={"question_id": question.id}),
        {"outcome": True},
        format="json",
    )
    assert resolve_response.status_code == 200
    assert resolve_response.json()["status"] == "resolved"

    detail_after = api_client.get(
        reverse("evaluations:evaluation-detail", kwargs={"exercise_id": exercise.id})
    )
    resolved_payload = detail_after.json()["forecast_questions"][0]
    assert len(resolved_payload["forecasts"]) == 2


@pytest.mark.django_db
def test_forecast_question_resolve_api_rejects_non_manager(
    api_client, organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    from apps.evaluations.models import EvaluationExercise
    from apps.evaluations.services import create_exercise, create_forecast_question, update_exercise
    from apps.organisations.models import Membership
    from apps.participants.models import Participant

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
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Forecasting",
        purpose="p",
        method="forecasting",
        quorum_count=1,
    )
    exercise = update_exercise(
        actor=owner, exercise=exercise, fields={"status": EvaluationExercise.Status.OPEN}
    )
    question = create_forecast_question(
        actor=owner, exercise=exercise, question_text="Will X happen?"
    )

    api_client.force_authenticate(contributor)
    response = api_client.patch(
        reverse("evaluations:forecast-question-resolve", kwargs={"question_id": question.id}),
        {"outcome": True},
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_forecasting_leaderboard_api(
    api_client, organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    from apps.evaluations.models import EvaluationExercise
    from apps.evaluations.services import (
        create_exercise,
        create_forecast_question,
        resolve_forecast_question,
        submit_forecast,
        update_exercise,
    )

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
    exercise = update_exercise(
        actor=owner, exercise=exercise, fields={"status": EvaluationExercise.Status.OPEN}
    )
    question = create_forecast_question(
        actor=owner, exercise=exercise, question_text="Will X happen?"
    )
    submit_forecast(actor=owner, question=question, probability=90)
    resolve_forecast_question(actor=owner, question=question, outcome=True)

    api_client.force_authenticate(owner)
    response = api_client.get(
        reverse(
            "evaluations:forecasting-leaderboard", kwargs={"organisation_id": organisation.id}
        )
    )
    assert response.status_code == 200
    body = response.json()
    assert body[0]["email"] == owner.email
    assert body[0]["rank"] == 1
    assert body[0]["mean_brier_score"] == pytest.approx(0.01)


@pytest.mark.django_db
def test_quadratic_voting_full_flow_and_budget_rejection_via_api(
    api_client, organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    from apps.decision_options.services import create_option
    from apps.evaluations.models import EvaluationRound
    from apps.evaluations.services import create_exercise, create_round, transition_round

    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    option_a = create_option(actor=owner, decision=decision, title="Option A", description="d")
    option_b = create_option(actor=owner, decision=decision, title="Option B", description="d")
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Quadratic voting",
        purpose="p",
        method="quadratic",
        blind_results_until_close=False,
        voice_credit_budget=50,
        quorum_count=1,
    )
    round_item = create_round(actor=owner, exercise=exercise)
    transition_round(actor=owner, round=round_item, status=EvaluationRound.Status.OPEN)

    api_client.force_authenticate(owner)

    over_budget = api_client.put(
        reverse("evaluations:evaluation-submission", kwargs={"round_id": round_item.id}),
        {
            "confidence": 4,
            "overall_rationale": "",
            "responses": [
                {"option_id": str(option_a.id), "quadratic_votes": 6},  # 36
                {"option_id": str(option_b.id), "quadratic_votes": 4},  # 16, total 52 > 50
            ],
        },
        format="json",
    )
    assert over_budget.status_code == 400
    assert "responses" in over_budget.json()

    within_budget = api_client.put(
        reverse("evaluations:evaluation-submission", kwargs={"round_id": round_item.id}),
        {
            "confidence": 4,
            "overall_rationale": "",
            "responses": [{"option_id": str(option_a.id), "quadratic_votes": -7}],  # 49
        },
        format="json",
    )
    assert within_budget.status_code == 200
    assert within_budget.json()["responses"][0]["quadratic_votes"] == -7

    results = api_client.get(
        reverse("evaluations:evaluation-results", kwargs={"round_id": round_item.id})
    )
    assert results.status_code == 200
    body = results.json()
    row = next(r for r in body["options"] if r["option_id"] == str(option_a.id))
    assert row["net_votes"] == -7
    assert row["oppose_votes"] == 7
    assert row["credits_spent"] == 49
