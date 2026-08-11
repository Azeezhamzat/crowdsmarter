"""Transparent zero-cost decision review provider."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date, datetime
from typing import Any

from .base import AIReviewOutput, AnalyticsNarrative, AnalyticsObservation, ReviewFinding, SimilarDecision


_TOKEN_PATTERN = re.compile(r"[a-z0-9]{3,}")
_DUPLICATE_EVIDENCE_THRESHOLD = 0.6


def _as_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        parsed = datetime.fromisoformat(value)
        return parsed.date()
    return None


def _tokens(value: str) -> set[str]:
    return set(_TOKEN_PATTERN.findall(value.lower()))


def _similarity(left: str, right: str) -> float:
    left_tokens = _tokens(left)
    right_tokens = _tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


class RuleBasedAIProvider:
    """Deterministic review rules that require no paid model or external service."""

    key = "rules"
    label = "Transparent rules review"
    model_identifier = "crowdsmarter-rules-v1"

    def review_decision(self, *, snapshot: dict[str, Any]) -> AIReviewOutput:
        options = snapshot["options"]
        evidence = snapshot["evidence"]
        assumptions = snapshot["assumptions"]
        risks = snapshot["risks"]
        participants = snapshot["participants"]

        missing_evidence: list[ReviewFinding] = []
        if not evidence:
            missing_evidence.append(
                ReviewFinding(
                    severity="high",
                    title="No active evidence is recorded",
                    detail=(
                        "Human reviewers should add attributable evidence before "
                        "relying on the decision record."
                    ),
                )
            )
        evidence_by_option: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in evidence:
            if item["option_id"]:
                evidence_by_option[item["option_id"]].append(item)
        for option in options:
            if not evidence_by_option.get(option["id"]):
                missing_evidence.append(
                    ReviewFinding(
                        severity="medium",
                        title=f"Option lacks specific evidence: {option['title']}",
                        detail=(
                            "No active evidence item is linked directly to this option. "
                            "General evidence may not expose option-specific uncertainty."
                        ),
                        related_type="decision_option",
                        related_id=option["id"],
                    )
                )
        if evidence and not any(
            item["stance"] in {"challenges", "mixed"} for item in evidence
        ):
            missing_evidence.append(
                ReviewFinding(
                    severity="medium",
                    title="No challenging evidence is recorded",
                    detail=(
                        "The evidence set contains no item that challenges or qualifies "
                        "the proposed options. Reviewers should consider disconfirming "
                        "evidence."
                    ),
                )
            )

        unsupported_assumptions: list[ReviewFinding] = []
        for assumption in assumptions:
            if assumption["verification_status"] == "invalidated":
                unsupported_assumptions.append(
                    ReviewFinding(
                        severity="high",
                        title="An active assumption has been invalidated",
                        detail=assumption["statement"],
                        related_type="assumption",
                        related_id=assumption["id"],
                    )
                )
            elif assumption["verification_status"] == "unverified":
                severity = "high" if assumption["confidence"] == "high" else "medium"
                unsupported_assumptions.append(
                    ReviewFinding(
                        severity=severity,
                        title="Unverified assumption",
                        detail=(
                            f"{assumption['statement']} Impact if false: "
                            f"{assumption['impact_if_false']}"
                        ),
                        related_type="assumption",
                        related_id=assumption["id"],
                    )
                )
        if not assumptions:
            unsupported_assumptions.append(
                ReviewFinding(
                    severity="medium",
                    title="No assumptions are recorded",
                    detail=(
                        "Important decisions usually depend on beliefs about conditions, "
                        "behaviour, timing, or capacity. Reviewers should confirm that "
                        "assumptions have been made explicit."
                    ),
                )
            )

        contradictory_evidence: list[ReviewFinding] = []
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in evidence:
            grouped[item["option_id"] or "decision"].append(item)
        option_names = {item["id"]: item["title"] for item in options}
        for related_id, items in grouped.items():
            supports = [item for item in items if item["stance"] == "supports"]
            challenges = [item for item in items if item["stance"] == "challenges"]
            if supports and challenges:
                high_strength = any(
                    item["strength"] == "high" for item in supports
                ) and any(item["strength"] == "high" for item in challenges)
                target = option_names.get(related_id, "the overall decision")
                contradictory_evidence.append(
                    ReviewFinding(
                        severity="high" if high_strength else "medium",
                        title=f"Evidence points in opposing directions for {target}",
                        detail=(
                            f"{len(supports)} item(s) support and {len(challenges)} "
                            "item(s) challenge this target. Human reviewers should "
                            "reconcile the difference rather than average it away."
                        ),
                        related_type=(
                            "decision_option"
                            if related_id != "decision"
                            else "decision"
                        ),
                        related_id="" if related_id == "decision" else related_id,
                    )
                )

        duplicate_evidence: list[ReviewFinding] = []
        seen_pairs: set[frozenset[str]] = set()
        for left_index, left in enumerate(evidence):
            left_text = f"{left['title']} {left['summary']}"
            for right in evidence[left_index + 1 :]:
                pair_key = frozenset({left["id"], right["id"]})
                if pair_key in seen_pairs:
                    continue
                right_text = f"{right['title']} {right['summary']}"
                score = _similarity(left_text, right_text)
                if score >= _DUPLICATE_EVIDENCE_THRESHOLD:
                    seen_pairs.add(pair_key)
                    duplicate_evidence.append(
                        ReviewFinding(
                            severity="low",
                            title=f"Possible duplicate evidence: {left['title']!r} and {right['title']!r}",
                            detail=(
                                f"These two evidence items overlap by "
                                f"{round(score * 100)}% of their distinct terms. "
                                "Confirm they record genuinely separate evidence "
                                "rather than the same item entered twice."
                            ),
                            related_type="evidence",
                            related_id=left["id"],
                        )
                    )

        active_roles = {item["role"] for item in participants}
        missing_stakeholders: list[ReviewFinding] = []
        if "decision_maker" not in active_roles:
            missing_stakeholders.append(
                ReviewFinding(
                    severity="high",
                    title="No designated decision maker",
                    detail=(
                        "The decision owner is accountable for the workflow, but no "
                        "separate decision-maker role is recorded."
                    ),
                )
            )
        if "reviewer" not in active_roles:
            missing_stakeholders.append(
                ReviewFinding(
                    severity="medium",
                    title="No reviewer is represented",
                    detail=(
                        "A reviewer can challenge framing, evidence quality, and "
                        "unresolved trade-offs before finalisation."
                    ),
                )
            )
        if "contributor" not in active_roles:
            missing_stakeholders.append(
                ReviewFinding(
                    severity="medium",
                    title="No contributor is represented",
                    detail=(
                        "The record may be missing operational or domain knowledge from "
                        "people affected by implementation."
                    ),
                )
            )
        if len(participants) <= 1:
            missing_stakeholders.append(
                ReviewFinding(
                    severity="high",
                    title="The decision currently has only one participant",
                    detail=(
                        "Important organisational decisions benefit from explicit "
                        "participation beyond the decision owner."
                    ),
                )
            )

        risk_highlights: list[ReviewFinding] = []
        for risk in risks:
            score = risk["likelihood"] * risk["impact"]
            if score >= 15 and risk["status"] not in {"mitigated", "closed"}:
                risk_highlights.append(
                    ReviewFinding(
                        severity="high",
                        title=f"High exposure risk: {risk['title']}",
                        detail=(
                            f"Likelihood {risk['likelihood']}/5 × impact "
                            f"{risk['impact']}/5 = {score}. Current response: "
                            f"{risk['response_strategy']}."
                        ),
                        related_type="risk",
                        related_id=risk["id"],
                    )
                )
            elif score >= 9 and risk["status"] in {"open", "monitoring"}:
                risk_highlights.append(
                    ReviewFinding(
                        severity="medium",
                        title=f"Material open risk: {risk['title']}",
                        detail=(
                            f"The recorded exposure score is {score}; confirm that the "
                            "response plan and owner are sufficient."
                        ),
                        related_type="risk",
                        related_id=risk["id"],
                    )
                )
        if not risks:
            risk_highlights.append(
                ReviewFinding(
                    severity="medium",
                    title="No risks are recorded",
                    detail=(
                        "Reviewers should confirm whether operational, financial, legal, "
                        "ethical, adoption, and reputational risks have been considered."
                    ),
                )
            )

        today = _as_date(snapshot.get("generated_at")) or date.today()
        review_triggers: list[ReviewFinding] = []
        for assumption in assumptions:
            review_date = _as_date(assumption.get("review_date"))
            if review_date and review_date < today:
                review_triggers.append(
                    ReviewFinding(
                        severity="medium",
                        title=f"Assumption is overdue for re-verification: {assumption['statement']}",
                        detail=(
                            f"Its review date ({review_date.isoformat()}) has passed. "
                            "Confirm whether it still holds before relying on it further."
                        ),
                        related_type="assumption",
                        related_id=assumption["id"],
                    )
                )
        for risk in risks:
            review_date = _as_date(risk.get("review_date"))
            if review_date and review_date < today:
                review_triggers.append(
                    ReviewFinding(
                        severity="medium",
                        title=f"Risk is overdue for review: {risk['title']}",
                        detail=(
                            f"Its review date ({review_date.isoformat()}) has passed. "
                            "Confirm whether the likelihood, impact, or response plan "
                            "has changed."
                        ),
                        related_type="risk",
                        related_id=risk["id"],
                    )
                )

        current_text = " ".join(
            [
                snapshot["decision"]["title"],
                snapshot["decision"]["decision_question"],
                snapshot["decision"]["purpose"],
                snapshot["decision"]["context"],
            ]
        )
        similar: list[SimilarDecision] = []
        for historical in snapshot["historical_decisions"]:
            historical_text = " ".join(
                [
                    historical["title"],
                    historical["decision_question"],
                    historical["purpose"],
                    historical["context"],
                    " ".join(historical["lesson_titles"]),
                ]
            )
            score = _similarity(current_text, historical_text)
            if score >= 0.08:
                similar.append(
                    SimilarDecision(
                        decision_id=historical["id"],
                        title=historical["title"],
                        status=historical["status"],
                        similarity=round(score, 3),
                        url=f"/decisions/{historical['id']}",
                        reason="Shared terms in the decision framing and recorded lessons.",
                    )
                )
        similar.sort(key=lambda item: (-item.similarity, item.title))

        finding_count = sum(
            len(items)
            for items in [
                missing_evidence,
                unsupported_assumptions,
                contradictory_evidence,
                duplicate_evidence,
                missing_stakeholders,
                risk_highlights,
                review_triggers,
            ]
        )
        summary = (
            f"This advisory review examined {len(options)} active option(s), "
            f"{len(evidence)} evidence item(s), {len(assumptions)} assumption(s), "
            f"{len(risks)} risk(s), and {len(participants)} participant(s). "
            f"It surfaced {finding_count} point(s) for human consideration."
        )
        return AIReviewOutput(
            summary=summary,
            missing_evidence=missing_evidence,
            unsupported_assumptions=unsupported_assumptions,
            contradictory_evidence=contradictory_evidence,
            duplicate_evidence=duplicate_evidence,
            missing_stakeholders=missing_stakeholders,
            risk_highlights=risk_highlights,
            review_triggers=review_triggers,
            similar_decisions=similar[:5],
            limitations=[
                (
                    "This review uses explicit rules and recorded data; it cannot "
                    "determine truth, intent, or organisational context that was not "
                    "entered."
                ),
                (
                    "Findings are advisory prompts for human judgement and do not alter "
                    "any decision record."
                ),
            ],
        )

    def summarise_analytics(self, *, metrics: dict[str, Any]) -> AnalyticsNarrative:
        totals = metrics["totals"]
        flow = metrics["flow"]
        learning = metrics["learning"]

        if totals["decisions"] == 0:
            return AnalyticsNarrative(
                headline="No decisions have been recorded yet.",
                observations=[
                    AnalyticsObservation(
                        severity="low",
                        title="This organisation has no decision history yet",
                        detail="Metrics will become meaningful once decisions are framed and tracked.",
                    )
                ],
                generated_by=self.label,
            )

        headline = (
            f"{totals['decisions']} decision(s) tracked: {totals['open_decisions']} open, "
            f"{totals['finalised_decisions']} finalised, {totals['active_lessons']} active lesson(s)."
        )

        observations: list[AnalyticsObservation] = []

        overdue = flow["overdue_target_decisions"]
        if overdue > 0:
            observations.append(
                AnalyticsObservation(
                    severity="high",
                    title=f"{overdue} open decision(s) are past their target date",
                    detail="These decisions have a target_decision_date in the past and remain open.",
                )
            )

        coverage = flow["contribution_coverage_percent"]
        if coverage is not None:
            if coverage < 50:
                observations.append(
                    AnalyticsObservation(
                        severity="medium",
                        title=f"Contribution coverage is low ({coverage}%)",
                        detail="Fewer than half of open decisions have at least two active participants.",
                    )
                )
            elif coverage == 100:
                observations.append(
                    AnalyticsObservation(
                        severity="low",
                        title="Every open decision has at least two active participants",
                        detail="Contribution coverage is at 100% across open decisions.",
                    )
                )

        due_reviews = learning["reviews_due_or_overdue"]
        if due_reviews > 0:
            observations.append(
                AnalyticsObservation(
                    severity="medium",
                    title=f"{due_reviews} outcome review(s) are due or overdue",
                    detail="These decisions have passed their review_due_date without a recorded outcome review.",
                )
            )

        median_days = flow["median_days_to_finalise"]
        if median_days is not None and median_days > 60:
            observations.append(
                AnalyticsObservation(
                    severity="medium",
                    title=f"Median time to finalise is {median_days} days",
                    detail="Recent finalised decisions took a relatively long time from creation to finalisation.",
                )
            )

        success_rate = learning["outcome_success_percent"]
        if success_rate is not None:
            observations.append(
                AnalyticsObservation(
                    severity="low" if success_rate >= 60 else "medium",
                    title=f"{success_rate}% of completed outcome reviews met or exceeded expectations",
                    detail=f"Based on {learning['outcome_reviews_completed']} completed outcome review(s).",
                )
            )

        if not observations:
            observations.append(
                AnalyticsObservation(
                    severity="low",
                    title="No notable risk signals in the current metrics",
                    detail="Open decisions are on track, and there is not yet enough outcome history to assess further.",
                )
            )

        return AnalyticsNarrative(headline=headline, observations=observations, generated_by=self.label)
