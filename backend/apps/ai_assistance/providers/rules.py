"""Transparent zero-cost decision review provider."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from .base import AIReviewOutput, ReviewFinding, SimilarDecision


_TOKEN_PATTERN = re.compile(r"[a-z0-9]{3,}")


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
                missing_stakeholders,
                risk_highlights,
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
            missing_stakeholders=missing_stakeholders,
            risk_highlights=risk_highlights,
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
