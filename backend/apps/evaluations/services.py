"""Transactional collective evaluation and prioritisation workflows."""

from __future__ import annotations

import builtins
from collections import Counter, defaultdict
from decimal import ROUND_HALF_UP, Decimal
from statistics import mean, pstdev
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count, Max
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.services import record_event
from apps.decision_options.models import DecisionOption
from apps.notifications.models import Notification
from apps.notifications.services import notify_users
from apps.organisations.models import Membership
from apps.participants.models import ConflictOfInterest
from apps.participants.services import conflicts_for_decision

from .models import (
    EvaluationCriterion,
    EvaluationExercise,
    EvaluationResponse,
    EvaluationRound,
    EvaluationSubmission,
    Forecast,
    ForecastQuestion,
    LiquidVote,
    MinorityReport,
    OpinionStatement,
    OpinionVote,
    PortfolioAssessment,
    PortfolioCandidate,
    PortfolioCriterion,
    PortfolioSelection,
    PrioritisationPortfolio,
)
from .policies import (
    can_assess_portfolio,
    can_manage_exercise,
    can_manage_portfolio,
    can_submit_evaluation,
)

APPLICATION_LABEL_FORMAT = "Application {index}"

ROUNDLESS_METHODS = {
    EvaluationExercise.Method.FORECASTING,
    EvaluationExercise.Method.LIQUID_DEMOCRACY,
    EvaluationExercise.Method.OPINION_CLUSTERING,
}

OPINION_CLUSTER_CONSENSUS_THRESHOLD = 0.7

MAX_DELEGATION_CHAIN_DEPTH = 10


def scoring_options_for_exercise(*, exercise, viewer):
    """Active options for the scoring/ballot form, blinded to 'Application N' for non-managers.

    Blinding only applies while the exercise hasn't closed - once closed, the
    real title is restored for everyone, matching the plan's "revealed after
    the round closes" rule. A manager always sees the real title, since they
    administer eligibility/outcome regardless of blinding.
    """
    active_options = list(
        exercise.decision.options.filter(status=DecisionOption.Status.ACTIVE).order_by(
            "created_at", "id"
        )
    )
    reveal = (
        not exercise.blind_applicant_identity
        or exercise.status in {EvaluationExercise.Status.CLOSED, EvaluationExercise.Status.ARCHIVED}
        or can_manage_exercise(actor=viewer, exercise=exercise)
    )
    rows = []
    for index, option in enumerate(active_options):
        rows.append(
            {
                "id": str(option.id),
                "title": option.title
                if reveal
                else APPLICATION_LABEL_FORMAT.format(
                    index=chr(65 + index) if index < 26 else index + 1
                ),
                "blinded": not reveal,
            }
        )
    return rows


class EvaluationServiceError(ValidationError):
    pass


def _active_member(*, organisation, user_id):
    try:
        return (
            Membership.objects.select_related("user")
            .get(organisation=organisation, user_id=user_id, status=Membership.Status.ACTIVE)
            .user
        )
    except Membership.DoesNotExist as exc:
        raise EvaluationServiceError({"owner_id": "Choose an active organisation member."}) from exc


@transaction.atomic
def create_exercise(*, actor, decision, owner_id, **fields):
    membership = decision.organisation.memberships.filter(
        user=actor, status=Membership.Status.ACTIVE
    ).first()
    if membership is None or not (
        membership.role in {Membership.Role.OWNER, Membership.Role.ADMIN}
        or decision.owner_id == actor.id
    ):
        raise PermissionDenied(
            "Only the decision owner or an organisation manager may create an evaluation."
        )
    exercise = EvaluationExercise(
        organisation=decision.organisation,
        decision=decision,
        owner=_active_member(organisation=decision.organisation, user_id=owner_id),
        created_by=actor,
        **fields,
    )
    exercise.full_clean(validate_unique=False, validate_constraints=False)
    exercise.save()
    record_event(
        action="evaluation.exercise_created",
        object_type="evaluations.EvaluationExercise",
        object_id=str(exercise.id),
        actor=actor,
        organisation=decision.organisation,
        metadata={"decision_id": str(decision.id), "method": exercise.method},
    )
    return exercise


@transaction.atomic
def update_exercise(*, actor, exercise, fields):
    exercise = (
        EvaluationExercise.objects.select_for_update()
        .select_related("decision", "organisation", "owner")
        .get(id=exercise.id)
    )
    if not can_manage_exercise(actor=actor, exercise=exercise):
        raise PermissionDenied("You cannot manage this evaluation.")
    if exercise.status == EvaluationExercise.Status.ARCHIVED:
        raise EvaluationServiceError("Archived evaluations cannot be changed.")
    requested_status = fields.get("status")
    if requested_status is not None and requested_status != exercise.status:
        if exercise.method in ROUNDLESS_METHODS:
            allowed = {
                (EvaluationExercise.Status.DRAFT, EvaluationExercise.Status.OPEN),
                (EvaluationExercise.Status.OPEN, EvaluationExercise.Status.CLOSED),
                (EvaluationExercise.Status.CLOSED, EvaluationExercise.Status.ARCHIVED),
            }
            if (exercise.status, requested_status) not in allowed:
                raise EvaluationServiceError(
                    {"status": "Use the governed draft, open, closed, and archived sequence."}
                )
        elif not (
            exercise.status == EvaluationExercise.Status.CLOSED
            and requested_status == EvaluationExercise.Status.ARCHIVED
        ):
            raise EvaluationServiceError(
                {
                    "status": "Evaluation status is controlled by round transitions; only a closed exercise may be archived here."
                }
            )
    editable_after_start = {"owner_id", "status"}
    if exercise.status != EvaluationExercise.Status.DRAFT and any(
        key not in editable_after_start for key in fields
    ):
        raise EvaluationServiceError(
            "Evaluation governance can be changed only before the first round opens."
        )
    for key, value in fields.items():
        if key == "owner_id":
            exercise.owner = _active_member(organisation=exercise.organisation, user_id=value)
        else:
            setattr(exercise, key, value)
    exercise.full_clean(validate_unique=False, validate_constraints=False)
    exercise.save()
    record_event(
        action="evaluation.exercise_updated",
        object_type="evaluations.EvaluationExercise",
        object_id=str(exercise.id),
        actor=actor,
        organisation=exercise.organisation,
        metadata={"fields": sorted(fields)},
    )
    return exercise


@transaction.atomic
def create_criterion(*, actor, exercise, **fields):
    if not can_manage_exercise(actor=actor, exercise=exercise):
        raise PermissionDenied("You cannot manage this evaluation.")
    if exercise.status != EvaluationExercise.Status.DRAFT:
        raise EvaluationServiceError("Criteria can be changed only while the exercise is draft.")
    criterion = EvaluationCriterion(organisation=exercise.organisation, exercise=exercise, **fields)
    criterion.full_clean(validate_unique=False, validate_constraints=False)
    try:
        criterion.save()
    except IntegrityError as exc:
        raise EvaluationServiceError(
            {"title": "Criterion titles must be unique within an exercise."}
        ) from exc
    record_event(
        action="evaluation.criterion_created",
        object_type="evaluations.EvaluationCriterion",
        object_id=str(criterion.id),
        actor=actor,
        organisation=exercise.organisation,
        metadata={"exercise_id": str(exercise.id), "weight": criterion.weight},
    )
    return criterion


@transaction.atomic
def create_round(*, actor, exercise, title=""):
    exercise = (
        EvaluationExercise.objects.select_for_update()
        .select_related("decision", "organisation", "owner")
        .get(id=exercise.id)
    )
    if not can_manage_exercise(actor=actor, exercise=exercise):
        raise PermissionDenied("You cannot manage this evaluation.")
    if exercise.method in ROUNDLESS_METHODS:
        raise EvaluationServiceError(
            f"{exercise.get_method_display()} exercises do not use rounds."
        )
    if exercise.status == EvaluationExercise.Status.ARCHIVED:
        raise EvaluationServiceError("Archived evaluations cannot receive new rounds.")
    if exercise.rounds.filter(status=EvaluationRound.Status.OPEN).exists():
        raise EvaluationServiceError("Close the current round before creating another round.")
    if exercise.method != EvaluationExercise.Method.DELPHI and exercise.rounds.exists():
        raise EvaluationServiceError("Only Delphi exercises may contain multiple rounds.")
    number = (exercise.rounds.aggregate(value=Max("number"))["value"] or 0) + 1
    item = EvaluationRound(
        organisation=exercise.organisation, exercise=exercise, number=number, title=title
    )
    item.full_clean(validate_unique=False, validate_constraints=False)
    item.save()
    record_event(
        action="evaluation.round_created",
        object_type="evaluations.EvaluationRound",
        object_id=str(item.id),
        actor=actor,
        organisation=exercise.organisation,
        metadata={"exercise_id": str(exercise.id), "number": number},
    )
    return item


@transaction.atomic
def transition_round(*, actor, round, status, feedback_summary=""):
    item = (
        EvaluationRound.objects.select_for_update()
        .select_related("exercise__decision", "exercise__organisation", "exercise__owner")
        .get(id=round.id)
    )
    if not can_manage_exercise(actor=actor, exercise=item.exercise):
        raise PermissionDenied("You cannot manage this evaluation round.")
    if status == EvaluationRound.Status.OPEN:
        if item.status != EvaluationRound.Status.DRAFT:
            raise EvaluationServiceError("Only a draft round can be opened.")
        exercise = item.exercise
        if (
            exercise.method
            in {EvaluationExercise.Method.SCORECARD, EvaluationExercise.Method.DELPHI}
            and not exercise.criteria.exists()
        ):
            raise EvaluationServiceError(
                "Add at least one weighted criterion before opening this round."
            )
        if not exercise.decision.options.filter(status=DecisionOption.Status.ACTIVE).exists():
            raise EvaluationServiceError("The decision needs at least one active option.")
        item.status = status
        item.opens_at = timezone.now()
        item.opened_by = actor
        exercise.status = EvaluationExercise.Status.OPEN
        exercise.save(update_fields=["status", "updated_at"])
    elif status == EvaluationRound.Status.CLOSED:
        if item.status != EvaluationRound.Status.OPEN:
            raise EvaluationServiceError("Only an open round can be closed.")
        item.status = status
        item.closes_at = timezone.now()
        item.closed_by = actor
        item.feedback_summary = feedback_summary.strip()
        item.exercise.status = EvaluationExercise.Status.CLOSED
        item.exercise.save(update_fields=["status", "updated_at"])
    else:
        raise EvaluationServiceError("Use the explicit open or closed transition.")
    item.full_clean(validate_unique=False, validate_constraints=False)
    item.save()
    record_event(
        action=f"evaluation.round_{status}",
        object_type="evaluations.EvaluationRound",
        object_id=str(item.id),
        actor=actor,
        organisation=item.organisation,
        metadata={"exercise_id": str(item.exercise_id), "number": item.number},
    )
    recipients = [
        participant.user
        for participant in item.exercise.decision.participants.filter(status="active")
        .exclude(role="observer")
        .select_related("user")
    ]
    if status == EvaluationRound.Status.OPEN:
        notify_users(
            recipients=recipients,
            organisation=item.organisation,
            decision=item.exercise.decision,
            kind=Notification.Kind.COLLABORATION,
            title="Collective evaluation round opened",
            message=f"Round {item.number} of ‘{item.exercise.title}’ is open for independent contribution.",
            url=f"/decisions/{item.exercise.decision_id}/evaluations",
            metadata={"exercise_id": str(item.exercise_id), "round_id": str(item.id)},
            dedup_key_prefix=f"evaluation-round-open:{item.id}",
            exclude_user_id=actor.id,
        )
    else:
        notify_users(
            recipients=recipients,
            organisation=item.organisation,
            decision=item.exercise.decision,
            kind=Notification.Kind.COLLABORATION,
            title="Collective evaluation results available",
            message=f"Round {item.number} of ‘{item.exercise.title}’ has closed and its governed results are available.",
            url=f"/decisions/{item.exercise.decision_id}/evaluations",
            metadata={"exercise_id": str(item.exercise_id), "round_id": str(item.id)},
            dedup_key_prefix=f"evaluation-round-closed:{item.id}",
        )
    return item


def _validate_responses(*, exercise, responses):
    active_options = {
        str(item.id): item
        for item in exercise.decision.options.filter(status=DecisionOption.Status.ACTIVE)
    }
    criteria = {str(item.id): item for item in exercise.criteria.all()}
    expected_scorecard = exercise.method in {
        EvaluationExercise.Method.SCORECARD,
        EvaluationExercise.Method.DELPHI,
    }
    is_ranked_choice = exercise.method == EvaluationExercise.Method.RANKED_CHOICE
    is_quadratic = exercise.method == EvaluationExercise.Method.QUADRATIC
    cleaned = []
    seen = set()
    ranks_used = set()
    credits_spent = 0
    for value in responses:
        option = active_options.get(str(value["option_id"]))
        if option is None:
            raise EvaluationServiceError(
                {"responses": "Every response must use an active option from this decision."}
            )
        criterion = None
        if value.get("criterion_id"):
            criterion = criteria.get(str(value["criterion_id"]))
            if criterion is None:
                raise EvaluationServiceError(
                    {"responses": "Every criterion must belong to this evaluation."}
                )
        key = (option.id, criterion.id if criterion else None)
        if key in seen:
            raise EvaluationServiceError(
                {"responses": "Each option and criterion may be answered once."}
            )
        seen.add(key)
        if expected_scorecard and criterion is None:
            raise EvaluationServiceError({"responses": "Scorecard responses require a criterion."})
        if expected_scorecard and (value.get("score") is None or value.get("vote")):
            raise EvaluationServiceError(
                {"responses": "Scorecard responses require a score and do not use ballots."}
            )
        if not expected_scorecard and criterion is not None:
            raise EvaluationServiceError({"responses": "Ballot responses do not use criteria."})
        if not expected_scorecard and value.get("score") is not None:
            raise EvaluationServiceError({"responses": "Ballot responses do not use scores."})
        if is_ranked_choice:
            rank = value.get("rank")
            if rank is None:
                raise EvaluationServiceError({"responses": "Every option must receive a rank."})
            if rank < 1 or rank > len(active_options):
                raise EvaluationServiceError(
                    {
                        "responses": "Ranks must run from 1 to the number of active options, with no gaps or repeats."
                    }
                )
            if rank in ranks_used:
                raise EvaluationServiceError(
                    {"responses": "Each rank may be used once - this is a strict preference order."}
                )
            ranks_used.add(rank)
            if value.get("vote"):
                raise EvaluationServiceError(
                    {"responses": "Ranked-choice responses do not use a vote."}
                )
        elif is_quadratic:
            votes = value.get("quadratic_votes")
            if not votes:
                raise EvaluationServiceError(
                    {"responses": "Every quadratic-ballot response must cast a non-zero number of votes."}
                )
            if value.get("vote"):
                raise EvaluationServiceError(
                    {"responses": "Quadratic ballot responses do not use a vote."}
                )
            credits_spent += votes**2
        elif exercise.method == EvaluationExercise.Method.APPROVAL and value.get("vote") not in {
            EvaluationResponse.Vote.APPROVE,
            EvaluationResponse.Vote.ABSTAIN,
        }:
            raise EvaluationServiceError(
                {"responses": "Approval rounds accept only approve or abstain."}
            )
        elif exercise.method == EvaluationExercise.Method.CONSENT and value.get("vote") not in {
            EvaluationResponse.Vote.CONSENT,
            EvaluationResponse.Vote.CONCERN,
            EvaluationResponse.Vote.OBJECT,
            EvaluationResponse.Vote.ABSTAIN,
        }:
            raise EvaluationServiceError(
                {"responses": "Consent rounds accept consent, concern, objection, or abstention."}
            )
        cleaned.append((option, criterion, value))
    if not cleaned:
        raise EvaluationServiceError({"responses": "Submit at least one response."})
    if is_quadratic and credits_spent > exercise.voice_credit_budget:
        raise EvaluationServiceError(
            {
                "responses": f"This ballot costs {credits_spent} credits, exceeding the {exercise.voice_credit_budget}-credit voice-credit budget."
            }
        )
    return cleaned


@transaction.atomic
def save_submission(*, actor, round, confidence, overall_rationale, responses, submit=True):
    item = (
        EvaluationRound.objects.select_for_update()
        .select_related("exercise__decision", "exercise__organisation", "exercise__owner")
        .prefetch_related("exercise__criteria", "exercise__decision__options")
        .get(id=round.id)
    )
    if item.status != EvaluationRound.Status.OPEN:
        raise EvaluationServiceError("This evaluation round is not open.")
    if not can_submit_evaluation(actor=actor, exercise=item.exercise):
        raise PermissionDenied("Only active, non-observer decision participants may contribute.")
    cleaned = _validate_responses(exercise=item.exercise, responses=responses)
    if submit and item.exercise.method != EvaluationExercise.Method.QUADRATIC:
        active_option_count = item.exercise.decision.options.filter(
            status=DecisionOption.Status.ACTIVE
        ).count()
        expected_count = active_option_count * (
            item.exercise.criteria.count()
            if item.exercise.method
            in {EvaluationExercise.Method.SCORECARD, EvaluationExercise.Method.DELPHI}
            else 1
        )
        if len(cleaned) != expected_count:
            raise EvaluationServiceError(
                {
                    "responses": "A submitted evaluation must answer every active option and applicable criterion. Save a draft for incomplete work."
                }
            )
    submission, _ = EvaluationSubmission.objects.select_for_update().get_or_create(
        round=item, submitted_by=actor, defaults={"organisation": item.organisation}
    )
    submission.confidence = confidence
    submission.overall_rationale = overall_rationale
    submission.status = (
        EvaluationSubmission.Status.SUBMITTED if submit else EvaluationSubmission.Status.DRAFT
    )
    submission.submitted_at = timezone.now() if submit else None
    submission.full_clean(validate_unique=False, validate_constraints=False)
    submission.save()
    submission.responses.all().delete()
    for option, criterion, value in cleaned:
        response = EvaluationResponse(
            organisation=item.organisation,
            submission=submission,
            option=option,
            criterion=criterion,
            score=value.get("score"),
            vote=value.get("vote", ""),
            rank=value.get("rank"),
            quadratic_votes=value.get("quadratic_votes"),
            rationale=value.get("rationale", ""),
        )
        response.full_clean(validate_unique=False, validate_constraints=False)
        response.save()
    record_event(
        action="evaluation.submission_submitted" if submit else "evaluation.submission_saved",
        object_type="evaluations.EvaluationSubmission",
        object_id=str(submission.id),
        actor=actor,
        organisation=item.organisation,
        metadata={
            "round_id": str(item.id),
            "response_count": len(cleaned),
            "status": submission.status,
        },
    )
    return submission


@transaction.atomic
def create_minority_report(*, actor, exercise, round_id=None, **fields):
    if not can_submit_evaluation(actor=actor, exercise=exercise):
        raise PermissionDenied("Only eligible decision participants may publish a minority report.")
    round = None
    if round_id:
        try:
            round = exercise.rounds.get(id=round_id)
        except EvaluationRound.DoesNotExist as exc:
            raise EvaluationServiceError(
                {"round_id": "Select a round from this exercise."}
            ) from exc
    report = MinorityReport(
        organisation=exercise.organisation, exercise=exercise, round=round, author=actor, **fields
    )
    report.full_clean(validate_unique=False, validate_constraints=False)
    report.save()
    record_event(
        action="evaluation.minority_report_published",
        object_type="evaluations.MinorityReport",
        object_id=str(report.id),
        actor=actor,
        organisation=exercise.organisation,
        metadata={"exercise_id": str(exercise.id), "round_id": str(round.id) if round else None},
    )
    return report


def evaluation_results(*, round, viewer):
    exercise = round.exercise
    submitted = list(
        round.submissions.filter(status=EvaluationSubmission.Status.SUBMITTED).prefetch_related(
            "responses__option", "responses__criterion", "submitted_by"
        )
    )
    eligible = (
        exercise.decision.participants.filter(status="active")
        .exclude(role="observer")
        .values("user_id")
        .distinct()
        .count()
    )
    hidden = exercise.blind_results_until_close and round.status != EvaluationRound.Status.CLOSED
    base = {
        "hidden": hidden,
        "round_id": str(round.id),
        "submission_count": len(submitted),
        "eligible_count": eligible,
        "quorum_count": exercise.quorum_count,
        "quorum_met": len(submitted) >= exercise.quorum_count,
        "method": exercise.method,
        "options": [],
        "criterion_sensitivity": [],
        "tornado": None,
        "uncertainty_narrative": "",
        "ranked_choice_rounds": [],
    }
    if hidden:
        return base
    conflicts = list(conflicts_for_decision(decision=exercise.decision))
    decision_wide_conflicts = {
        c.participant.user_id for c in conflicts if c.scope == ConflictOfInterest.Scope.DECISION
    }
    option_conflicts = {
        (c.participant.user_id, c.option_id)
        for c in conflicts
        if c.scope == ConflictOfInterest.Scope.OPTION
    }
    excluded_emails_by_option = defaultdict(set)

    def _is_conflicted(user_id, option_id):
        return user_id in decision_wide_conflicts or (user_id, option_id) in option_conflicts

    if exercise.method in {EvaluationExercise.Method.SCORECARD, EvaluationExercise.Method.DELPHI}:
        criteria = list(exercise.criteria.all())
        total_weight = sum((c.weight for c in criteria), Decimal("0")) or Decimal("1")
        values: dict[Any, dict[Any, list[float]]] = defaultdict(lambda: defaultdict(list))
        confidences = defaultdict(list)
        option_map = {}
        per_submission_scores: dict[Any, dict[Any, dict[Any, float]]] = defaultdict(
            lambda: defaultdict(dict)
        )
        for submission in submitted:
            for response in submission.responses.all():
                if response.criterion_id and response.score is not None:
                    if _is_conflicted(submission.submitted_by_id, response.option_id):
                        excluded_emails_by_option[response.option_id].add(
                            submission.submitted_by.email
                        )
                        continue
                    values[response.option_id][response.criterion_id].append(float(response.score))
                    confidences[response.option_id].append(submission.confidence)
                    option_map[response.option_id] = response.option
                    per_submission_scores[submission.id][response.option_id][
                        response.criterion_id
                    ] = float(response.score)
        rows = []
        for option_id, option in option_map.items():
            weighted = 0.0
            coverage = 0.0
            criterion_rows = []
            for criterion in criteria:
                raw = values[option_id].get(criterion.id, [])
                avg = mean(raw) if raw else None
                normalised = None
                if avg is not None:
                    span = criterion.scale_max - criterion.scale_min
                    normalised = (avg - criterion.scale_min) / span * 100
                    if not criterion.higher_is_better:
                        normalised = 100 - normalised
                    weighted += normalised * float(criterion.weight / total_weight)
                    coverage += float(criterion.weight / total_weight)
                criterion_rows.append(
                    {
                        "criterion_id": str(criterion.id),
                        "title": criterion.title,
                        "mean_score": round_number(avg),
                        "normalised_score": round_number(normalised),
                        "response_count": len(raw),
                    }
                )
            individual_scores = _individual_weighted_scores(
                option_id=option_id,
                criteria=criteria,
                total_weight=total_weight,
                per_submission_scores=per_submission_scores,
            )
            dispersion = pstdev(individual_scores) if len(individual_scores) >= 2 else None
            rows.append(
                {
                    "option_id": str(option.id),
                    "title": option.title,
                    "weighted_score": builtins.round(weighted / coverage, 2) if coverage else None,
                    "confidence": builtins.round(mean(confidences[option_id]), 2)
                    if confidences[option_id]
                    else None,
                    "score_stdev": round_number(dispersion),
                    "score_min": round_number(min(individual_scores))
                    if individual_scores
                    else None,
                    "score_max": round_number(max(individual_scores))
                    if individual_scores
                    else None,
                    "disagreement": _disagreement_label(dispersion),
                    "criteria": criterion_rows,
                    "excluded_response_count": len(excluded_emails_by_option.get(option_id, ())),
                    "conflicted_reviewer_emails": sorted(
                        excluded_emails_by_option.get(option_id, ())
                    ),
                }
            )
        rows.sort(
            key=lambda x: (x["weighted_score"] is not None, x["weighted_score"] or -1), reverse=True
        )
        base["options"] = rows
        base["criterion_sensitivity"] = _sensitivity(rows=rows, criteria=criteria, values=values)
        base["tornado"] = _tornado(rows=rows, criteria=criteria, values=values)
        base["uncertainty_narrative"] = _uncertainty_narrative(
            rows=rows, criterion_sensitivity=base["criterion_sensitivity"]
        )
    elif exercise.method == EvaluationExercise.Method.RANKED_CHOICE:
        option_map = {}
        ballots = []
        for submission in submitted:
            if any(
                _is_conflicted(submission.submitted_by_id, response.option_id)
                for response in submission.responses.all()
            ):
                for response in submission.responses.all():
                    excluded_emails_by_option[response.option_id].add(submission.submitted_by.email)
                continue
            preferences = sorted(
                submission.responses.all(), key=lambda r: r.rank if r.rank is not None else 999
            )
            ballot = [response.option_id for response in preferences if response.rank is not None]
            for response in preferences:
                option_map[response.option_id] = response.option
            if ballot:
                ballots.append(ballot)
        base["options"], base["ranked_choice_rounds"] = _instant_runoff(
            option_map=option_map, ballots=ballots
        )
        for row in base["options"]:
            option_uuid = next((oid for oid in option_map if str(oid) == row["option_id"]), None)
            row["excluded_response_count"] = len(excluded_emails_by_option.get(option_uuid, ()))
            row["conflicted_reviewer_emails"] = sorted(
                excluded_emails_by_option.get(option_uuid, ())
            )
        if base["options"]:
            winner = base["options"][0]
            base["uncertainty_narrative"] = (
                f"“{winner['title']}” wins by instant runoff after "
                f"{len(base.get('ranked_choice_rounds', []))} elimination round(s)."
            )
    elif exercise.method == EvaluationExercise.Method.QUADRATIC:
        grouped = defaultdict(list)
        option_map = {}
        for submission in submitted:
            for response in submission.responses.all():
                if _is_conflicted(submission.submitted_by_id, response.option_id):
                    excluded_emails_by_option[response.option_id].add(submission.submitted_by.email)
                    continue
                grouped[response.option_id].append(response.quadratic_votes)
                option_map[response.option_id] = response.option
        rows = []
        for option_id, votes in grouped.items():
            support_votes = sum(v for v in votes if v > 0)
            oppose_votes = sum(-v for v in votes if v < 0)
            rows.append(
                {
                    "option_id": str(option_id),
                    "title": option_map[option_id].title,
                    "net_votes": support_votes - oppose_votes,
                    "support_votes": support_votes,
                    "oppose_votes": oppose_votes,
                    "voter_count": len(votes),
                    "credits_spent": sum(v * v for v in votes),
                    "excluded_response_count": len(excluded_emails_by_option.get(option_id, ())),
                    "conflicted_reviewer_emails": sorted(
                        excluded_emails_by_option.get(option_id, ())
                    ),
                }
            )
        rows.sort(key=lambda x: x["net_votes"], reverse=True)
        base["options"] = rows
        if rows:
            leader = rows[0]
            base["uncertainty_narrative"] = (
                f"“{leader['title']}” leads with a net {leader['net_votes']} vote(s) "
                f"across {leader['voter_count']} voter(s)."
            )
    else:
        grouped = defaultdict(list)
        option_map = {}
        for submission in submitted:
            for response in submission.responses.all():
                if _is_conflicted(submission.submitted_by_id, response.option_id):
                    excluded_emails_by_option[response.option_id].add(submission.submitted_by.email)
                    continue
                grouped[response.option_id].append(response.vote)
                option_map[response.option_id] = response.option
        rows = []
        for option_id, votes in grouped.items():
            non_abstain = [v for v in votes if v != EvaluationResponse.Vote.ABSTAIN]
            approvals = sum(
                v in {EvaluationResponse.Vote.APPROVE, EvaluationResponse.Vote.CONSENT}
                for v in non_abstain
            )
            objections = sum(v == EvaluationResponse.Vote.OBJECT for v in non_abstain)
            approval_rate = (approvals / len(non_abstain) * 100) if non_abstain else 0
            objection_rate = (objections / len(non_abstain) * 100) if non_abstain else 0
            passes = (
                approval_rate >= float(exercise.approval_threshold)
                if exercise.method == EvaluationExercise.Method.APPROVAL
                else objection_rate <= float(exercise.objection_threshold)
            )
            if non_abstain:
                majority_count = Counter(non_abstain).most_common(1)[0][1]
                dissent_rate = builtins.round(
                    (len(non_abstain) - majority_count) / len(non_abstain) * 100, 2
                )
            else:
                dissent_rate = 0
            rows.append(
                {
                    "option_id": str(option_id),
                    "title": option_map[option_id].title,
                    "vote_count": len(votes),
                    "approval_rate": builtins.round(approval_rate, 2),
                    "objection_rate": builtins.round(objection_rate, 2),
                    "dissent_rate": dissent_rate,
                    "passes_threshold": passes,
                    "breakdown": {
                        choice: votes.count(choice) for choice, _ in EvaluationResponse.Vote.choices
                    },
                    "excluded_response_count": len(excluded_emails_by_option.get(option_id, ())),
                    "conflicted_reviewer_emails": sorted(
                        excluded_emails_by_option.get(option_id, ())
                    ),
                }
            )
        rows.sort(
            key=lambda x: (x["passes_threshold"], x["approval_rate"], -x["objection_rate"]),
            reverse=True,
        )
        base["options"] = rows
        if rows:
            leader = rows[0]
            if leader["dissent_rate"] > 0:
                base["uncertainty_narrative"] = (
                    f"“{leader['title']}” currently leads, but {leader['dissent_rate']}% of non-abstaining votes dissented from the majority position."
                )
            else:
                base["uncertainty_narrative"] = (
                    f"“{leader['title']}” currently leads with no recorded dissent among non-abstaining votes."
                )
    return base


def _individual_weighted_scores(*, option_id, criteria, total_weight, per_submission_scores):
    """Each submitter's own weighted score for one option, so dispersion reflects evaluator disagreement."""
    scores = []
    for option_scores in per_submission_scores.values():
        answered = option_scores.get(option_id)
        if not answered:
            continue
        weighted = 0.0
        coverage = 0.0
        for criterion in criteria:
            if criterion.id not in answered:
                continue
            span = criterion.scale_max - criterion.scale_min
            normalised = (answered[criterion.id] - criterion.scale_min) / span * 100
            if not criterion.higher_is_better:
                normalised = 100 - normalised
            fraction = float(criterion.weight / total_weight)
            weighted += normalised * fraction
            coverage += fraction
        if coverage:
            scores.append(weighted / coverage)
    return scores


def _disagreement_label(stdev):
    """Thresholds are on the 0-100 normalised score scale, not raw criterion units."""
    if stdev is None:
        return "insufficient_data"
    if stdev < 7:
        return "low"
    if stdev < 15:
        return "moderate"
    return "high"


def round_number(value):
    return round(value, 2) if value is not None else None


def _simulate_scores(*, criteria, values, weights, total):
    """Recompute every option's weighted score under a hypothetical set of criterion weights."""
    scores = {}
    for option_id in values:
        score = 0.0
        coverage = 0.0
        for criterion in criteria:
            raw = values[option_id].get(criterion.id, [])
            if not raw:
                continue
            avg = mean(raw)
            normalised = (
                (avg - criterion.scale_min) / (criterion.scale_max - criterion.scale_min) * 100
            )
            if not criterion.higher_is_better:
                normalised = 100 - normalised
            fraction = float(weights[criterion.id] / total)
            score += normalised * fraction
            coverage += fraction
        scores[option_id] = score / coverage if coverage else None
    return scores


def _perturbed_weights(*, criteria, changed, factor):
    weights = {c.id: c.weight * (factor if c.id == changed.id else Decimal("1")) for c in criteria}
    total = sum(weights.values(), Decimal("0")) or Decimal("1")
    return weights, total


def _sensitivity(*, rows, criteria, values):
    if not rows or not criteria:
        return []
    base_rank = {row["option_id"]: index + 1 for index, row in enumerate(rows)}
    rank_ranges = {key: [rank] for key, rank in base_rank.items()}
    for changed in criteria:
        for factor in (Decimal("0.75"), Decimal("1.25")):
            weights, total = _perturbed_weights(criteria=criteria, changed=changed, factor=factor)
            scores = _simulate_scores(
                criteria=criteria, values=values, weights=weights, total=total
            )
            simulated = sorted(
                (
                    (str(option_id), score if score is not None else -1.0)
                    for option_id, score in scores.items()
                ),
                key=lambda pair: pair[1],
                reverse=True,
            )
            for index, (option_id, _) in enumerate(simulated):
                rank_ranges[option_id].append(index + 1)
    return [
        {
            "option_id": oid,
            "base_rank": base_rank[oid],
            "best_rank": min(ranks),
            "worst_rank": max(ranks),
            "stable": min(ranks) == max(ranks),
        }
        for oid, ranks in rank_ranges.items()
    ]


def _tornado(*, rows, criteria, values):
    """Per-criterion impact on the current leader's own score under a +/-25% weight change."""
    if not rows or not criteria:
        return None
    leader_id = next(
        (option_id for option_id in values if str(option_id) == rows[0]["option_id"]), None
    )
    if leader_id is None:
        return None
    bars = []
    for changed in criteria:
        low_weights, low_total = _perturbed_weights(
            criteria=criteria, changed=changed, factor=Decimal("0.75")
        )
        high_weights, high_total = _perturbed_weights(
            criteria=criteria, changed=changed, factor=Decimal("1.25")
        )
        low_score = _simulate_scores(
            criteria=criteria, values=values, weights=low_weights, total=low_total
        ).get(leader_id)
        high_score = _simulate_scores(
            criteria=criteria, values=values, weights=high_weights, total=high_total
        ).get(leader_id)
        if low_score is None or high_score is None:
            continue
        bars.append(
            {
                "criterion_id": str(changed.id),
                "title": changed.title,
                "score_low": round_number(min(low_score, high_score)),
                "score_high": round_number(max(low_score, high_score)),
                "impact": round_number(abs(high_score - low_score)),
            }
        )
    bars.sort(key=lambda item: item["impact"], reverse=True)
    return {
        "option_id": rows[0]["option_id"],
        "option_title": rows[0]["title"],
        "base_score": rows[0]["weighted_score"],
        "criteria": bars,
    }


def _instant_runoff(*, option_map, ballots):
    """Single-winner ranked-choice tabulation: eliminate the last place, transfer its ballots, repeat.

    Returns (rows, rounds) where rows are ordered from winner (final_rank=1)
    down to first-eliminated (highest final_rank), and rounds records each
    elimination round's tallies for a transparent, replayable audit trail.
    """
    all_ids = list(option_map.keys())
    if not all_ids:
        return [], []
    if len(all_ids) == 1 or not ballots:
        oid = all_ids[0]
        return [
            {
                "option_id": str(oid),
                "title": option_map[oid].title,
                "final_rank": 1,
                "first_round_votes": len(ballots),
                "eliminated_in_round": None,
            }
        ], []

    remaining = set(all_ids)
    elimination_order = []
    rounds = []
    round_number = 0
    first_round_tally = None
    last_tally = {}
    winner_id = None
    while len(remaining) > 1:
        round_number += 1
        tally = {oid: 0 for oid in remaining}
        exhausted = 0
        for ballot in ballots:
            choice = next((oid for oid in ballot if oid in remaining), None)
            if choice is None:
                exhausted += 1
            else:
                tally[choice] += 1
        if first_round_tally is None:
            first_round_tally = dict(tally)
        last_tally = tally
        active_votes = sum(tally.values())
        entry = {
            "round_number": round_number,
            "tallies": {str(k): v for k, v in tally.items()},
            "exhausted_ballots": exhausted,
            "eliminated_option_id": None,
        }
        if active_votes == 0:
            rounds.append(entry)
            break
        leader_votes = max(tally.values())
        if leader_votes * 2 > active_votes:
            winner_id = max(tally, key=lambda oid: tally[oid])
            rounds.append(entry)
            break
        min_votes = min(tally.values())
        tied = [oid for oid, v in tally.items() if v == min_votes]
        eliminated = min(tied, key=lambda oid: option_map[oid].title)
        entry["eliminated_option_id"] = str(eliminated)
        rounds.append(entry)
        remaining.discard(eliminated)
        elimination_order.append(eliminated)

    if winner_id is None and remaining:
        winner_id = next(iter(remaining))

    # Candidates who survived every elimination but weren't the majority winner
    # (the race ended early once someone crossed 50%) still outrank anyone
    # who was actually eliminated, ordered by their last-counted tally.
    runner_ups = sorted(
        (oid for oid in remaining if oid != winner_id),
        key=lambda oid: last_tally.get(oid, 0),
        reverse=True,
    )
    final_order = (
        ([winner_id] if winner_id is not None else [])
        + runner_ups
        + list(reversed(elimination_order))
    )
    rows = []
    for rank, oid in enumerate(final_order, start=1):
        elim_round = next(
            (r["round_number"] for r in rounds if r.get("eliminated_option_id") == str(oid)), None
        )
        rows.append(
            {
                "option_id": str(oid),
                "title": option_map[oid].title,
                "final_rank": rank,
                "first_round_votes": (first_round_tally or {}).get(oid, 0),
                "eliminated_in_round": elim_round,
            }
        )
    return rows, rounds


def _uncertainty_narrative(*, rows, criterion_sensitivity):
    if not rows:
        return ""
    leader = rows[0]
    sensitivity_by_option = {item["option_id"]: item for item in criterion_sensitivity}
    leader_sensitivity = sensitivity_by_option.get(leader["option_id"])
    sentences = []
    if leader_sensitivity and not leader_sensitivity["stable"]:
        sentences.append(
            f"“{leader['title']}” currently ranks first, but a ±25% change to at least one "
            "criterion weight changes which option leads - treat this ranking as directional, "
            "not final."
        )
    else:
        sentences.append(
            f"“{leader['title']}” ranks first and stays first across ±25% changes to any "
            "single criterion weight."
        )
    if leader.get("disagreement") in {"moderate", "high"}:
        sentences.append(
            f"Evaluators showed {leader['disagreement']} disagreement on this option's score. "
            "Review individual rationale before treating the ranking as consensus."
        )
    return " ".join(sentences)


@transaction.atomic
def create_portfolio(*, actor, organisation, owner_id, **fields):
    membership = organisation.memberships.filter(
        user=actor, status=Membership.Status.ACTIVE
    ).first()
    if membership is None or membership.role not in {Membership.Role.OWNER, Membership.Role.ADMIN}:
        raise PermissionDenied("Only organisation managers may create a prioritisation portfolio.")
    item = PrioritisationPortfolio(
        organisation=organisation,
        owner=_active_member(organisation=organisation, user_id=owner_id),
        created_by=actor,
        **fields,
    )
    item.full_clean(validate_unique=False, validate_constraints=False)
    item.save()
    record_event(
        action="prioritisation.portfolio_created",
        object_type="evaluations.PrioritisationPortfolio",
        object_id=str(item.id),
        actor=actor,
        organisation=organisation,
        metadata={"title": item.title},
    )
    return item


@transaction.atomic
def update_portfolio(*, actor, portfolio, fields):
    item = (
        PrioritisationPortfolio.objects.select_for_update()
        .select_related("organisation", "owner")
        .get(id=portfolio.id)
    )
    if not can_manage_portfolio(actor=actor, portfolio=item):
        raise PermissionDenied("You cannot manage this portfolio.")
    if item.status == PrioritisationPortfolio.Status.ARCHIVED:
        raise EvaluationServiceError("Archived portfolios cannot be changed.")
    requested_status = fields.get("status")
    if requested_status is not None and requested_status != item.status:
        allowed = {
            (PrioritisationPortfolio.Status.DRAFT, PrioritisationPortfolio.Status.OPEN),
            (PrioritisationPortfolio.Status.OPEN, PrioritisationPortfolio.Status.CLOSED),
            (PrioritisationPortfolio.Status.CLOSED, PrioritisationPortfolio.Status.ARCHIVED),
        }
        if (item.status, requested_status) not in allowed:
            raise EvaluationServiceError(
                {"status": "Use the governed draft, open, closed, and archived sequence."}
            )
        if requested_status == PrioritisationPortfolio.Status.OPEN:
            if (
                not item.criteria.exists()
                or not item.candidates.filter(status=PortfolioCandidate.Status.ACTIVE).exists()
            ):
                raise EvaluationServiceError(
                    {
                        "status": "Add at least one criterion and one active candidate before opening assessment."
                    }
                )
    editable_after_open = {"owner_id", "status"}
    if item.status != PrioritisationPortfolio.Status.DRAFT and any(
        key not in editable_after_open for key in fields
    ):
        raise EvaluationServiceError(
            "Portfolio governance and constraints can be changed only while draft."
        )
    for key, value in fields.items():
        if key == "owner_id":
            item.owner = _active_member(organisation=item.organisation, user_id=value)
        else:
            setattr(item, key, value)
    item.full_clean(validate_unique=False, validate_constraints=False)
    item.save()
    record_event(
        action="prioritisation.portfolio_updated",
        object_type="evaluations.PrioritisationPortfolio",
        object_id=str(item.id),
        actor=actor,
        organisation=item.organisation,
        metadata={"fields": sorted(fields)},
    )
    return item


@transaction.atomic
def add_portfolio_criterion(*, actor, portfolio, **fields):
    if not can_manage_portfolio(actor=actor, portfolio=portfolio):
        raise PermissionDenied("You cannot manage this portfolio.")
    if portfolio.status != PrioritisationPortfolio.Status.DRAFT:
        raise EvaluationServiceError("Criteria can be added only while the portfolio is draft.")
    item = PortfolioCriterion(organisation=portfolio.organisation, portfolio=portfolio, **fields)
    item.full_clean(validate_unique=False, validate_constraints=False)
    item.save()
    record_event(
        action="prioritisation.criterion_created",
        object_type="evaluations.PortfolioCriterion",
        object_id=str(item.id),
        actor=actor,
        organisation=portfolio.organisation,
        metadata={"portfolio_id": str(portfolio.id), "weight": item.weight},
    )
    return item


@transaction.atomic
def add_candidate(*, actor, portfolio, decision_id, **fields):
    if not can_manage_portfolio(actor=actor, portfolio=portfolio):
        raise PermissionDenied("You cannot manage this portfolio.")
    try:
        decision = portfolio.organisation.decisions.get(id=decision_id)
    except Exception as exc:
        raise EvaluationServiceError(
            {"decision_id": "Select a decision from this organisation."}
        ) from exc
    item = PortfolioCandidate(
        organisation=portfolio.organisation,
        portfolio=portfolio,
        decision=decision,
        added_by=actor,
        **fields,
    )
    item.full_clean(validate_unique=False, validate_constraints=False)
    try:
        item.save()
    except IntegrityError as exc:
        raise EvaluationServiceError(
            {"decision_id": "This decision is already in the portfolio."}
        ) from exc
    record_event(
        action="prioritisation.candidate_added",
        object_type="evaluations.PortfolioCandidate",
        object_id=str(item.id),
        actor=actor,
        organisation=portfolio.organisation,
        metadata={"portfolio_id": str(portfolio.id), "decision_id": str(decision.id)},
    )
    return item


@transaction.atomic
def save_portfolio_assessment(*, actor, candidate, criterion_id, **fields):
    portfolio = candidate.portfolio
    if portfolio.status != PrioritisationPortfolio.Status.OPEN:
        raise EvaluationServiceError("The portfolio is not open for assessment.")
    if not can_assess_portfolio(actor=actor, portfolio=portfolio):
        raise PermissionDenied("Contributors or managers may assess portfolio candidates.")
    try:
        criterion = portfolio.criteria.get(id=criterion_id)
    except PortfolioCriterion.DoesNotExist as exc:
        raise EvaluationServiceError(
            {"criterion_id": "Select a criterion from this portfolio."}
        ) from exc
    item, _ = PortfolioAssessment.objects.update_or_create(
        candidate=candidate,
        criterion=criterion,
        assessor=actor,
        defaults={"organisation": portfolio.organisation, **fields},
    )
    item.full_clean(validate_unique=False, validate_constraints=False)
    item.save()
    record_event(
        action="prioritisation.assessment_saved",
        object_type="evaluations.PortfolioAssessment",
        object_id=str(item.id),
        actor=actor,
        organisation=portfolio.organisation,
        metadata={"candidate_id": str(candidate.id), "criterion_id": str(criterion.id)},
    )
    return item


@transaction.atomic
def set_selection(*, actor, candidate, **fields):
    if not can_manage_portfolio(actor=actor, portfolio=candidate.portfolio):
        raise PermissionDenied("You cannot finalise this portfolio.")
    if candidate.portfolio.status != PrioritisationPortfolio.Status.CLOSED:
        raise EvaluationServiceError(
            "Close collective assessment before recording authority selections."
        )
    item, _ = PortfolioSelection.objects.update_or_create(
        candidate=candidate,
        defaults={
            "organisation": candidate.organisation,
            "selected_by": actor,
            "selected_at": timezone.now(),
            **fields,
        },
    )
    item.full_clean(validate_unique=False, validate_constraints=False)
    item.save()
    record_event(
        action="prioritisation.selection_recorded",
        object_type="evaluations.PortfolioSelection",
        object_id=str(item.id),
        actor=actor,
        organisation=candidate.organisation,
        metadata={"candidate_id": str(candidate.id), "selected": item.selected},
    )
    return item


def portfolio_recommendation(*, portfolio):
    if (
        portfolio.blind_results_until_close
        and portfolio.status == PrioritisationPortfolio.Status.OPEN
    ):
        return {
            "hidden": True,
            "portfolio_id": str(portfolio.id),
            "budget_limit": float(portfolio.budget_limit)
            if portfolio.budget_limit is not None
            else None,
            "capacity_limit": float(portfolio.capacity_limit)
            if portfolio.capacity_limit is not None
            else None,
            "recommended_budget": 0,
            "recommended_capacity": 0,
            "candidates": [],
            "warning": "Assessment results remain sealed until the portfolio closes.",
        }
    criteria = list(portfolio.criteria.all())
    candidates = list(
        portfolio.candidates.filter(status=PortfolioCandidate.Status.ACTIVE)
        .select_related("decision")
        .prefetch_related("assessments")
    )
    total_weight = sum((c.weight for c in criteria), Decimal("0")) or Decimal("1")
    rows = []
    for candidate in candidates:
        weighted = 0.0
        coverage = 0.0
        assessors: set[Any] = set()
        confidence: list[Any] = []
        for criterion in criteria:
            items = [a for a in candidate.assessments.all() if a.criterion_id == criterion.id]
            if items:
                avg = mean(float(a.score) for a in items)
                normalised = avg if criterion.higher_is_better else 100 - avg
                fraction = float(criterion.weight / total_weight)
                weighted += normalised * fraction
                coverage += fraction
                assessors.update(a.assessor_id for a in items)
                confidence.extend(a.confidence for a in items)
        score = weighted / coverage if coverage else 0
        rows.append(
            {
                "candidate_id": str(candidate.id),
                "decision_id": str(candidate.decision_id),
                "title": candidate.decision.title,
                "score": round(score, 2),
                "assessor_count": len(assessors),
                "confidence": round(mean(confidence), 2) if confidence else None,
                "budget_required": float(candidate.budget_required),
                "capacity_required": float(candidate.capacity_required),
                "mandatory": candidate.mandatory,
                "recommended": False,
                "constraint_reason": "",
            }
        )
    rows.sort(key=lambda x: (x["mandatory"], x["score"]), reverse=True)
    budget = float(portfolio.budget_limit) if portfolio.budget_limit is not None else None
    capacity = float(portfolio.capacity_limit) if portfolio.capacity_limit is not None else None
    used_budget = used_capacity = 0.0
    for row in rows:
        fits_budget = budget is None or used_budget + row["budget_required"] <= budget
        fits_capacity = capacity is None or used_capacity + row["capacity_required"] <= capacity
        if row["mandatory"] or (fits_budget and fits_capacity):
            row["recommended"] = True
            used_budget += row["budget_required"]
            used_capacity += row["capacity_required"]
            if row["mandatory"] and not (fits_budget and fits_capacity):
                row["constraint_reason"] = "Mandatory candidate exceeds one or more constraints."
        else:
            reasons = []
            if not fits_budget:
                reasons.append("budget")
            if not fits_capacity:
                reasons.append("capacity")
            row["constraint_reason"] = "Excluded by " + " and ".join(reasons) + " constraint."
    return {
        "hidden": False,
        "portfolio_id": str(portfolio.id),
        "budget_limit": budget,
        "capacity_limit": capacity,
        "recommended_budget": round(used_budget, 2),
        "recommended_capacity": round(used_capacity, 2),
        "candidates": rows,
        "warning": "This is an explainable greedy recommendation, not an automatic organisational decision.",
    }


@transaction.atomic
def create_forecast_question(*, actor, exercise, question_text, resolution_criteria=""):
    exercise = (
        EvaluationExercise.objects.select_for_update()
        .select_related("decision", "organisation", "owner")
        .get(id=exercise.id)
    )
    if not can_manage_exercise(actor=actor, exercise=exercise):
        raise PermissionDenied("You cannot manage this evaluation.")
    if exercise.method != EvaluationExercise.Method.FORECASTING:
        raise EvaluationServiceError(
            "Only a calibrated-forecasting exercise accepts forecast questions."
        )
    if exercise.status in {EvaluationExercise.Status.CLOSED, EvaluationExercise.Status.ARCHIVED}:
        raise EvaluationServiceError("Add forecast questions before the exercise closes.")
    question = ForecastQuestion(
        organisation=exercise.organisation,
        exercise=exercise,
        question_text=question_text,
        resolution_criteria=resolution_criteria,
    )
    question.full_clean(validate_unique=False, validate_constraints=False)
    question.save()
    record_event(
        action="evaluation.forecast_question_created",
        object_type="evaluations.ForecastQuestion",
        object_id=str(question.id),
        actor=actor,
        organisation=exercise.organisation,
        metadata={"exercise_id": str(exercise.id)},
    )
    return question


@transaction.atomic
def submit_forecast(*, actor, question, probability):
    question = (
        ForecastQuestion.objects.select_for_update()
        .select_related("exercise__decision", "exercise__organisation", "exercise__owner")
        .get(id=question.id)
    )
    exercise = question.exercise
    if not can_submit_evaluation(actor=actor, exercise=exercise):
        raise PermissionDenied("Only active, non-observer decision participants may forecast.")
    if question.status != ForecastQuestion.Status.OPEN:
        raise EvaluationServiceError("This question has already resolved.")
    if exercise.status != EvaluationExercise.Status.OPEN:
        raise EvaluationServiceError("This forecasting exercise is not open.")
    forecast, _ = Forecast.objects.update_or_create(
        question=question,
        forecaster=actor,
        defaults={"organisation": question.organisation, "probability": probability},
    )
    forecast.full_clean(validate_unique=False, validate_constraints=False)
    forecast.save()
    record_event(
        action="evaluation.forecast_submitted",
        object_type="evaluations.Forecast",
        object_id=str(forecast.id),
        actor=actor,
        organisation=question.organisation,
        metadata={"question_id": str(question.id), "probability": forecast.probability},
    )
    return forecast


@transaction.atomic
def resolve_forecast_question(*, actor, question, outcome):
    question = (
        ForecastQuestion.objects.select_for_update()
        .select_related("exercise__decision", "exercise__organisation", "exercise__owner")
        .get(id=question.id)
    )
    exercise = question.exercise
    if not can_manage_exercise(actor=actor, exercise=exercise):
        raise PermissionDenied("You cannot resolve this forecasting question.")
    if question.status != ForecastQuestion.Status.OPEN:
        raise EvaluationServiceError("This question has already resolved.")
    question.status = ForecastQuestion.Status.RESOLVED
    question.outcome = outcome
    question.resolved_at = timezone.now()
    question.resolved_by = actor
    question.full_clean(validate_unique=False, validate_constraints=False)
    question.save()
    target = Decimal("1") if outcome else Decimal("0")
    forecasts = list(question.forecasts.all())
    for forecast in forecasts:
        brier = (forecast.probability / Decimal("100") - target) ** 2
        forecast.brier_score = brier.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        forecast.save(update_fields=["brier_score", "updated_at"])
    record_event(
        action="evaluation.forecast_question_resolved",
        object_type="evaluations.ForecastQuestion",
        object_id=str(question.id),
        actor=actor,
        organisation=question.organisation,
        metadata={
            "exercise_id": str(exercise.id),
            "outcome": outcome,
            "forecast_count": len(forecasts),
        },
    )
    return question


def forecasting_leaderboard(*, organisation):
    """Mean Brier score per forecaster across every resolved question in this organisation.

    Lower is better - this ranks calibration across every question someone
    has ever forecast, not just whether they happened to guess right once.
    """
    aggregates = list(
        Forecast.objects.filter(organisation=organisation, brier_score__isnull=False)
        .values("forecaster_id")
        .annotate(mean_brier_score=Avg("brier_score"), question_count=Count("question", distinct=True))
        .order_by("mean_brier_score", "forecaster_id")
    )
    forecasters = {
        user.id: user
        for user in User.objects.filter(id__in=[row["forecaster_id"] for row in aggregates])
    }
    rows = []
    for index, row in enumerate(aggregates):
        forecaster = forecasters[row["forecaster_id"]]
        rows.append(
            {
                "forecaster_id": str(forecaster.id),
                "email": forecaster.email,
                "first_name": forecaster.first_name,
                "last_name": forecaster.last_name,
                "mean_brier_score": round_number(float(row["mean_brier_score"])),
                "resolved_question_count": row["question_count"],
                "rank": index + 1,
            }
        )
    return rows


def _creates_delegation_cycle(*, exercise, voter_id, delegate_to_id):
    """Would voter_id delegating to delegate_to_id eventually loop back to voter_id?

    Walks the existing chain starting at delegate_to_id (voter_id's own vote
    isn't written yet, so it can't appear on its own path). Anything else -
    an unrelated existing cycle, a dead end, or a chain longer than the cap -
    isn't this voter's problem to reject; the tally resolves it as an
    abstention for whoever it actually affects.
    """
    current_id = delegate_to_id
    seen = set()
    for _ in range(MAX_DELEGATION_CHAIN_DEPTH + 1):
        if current_id == voter_id:
            return True
        if current_id in seen:
            return False
        seen.add(current_id)
        try:
            next_vote = LiquidVote.objects.get(exercise=exercise, voter_id=current_id)
        except LiquidVote.DoesNotExist:
            return False
        if next_vote.delegate_to_id is None:
            return False
        current_id = next_vote.delegate_to_id
    return False


@transaction.atomic
def cast_liquid_vote(*, actor, exercise, option_id=None, delegate_to_id=None):
    exercise = (
        EvaluationExercise.objects.select_for_update()
        .select_related("decision", "organisation", "owner")
        .get(id=exercise.id)
    )
    if exercise.method != EvaluationExercise.Method.LIQUID_DEMOCRACY:
        raise EvaluationServiceError(
            "Only a liquid-democracy exercise accepts direct votes or delegations."
        )
    if exercise.status != EvaluationExercise.Status.OPEN:
        raise EvaluationServiceError("This liquid-democracy exercise is not open.")
    if not can_submit_evaluation(actor=actor, exercise=exercise):
        raise PermissionDenied("Only active, non-observer decision participants may vote.")
    if bool(option_id) == bool(delegate_to_id):
        raise EvaluationServiceError(
            "Choose exactly one of an active option to vote for, or a participant to delegate to."
        )
    option = None
    delegate_to = None
    if option_id:
        try:
            option = exercise.decision.options.get(
                id=option_id, status=DecisionOption.Status.ACTIVE
            )
        except DecisionOption.DoesNotExist as exc:
            raise EvaluationServiceError(
                {"option_id": "Select an active option from this decision."}
            ) from exc
    else:
        if str(delegate_to_id) == str(actor.id):
            raise EvaluationServiceError({"delegate_to_id": "You cannot delegate to yourself."})
        try:
            delegate_to = User.objects.get(id=delegate_to_id)
        except User.DoesNotExist as exc:
            raise EvaluationServiceError(
                {"delegate_to_id": "Select someone to delegate to."}
            ) from exc
        if not can_submit_evaluation(actor=delegate_to, exercise=exercise):
            raise EvaluationServiceError(
                {
                    "delegate_to_id": "You can only delegate to another eligible participant in this decision."
                }
            )
        if _creates_delegation_cycle(
            exercise=exercise, voter_id=actor.id, delegate_to_id=delegate_to.id
        ):
            raise EvaluationServiceError(
                {"delegate_to_id": "This delegation would create a cycle - choose someone else."}
            )
    vote, _ = LiquidVote.objects.update_or_create(
        exercise=exercise,
        voter=actor,
        defaults={"organisation": exercise.organisation, "option": option, "delegate_to": delegate_to},
    )
    vote.full_clean(validate_unique=False, validate_constraints=False)
    vote.save()
    record_event(
        action="evaluation.liquid_vote_cast",
        object_type="evaluations.LiquidVote",
        object_id=str(vote.id),
        actor=actor,
        organisation=exercise.organisation,
        metadata={
            "exercise_id": str(exercise.id),
            "option_id": str(option.id) if option else None,
            "delegate_to_id": str(delegate_to.id) if delegate_to else None,
        },
    )
    return vote


def _resolve_direct_voter(*, votes, start_voter_id):
    """Walk delegate_to pointers from start_voter_id to whoever casts a direct vote.

    Each voter's own distance to resolution is capped independently, so a
    voter one hop from a direct vote still resolves even if some other,
    far-upstream delegator's much longer chain would exceed the cap. A cycle
    or a chain longer than MAX_DELEGATION_CHAIN_DEPTH resolves to None
    (abstain) rather than looping or raising - the mechanism's own rule, not
    just a defensive fallback.
    """
    current_id = start_voter_id
    visited: set = set()
    hops = 0
    while True:
        vote = votes.get(current_id)
        if vote is None:
            return None
        if vote.option_id is not None:
            return current_id
        if current_id in visited:
            return None
        visited.add(current_id)
        if hops >= MAX_DELEGATION_CHAIN_DEPTH:
            return None
        current_id = vote.delegate_to_id
        hops += 1


def liquid_democracy_tally(*, exercise):
    """Resolve every standing vote/delegation to whoever ultimately casts a direct vote."""
    votes = {
        item.voter_id: item
        for item in LiquidVote.objects.filter(exercise=exercise).select_related(
            "voter", "option", "delegate_to"
        )
    }
    option_tally: dict[Any, dict[str, Any]] = {}
    delegated_count_by_direct_voter: Counter = Counter()
    abstained_count = 0
    for voter_id in votes:
        direct_voter_id = _resolve_direct_voter(votes=votes, start_voter_id=voter_id)
        if direct_voter_id is None:
            abstained_count += 1
            continue
        direct_vote = votes[direct_voter_id]
        bucket = option_tally.setdefault(
            direct_vote.option_id, {"option": direct_vote.option, "direct": 0, "delegated": 0}
        )
        if voter_id == direct_voter_id:
            bucket["direct"] += 1
        else:
            bucket["delegated"] += 1
            delegated_count_by_direct_voter[direct_voter_id] += 1

    option_rows = sorted(
        (
            {
                "option_id": str(option_id),
                "title": bucket["option"].title,
                "direct_vote_count": bucket["direct"],
                "delegated_vote_count": bucket["delegated"],
                "total_vote_count": bucket["direct"] + bucket["delegated"],
            }
            for option_id, bucket in option_tally.items()
        ),
        key=lambda row: row["total_vote_count"],
        reverse=True,
    )
    direct_voter_rows = sorted(
        (
            {
                "voter_id": str(vote.voter_id),
                "email": vote.voter.email,
                "option_id": str(vote.option_id),
                "option_title": vote.option.title,
                "delegated_vote_count": delegated_count_by_direct_voter.get(vote.voter_id, 0),
            }
            for vote in votes.values()
            if vote.option_id is not None
        ),
        key=lambda row: row["delegated_vote_count"],
        reverse=True,
    )
    return {
        "exercise_id": str(exercise.id),
        "options": option_rows,
        "direct_voters": direct_voter_rows,
        "abstained_count": abstained_count,
        "total_vote_count": len(votes),
    }


@transaction.atomic
def create_opinion_statement(*, actor, exercise, text):
    exercise = (
        EvaluationExercise.objects.select_for_update()
        .select_related("decision", "organisation", "owner")
        .get(id=exercise.id)
    )
    if exercise.method != EvaluationExercise.Method.OPINION_CLUSTERING:
        raise EvaluationServiceError(
            "Only an opinion-clustering exercise accepts statements."
        )
    if exercise.status != EvaluationExercise.Status.OPEN:
        raise EvaluationServiceError("This opinion-clustering exercise is not open.")
    if not can_submit_evaluation(actor=actor, exercise=exercise):
        raise PermissionDenied("Only active, non-observer decision participants may add statements.")
    statement = OpinionStatement(
        organisation=exercise.organisation, exercise=exercise, author=actor, text=text
    )
    statement.full_clean(validate_unique=False, validate_constraints=False)
    statement.save()
    record_event(
        action="evaluation.opinion_statement_created",
        object_type="evaluations.OpinionStatement",
        object_id=str(statement.id),
        actor=actor,
        organisation=exercise.organisation,
        metadata={"exercise_id": str(exercise.id)},
    )
    return statement


@transaction.atomic
def cast_opinion_vote(*, actor, statement, choice):
    statement = (
        OpinionStatement.objects.select_for_update()
        .select_related("exercise__decision", "exercise__organisation", "exercise__owner")
        .get(id=statement.id)
    )
    exercise = statement.exercise
    if not can_submit_evaluation(actor=actor, exercise=exercise):
        raise PermissionDenied("Only active, non-observer decision participants may vote.")
    if exercise.status != EvaluationExercise.Status.OPEN:
        raise EvaluationServiceError("This opinion-clustering exercise is not open.")
    vote, _ = OpinionVote.objects.update_or_create(
        statement=statement,
        voter=actor,
        defaults={"organisation": statement.organisation, "choice": choice},
    )
    vote.full_clean(validate_unique=False, validate_constraints=False)
    vote.save()
    record_event(
        action="evaluation.opinion_vote_cast",
        object_type="evaluations.OpinionVote",
        object_id=str(vote.id),
        actor=actor,
        organisation=statement.organisation,
        metadata={"statement_id": str(statement.id), "choice": choice},
    )
    return vote


def _select_pivot_statement(statements):
    """The most-voted statement that has at least one agreeing and one disagreeing
    voter - the natural axis to split the group on. Ties break on creation order.
    """
    candidates = sorted(statements, key=lambda s: len(s.votes.all()), reverse=True)
    for statement in candidates:
        agree_voters = {
            v.voter_id for v in statement.votes.all() if v.choice == OpinionVote.Choice.AGREE
        }
        disagree_voters = {
            v.voter_id for v in statement.votes.all() if v.choice == OpinionVote.Choice.DISAGREE
        }
        if agree_voters and disagree_voters:
            return statement, agree_voters, disagree_voters
    return None, set(), set()


def _cluster_agree_rate(*, votes, cluster_voter_ids):
    in_cluster = [v for v in votes if v.voter_id in cluster_voter_ids]
    if not in_cluster:
        return None
    agree = sum(1 for v in in_cluster if v.choice == OpinionVote.Choice.AGREE)
    return agree / len(in_cluster)


def _classify_statement(*, cluster_a_rate, cluster_b_rate):
    if cluster_a_rate is None or cluster_b_rate is None:
        return "no_data"
    high, low = OPINION_CLUSTER_CONSENSUS_THRESHOLD, 1 - OPINION_CLUSTER_CONSENSUS_THRESHOLD
    both_agree = cluster_a_rate >= high and cluster_b_rate >= high
    both_disagree = cluster_a_rate <= low and cluster_b_rate <= low
    if both_agree or both_disagree:
        return "bridging"
    opposite_stances = (cluster_a_rate >= high and cluster_b_rate <= low) or (
        cluster_b_rate >= high and cluster_a_rate <= low
    )
    if opposite_stances:
        return "divisive"
    return "mixed"


def opinion_clustering_analysis(*, exercise):
    """On-demand clustering of participants into two opinion groups from their votes.

    A simple two-group split, not a PCA/k-means pipeline: the most-voted
    statement with both agreeing and disagreeing voters becomes the pivot,
    and everyone who voted on it is clustered by which side they took.
    Everyone else - anyone who never voted on the pivot - isn't clustered.
    Statements then get classified by whether the two clusters agree
    ("bridging"), split ("divisive"), or neither ("mixed").
    """
    statements = list(
        exercise.opinion_statements.select_related("author").prefetch_related("votes__voter")
    )
    base = {
        "exercise_id": str(exercise.id),
        "insufficient_data": True,
        "pivot_statement_id": None,
        "cluster_a_size": 0,
        "cluster_b_size": 0,
        "statements": [],
        "bridging_statement_ids": [],
        "divisive_statement_ids": [],
        "warning": (
            "Clusters are anchored on the most-voted statement with both agreeing and "
            "disagreeing votes; participants who didn't vote on it aren't clustered."
        ),
    }
    if not statements:
        return base
    pivot, cluster_a_ids, cluster_b_ids = _select_pivot_statement(statements)
    if pivot is None:
        return base

    rows = []
    bridging_ids = []
    divisive_ids = []
    for statement in statements:
        votes = list(statement.votes.all())
        cluster_a_rate = _cluster_agree_rate(votes=votes, cluster_voter_ids=cluster_a_ids)
        cluster_b_rate = _cluster_agree_rate(votes=votes, cluster_voter_ids=cluster_b_ids)
        classification = _classify_statement(
            cluster_a_rate=cluster_a_rate, cluster_b_rate=cluster_b_rate
        )
        if classification == "bridging":
            bridging_ids.append(str(statement.id))
        elif classification == "divisive":
            divisive_ids.append(str(statement.id))
        rows.append(
            {
                "statement_id": str(statement.id),
                "text": statement.text,
                "author_email": statement.author.email,
                "cluster_a_vote_count": sum(1 for v in votes if v.voter_id in cluster_a_ids),
                "cluster_a_agree_rate": round_number(cluster_a_rate),
                "cluster_b_vote_count": sum(1 for v in votes if v.voter_id in cluster_b_ids),
                "cluster_b_agree_rate": round_number(cluster_b_rate),
                "classification": classification,
            }
        )
    return {
        **base,
        "insufficient_data": False,
        "pivot_statement_id": str(pivot.id),
        "cluster_a_size": len(cluster_a_ids),
        "cluster_b_size": len(cluster_b_ids),
        "statements": rows,
        "bridging_statement_ids": bridging_ids,
        "divisive_statement_ids": divisive_ids,
    }
