"""Explainable, read-only synthesis of existing decision records."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean

from django.utils import timezone

from apps.assumptions.models import Assumption
from apps.decision_options.models import DecisionOption
from apps.evaluations.models import EvaluationRound, MinorityReport
from apps.evaluations.services import evaluation_results
from apps.evidence.models import Evidence
from apps.foresight.models import SignalDecisionLink, Source, StrategicImplication, WindTunnelAssessment
from apps.participants.models import Participant
from apps.positions.models import Position
from apps.risks.models import Risk

from .models import DecisionIssue, DecisionQualityReview, ExecutiveDecisionSummary
from .policies import can_contribute_analysis, can_manage_analysis


def _latest_positions(decision):
    latest = {}
    for position in Position.objects.filter(
        decision=decision, participant__status=Participant.Status.ACTIVE
    ).select_related("participant", "preferred_option").order_by("participant_id", "-version"):
        latest.setdefault(position.participant_id, position)
    return list(latest.values())


def decision_analysis_workspace(*, decision, viewer) -> dict:
    options = list(DecisionOption.objects.filter(decision=decision, status=DecisionOption.Status.ACTIVE).order_by("title"))
    evidence = list(Evidence.objects.filter(decision=decision, status=Evidence.Status.ACTIVE).select_related("source"))
    assumptions = list(Assumption.objects.filter(decision=decision, status=Assumption.Status.ACTIVE))
    risks = list(Risk.objects.filter(decision=decision).exclude(status=Risk.Status.CLOSED))
    issues = list(DecisionIssue.objects.filter(decision=decision).select_related("owner", "option"))
    positions = _latest_positions(decision)
    today = timezone.localdate()

    evidence_by_option = defaultdict(list)
    assumptions_by_option = defaultdict(list)
    risks_by_option = defaultdict(list)
    positions_by_option = defaultdict(list)
    issues_by_option = defaultdict(list)
    for item in evidence:
        evidence_by_option[item.option_id].append(item)
    for item in assumptions:
        assumptions_by_option[item.option_id].append(item)
    for item in risks:
        risks_by_option[item.option_id].append(item)
    for item in positions:
        positions_by_option[item.preferred_option_id].append(item)
    for item in issues:
        issues_by_option[item.option_id].append(item)

    wind = defaultdict(list)
    assessments = WindTunnelAssessment.objects.filter(
        option__decision=decision,
        scenario__scenario_set__linked_decision=decision,
    ).select_related("scenario", "scenario__scenario_set", "option")
    for item in assessments:
        wind[item.option_id].append(item)

    closed_rounds = EvaluationRound.objects.filter(
        exercise__decision=decision,
        status=EvaluationRound.Status.CLOSED,
    ).select_related("exercise").order_by("exercise_id", "-number")
    latest_round_by_exercise = {}
    for round_item in closed_rounds:
        latest_round_by_exercise.setdefault(round_item.exercise_id, round_item)
    evaluation_by_option = defaultdict(list)
    for round_item in latest_round_by_exercise.values():
        results = evaluation_results(round=round_item, viewer=viewer)
        if results.get("hidden"):
            continue
        for result in results.get("options", []):
            evaluation_by_option[result["option_id"]].append(
                {
                    "exercise_id": str(round_item.exercise_id),
                    "exercise_title": round_item.exercise.title,
                    "method": round_item.exercise.method,
                    "weighted_score": result.get("weighted_score"),
                    "approval_rate": result.get("approval_rate"),
                    "objection_rate": result.get("objection_rate"),
                    "passes_threshold": result.get("passes_threshold"),
                    "confidence": result.get("confidence"),
                }
            )

    option_rows = []
    for option in options:
        option_evidence = evidence_by_option[option.id]
        option_assumptions = assumptions_by_option[option.id]
        option_risks = risks_by_option[option.id]
        option_positions = positions_by_option[option.id]
        option_wind = wind[option.id]
        option_issues = issues_by_option[option.id]
        scores = [item.robustness_score for item in option_wind]
        option_rows.append(
            {
                "id": str(option.id),
                "title": option.title,
                "description": option.description,
                "expected_benefits": option.expected_benefits,
                "tradeoffs": option.tradeoffs,
                "is_status_quo": option.is_status_quo,
                "evidence": {
                    "supporting": sum(item.stance == Evidence.Stance.SUPPORTS for item in option_evidence),
                    "challenging": sum(item.stance == Evidence.Stance.CHALLENGES for item in option_evidence),
                    "mixed": sum(item.stance == Evidence.Stance.MIXED for item in option_evidence),
                    "context": sum(item.stance == Evidence.Stance.CONTEXT for item in option_evidence),
                    "high_strength": sum(item.strength == Evidence.Strength.HIGH for item in option_evidence),
                    "structured_sources": sum(item.source_id is not None for item in option_evidence),
                    "high_credibility_sources": sum(
                        item.source_id is not None and item.source.credibility == Source.Credibility.HIGH
                        for item in option_evidence
                    ),
                    "unassessed_sources": sum(
                        item.source_id is not None and item.source.credibility == Source.Credibility.UNASSESSED
                        for item in option_evidence
                    ),
                    "superseded_sources": sum(
                        item.source_id is not None and item.source.status == Source.Status.SUPERSEDED
                        for item in option_evidence
                    ),
                    "withdrawn_sources": sum(
                        item.source_id is not None and item.source.status == Source.Status.WITHDRAWN
                        for item in option_evidence
                    ),
                    "dated_sources": sum(
                        item.source_id is not None and item.source.published_on is not None
                        for item in option_evidence
                    ),
                },
                "assumptions": {
                    "total": len(option_assumptions),
                    "unverified": sum(item.verification_status == Assumption.VerificationStatus.UNVERIFIED for item in option_assumptions),
                    "invalidated": sum(item.verification_status == Assumption.VerificationStatus.INVALIDATED for item in option_assumptions),
                    "low_confidence": sum(item.confidence == Assumption.Confidence.LOW for item in option_assumptions),
                    "overdue_review": sum(
                        item.review_date is not None and item.review_date < today
                        for item in option_assumptions
                    ),
                },
                "risks": {
                    "total": len(option_risks),
                    "exposure": sum(item.score for item in option_risks),
                    "highest_score": max((item.score for item in option_risks), default=0),
                    "without_mitigation": sum(not item.mitigation_plan for item in option_risks),
                    "overdue_review": sum(
                        item.review_date is not None and item.review_date < today
                        for item in option_risks
                    ),
                },
                "stakeholders": {
                    "support": sum(item.recommendation in {Position.Recommendation.SUPPORT, Position.Recommendation.SUPPORT_WITH_CONDITIONS} for item in option_positions),
                    "conditional": sum(item.recommendation == Position.Recommendation.SUPPORT_WITH_CONDITIONS for item in option_positions),
                    "high_confidence": sum(item.confidence == Position.Confidence.HIGH for item in option_positions),
                },
                "scenarios": {
                    "assessment_count": len(option_wind),
                    "average_robustness": round(mean(scores), 2) if scores else None,
                    "minimum_robustness": round(min(scores), 2) if scores else None,
                    "vulnerability_count": sum(bool(item.vulnerabilities.strip()) for item in option_wind),
                    "mitigation_count": sum(bool(item.mitigations.strip()) for item in option_wind),
                },
                "evaluations": evaluation_by_option[str(option.id)],
                "issues": {
                    "open": sum(item.status in {DecisionIssue.Status.OPEN, DecisionIssue.Status.IN_PROGRESS} for item in option_issues),
                    "critical": sum(item.severity == DecisionIssue.Severity.CRITICAL and item.status in {DecisionIssue.Status.OPEN, DecisionIssue.Status.IN_PROGRESS} for item in option_issues),
                },
            }
        )

    general_evidence = evidence_by_option[None]
    general_assumptions = assumptions_by_option[None]
    general_risks = risks_by_option[None]
    general_issues = issues_by_option[None]
    signals = SignalDecisionLink.objects.filter(decision=decision).select_related("signal")
    implications = StrategicImplication.objects.filter(linked_decision=decision).select_related("canvas", "owner")
    minority_reports = MinorityReport.objects.filter(exercise__decision=decision, status=MinorityReport.Status.PUBLISHED).select_related("exercise", "author")
    can_manage = can_manage_analysis(actor=viewer, decision=decision)
    review_queryset = DecisionQualityReview.objects.filter(decision=decision).exclude(
        status=DecisionQualityReview.Status.SUPERSEDED
    )
    summary_queryset = ExecutiveDecisionSummary.objects.filter(decision=decision).exclude(
        status=ExecutiveDecisionSummary.Status.SUPERSEDED
    )
    if not can_manage:
        review_queryset = review_queryset.exclude(status=DecisionQualityReview.Status.DRAFT)
        summary_queryset = summary_queryset.exclude(status=ExecutiveDecisionSummary.Status.DRAFT)
    latest_review = review_queryset.first()
    latest_summary = summary_queryset.first()

    return {
        "decision": {
            "id": str(decision.id),
            "title": decision.title,
            "question": decision.decision_question,
            "status": decision.status,
            "status_label": decision.get_status_display(),
        },
        "options": option_rows,
        "cross_cutting": {
            "evidence": len(general_evidence),
            "assumptions": len(general_assumptions),
            "risks": len(general_risks),
            "open_issues": sum(item.status in {DecisionIssue.Status.OPEN, DecisionIssue.Status.IN_PROGRESS} for item in general_issues),
            "do_not_support_any": sum(item.recommendation == Position.Recommendation.DO_NOT_SUPPORT_ANY for item in positions),
            "abstentions": sum(item.recommendation == Position.Recommendation.ABSTAIN for item in positions),
        },
        "foresight": {
            "linked_signals": [
                {
                    "id": str(link.signal_id),
                    "title": link.signal.title,
                    "relevance": link.relevance,
                    "priority_score": link.signal.priority_score,
                    "time_horizon": link.signal.time_horizon,
                }
                for link in signals
            ],
            "implications": [
                {
                    "id": str(item.id),
                    "canvas_id": str(item.canvas_id),
                    "canvas_title": item.canvas.title,
                    "title": item.title,
                    "type": item.implication_type,
                    "priority": item.priority,
                    "status": item.status,
                }
                for item in implications
            ],
        },
        "quality_review": None if latest_review is None else {
            "id": str(latest_review.id), "version": latest_review.version, "status": latest_review.status,
            "judgement": latest_review.judgement, "blockers": latest_review.blockers,
            "conditions": latest_review.conditions, "published_at": latest_review.published_at,
        },
        "executive_summary": None if latest_summary is None else {
            "id": str(latest_summary.id), "version": latest_summary.version, "status": latest_summary.status,
            "proposed_judgement": latest_summary.proposed_judgement,
            "approved_at": latest_summary.approved_at,
        },
        "minority_reports": [
            {
                "id": str(item.id),
                "exercise_id": str(item.exercise_id),
                "exercise_title": item.exercise.title,
                "title": item.title,
                "analysis": item.analysis,
                "recommendation": item.recommendation,
                "published_at": item.published_at,
            }
            for item in minority_reports
        ],
        "issue_summary": {
            "total": len(issues),
            "open": sum(item.status in {DecisionIssue.Status.OPEN, DecisionIssue.Status.IN_PROGRESS} for item in issues),
            "critical": sum(item.severity == DecisionIssue.Severity.CRITICAL and item.status in {DecisionIssue.Status.OPEN, DecisionIssue.Status.IN_PROGRESS} for item in issues),
        },
        "capabilities": {
            "can_manage": can_manage,
            "can_contribute": can_contribute_analysis(actor=viewer, decision=decision),
        },
        "principle": "This workspace organises traceable human judgement. It does not select an option or advance the decision lifecycle.",
    }
