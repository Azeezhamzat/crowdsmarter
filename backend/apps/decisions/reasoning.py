"""Read-only decision reasoning readiness summaries."""

from __future__ import annotations

from typing import Any

from .models import Decision


def reasoning_summary(decision: Decision) -> dict[str, Any]:
    """Return transparent counts and blockers for structured review readiness."""
    from apps.assumptions.models import Assumption
    from apps.decision_options.models import DecisionOption
    from apps.evidence.models import Evidence
    from apps.risks.models import Risk

    active_options = DecisionOption.objects.filter(
        decision=decision, status=DecisionOption.Status.ACTIVE
    ).count()
    active_evidence = Evidence.objects.filter(
        decision=decision, status=Evidence.Status.ACTIVE
    ).count()
    active_assumptions = Assumption.objects.filter(
        decision=decision, status=Assumption.Status.ACTIVE
    ).count()
    invalidated_assumptions = Assumption.objects.filter(
        decision=decision,
        status=Assumption.Status.ACTIVE,
        verification_status=Assumption.VerificationStatus.INVALIDATED,
    ).count()
    current_risks = Risk.objects.filter(decision=decision).exclude(
        status=Risk.Status.CLOSED
    ).count()

    blockers: list[str] = []
    if active_options < 2:
        blockers.append("Add at least two active options.")
    if active_evidence < 1:
        blockers.append("Add at least one active evidence item.")
    if active_assumptions < 1:
        blockers.append("Add at least one active assumption.")
    if invalidated_assumptions:
        blockers.append("Resolve or retire invalidated assumptions.")
    if current_risks < 1:
        blockers.append("Add at least one current risk.")

    return {
        "active_options": active_options,
        "active_evidence": active_evidence,
        "active_assumptions": active_assumptions,
        "invalidated_assumptions": invalidated_assumptions,
        "current_risks": current_risks,
        "ready_for_decision": not blockers,
        "blockers": blockers,
    }
