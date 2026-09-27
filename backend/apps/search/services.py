"""PostgreSQL full-text search across tenant-owned decision knowledge."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db import connection

from apps.assumptions.models import Assumption
from apps.contributions.models import ContributionRequest, FacilitationSession
from apps.decision_analysis.models import DecisionIssue, ExecutiveDecisionSummary
from apps.decision_options.models import DecisionOption
from apps.decisions.models import Decision
from apps.evaluations.models import EvaluationExercise, MinorityReport, PrioritisationPortfolio
from apps.evidence.models import Evidence
from apps.foresight.models import (
    Driver,
    FeedbackLoop,
    ForesightCanvas,
    Scenario,
    ScenarioSet,
    Signal,
    Signpost,
    Source,
    StrategicImplication,
)
from apps.lessons.models import Lesson
from apps.methodology.models import DecisionMethod
from apps.organisations.models import Organisation
from apps.reviews.models import DecisionReview
from apps.risks.models import Risk


@dataclass(frozen=True)
class SearchResult:
    kind: str
    object_id: str
    decision_id: str
    title: str
    snippet: str
    url: str
    rank: float


def _snippet(values: Iterable[str], query: str, limit: int = 240) -> str:
    text = " ".join(value.strip() for value in values if value and value.strip())
    if not text:
        return ""
    lowered = text.casefold()
    words = [word.casefold() for word in query.split() if len(word) > 1]
    indexes = [lowered.find(word) for word in words if lowered.find(word) >= 0]
    start = max(0, min(indexes) - 70) if indexes else 0
    excerpt = text[start : start + limit].strip()
    if start:
        excerpt = f"…{excerpt}"
    if start + limit < len(text):
        excerpt = f"{excerpt}…"
    return excerpt


def _fallback_search_organisation(
    *, organisation: Organisation, query_text: str
) -> list[SearchResult]:
    """Provide deterministic tenant search on non-PostgreSQL development databases.

    Production uses PostgreSQL ranking. The documented fast test path uses
    SQLite, where PostgreSQL search-vector SQL is invalid; this bounded
    fallback keeps the same record coverage and result contract without
    pretending to reproduce PostgreSQL's linguistic ranking.
    """

    words = [word.casefold() for word in query_text.split() if len(word) > 1]
    results: list[SearchResult] = []

    def text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, (list, tuple, set)):
            return " ".join(text(item) for item in value)
        return str(value)

    def add(
        *,
        items: Iterable[Any],
        kind: str,
        title: Callable[[Any], str],
        values: Callable[[Any], Iterable[Any]],
        url: Callable[[Any], str],
        decision_id: Callable[[Any], Any] = lambda item: "",
        limit: int = 15,
    ) -> None:
        matches: list[SearchResult] = []
        for item in items:
            item_title = text(title(item))
            item_values = [text(value) for value in values(item)]
            searchable = " ".join([item_title, *item_values]).casefold()
            if not words or not all(word in searchable for word in words):
                continue
            title_text = item_title.casefold()
            score = sum(3 for word in words if word in title_text) + sum(
                searchable.count(word) for word in words
            )
            matches.append(
                SearchResult(
                    kind=kind,
                    object_id=str(item.id),
                    decision_id=str(decision_id(item) or ""),
                    title=item_title,
                    snippet=_snippet(item_values, query_text),
                    url=url(item),
                    rank=float(score),
                )
            )
        results.extend(sorted(matches, key=lambda result: (-result.rank, result.title))[:limit])

    organisation_url = f"/organisations/{organisation.id}"
    add(
        items=DecisionMethod.objects.filter(organisation=organisation).exclude(
            status=DecisionMethod.Status.RETIRED
        ),
        kind="decision method",
        title=lambda item: item.name,
        values=lambda item: [item.summary, item.best_for],
        url=lambda item: f"{organisation_url}/methods",
        limit=10,
    )
    add(
        items=Source.objects.filter(organisation=organisation),
        kind="source",
        title=lambda item: item.title,
        values=lambda item: [
            item.author,
            item.publisher,
            item.reference,
            item.notes,
        ],
        url=lambda item: f"{organisation_url}/foresight?source={item.id}",
        limit=10,
    )
    add(
        items=Signal.objects.filter(organisation=organisation),
        kind="signal",
        title=lambda item: item.title,
        values=lambda item: [
            item.summary,
            item.future_implication,
            item.domain,
            item.geography,
        ],
        url=lambda item: f"{organisation_url}/foresight?signal={item.id}",
    )
    add(
        items=ForesightCanvas.objects.filter(organisation=organisation),
        kind="foresight_canvas",
        title=lambda item: item.title,
        values=lambda item: [item.focal_question, item.scope],
        url=lambda item: f"{organisation_url}/foresight/canvases/{item.id}",
        limit=10,
    )
    add(
        items=Driver.objects.filter(canvas__organisation=organisation),
        kind="foresight_driver",
        title=lambda item: item.title,
        values=lambda item: [item.description],
        url=lambda item: f"{organisation_url}/foresight/canvases/{item.canvas_id}?tab=drivers",
        limit=12,
    )
    add(
        items=FeedbackLoop.objects.filter(canvas__organisation=organisation),
        kind="foresight_feedback_loop",
        title=lambda item: item.name,
        values=lambda item: [item.description, item.rationale],
        url=lambda item: f"{organisation_url}/foresight/canvases/{item.canvas_id}?tab=system",
        limit=10,
    )
    add(
        items=ScenarioSet.objects.filter(canvas__organisation=organisation),
        kind="foresight_scenario_set",
        title=lambda item: item.title,
        values=lambda item: [
            item.purpose,
            item.axis_x_low_label,
            item.axis_x_high_label,
            item.axis_y_low_label,
            item.axis_y_high_label,
        ],
        decision_id=lambda item: item.linked_decision_id,
        url=lambda item: (
            f"{organisation_url}/foresight/canvases/{item.canvas_id}/scenarios/{item.id}"
        ),
        limit=10,
    )
    add(
        items=Scenario.objects.filter(
            scenario_set__canvas__organisation=organisation
        ).select_related("scenario_set"),
        kind="foresight_scenario",
        title=lambda item: item.title,
        values=lambda item: [item.headline, item.narrative, item.key_assumptions],
        decision_id=lambda item: item.scenario_set.linked_decision_id,
        url=lambda item: (
            f"{organisation_url}/foresight/canvases/{item.scenario_set.canvas_id}/scenarios/"
            f"{item.scenario_set_id}"
        ),
        limit=12,
    )
    add(
        items=Signpost.objects.filter(
            scenario_set__canvas__organisation=organisation
        ).select_related("scenario_set"),
        kind="foresight_signpost",
        title=lambda item: item.title,
        values=lambda item: [item.description, item.indicator, item.threshold],
        decision_id=lambda item: item.scenario_set.linked_decision_id,
        url=lambda item: (
            f"{organisation_url}/foresight/canvases/{item.scenario_set.canvas_id}/scenarios/"
            f"{item.scenario_set_id}?tab=signposts"
        ),
        limit=10,
    )
    add(
        items=StrategicImplication.objects.filter(canvas__organisation=organisation),
        kind="strategic_implication",
        title=lambda item: item.title,
        values=lambda item: [item.description],
        decision_id=lambda item: item.linked_decision_id,
        url=lambda item: f"{organisation_url}/foresight/canvases/{item.canvas_id}?tab=implications",
        limit=12,
    )
    add(
        items=Decision.objects.filter(organisation=organisation),
        kind="decision",
        title=lambda item: item.title,
        values=lambda item: [
            item.decision_question,
            item.purpose,
            item.context,
            item.scope,
        ],
        decision_id=lambda item: item.id,
        url=lambda item: f"/decisions/{item.id}",
    )
    add(
        items=DecisionOption.objects.filter(organisation=organisation),
        kind="option",
        title=lambda item: item.title,
        values=lambda item: [
            item.description,
            item.expected_benefits,
            item.tradeoffs,
        ],
        decision_id=lambda item: item.decision_id,
        url=lambda item: f"/decisions/{item.decision_id}/reasoning/options",
        limit=10,
    )
    add(
        items=Evidence.objects.filter(organisation=organisation),
        kind="evidence",
        title=lambda item: item.title,
        values=lambda item: [item.summary, item.source_reference],
        decision_id=lambda item: item.decision_id,
        url=lambda item: f"/decisions/{item.decision_id}/reasoning/evidence",
        limit=10,
    )
    add(
        items=Assumption.objects.filter(organisation=organisation),
        kind="assumption",
        title=lambda item: item.statement[:160],
        values=lambda item: [
            item.statement,
            item.rationale,
            item.impact_if_false,
            item.verification_notes,
        ],
        decision_id=lambda item: item.decision_id,
        url=lambda item: f"/decisions/{item.decision_id}/reasoning/assumptions",
        limit=10,
    )
    add(
        items=Risk.objects.filter(organisation=organisation),
        kind="risk",
        title=lambda item: item.title,
        values=lambda item: [item.description, item.mitigation_plan],
        decision_id=lambda item: item.decision_id,
        url=lambda item: f"/decisions/{item.decision_id}/reasoning/risks",
        limit=10,
    )
    add(
        items=DecisionReview.objects.filter(organisation=organisation).select_related("decision"),
        kind="outcome review",
        title=lambda item: f"Outcome: {item.decision.title}",
        values=lambda item: [
            item.commitment_statement,
            item.success_measures,
            item.implementation_plan,
            item.implementation_summary,
            item.outcome_summary,
            item.review_evidence,
            item.unintended_consequences,
        ],
        decision_id=lambda item: item.decision_id,
        url=lambda item: f"/decisions/{item.decision_id}/outcomes",
        limit=10,
    )
    add(
        items=Lesson.objects.filter(organisation=organisation, status=Lesson.Status.ACTIVE),
        kind="lesson",
        title=lambda item: item.title,
        values=lambda item: [
            item.insight,
            item.applicability,
            item.recommended_change,
        ],
        decision_id=lambda item: item.decision_id,
        url=lambda item: f"/decisions/{item.decision_id}/outcomes",
    )
    add(
        items=EvaluationExercise.objects.filter(organisation=organisation),
        kind="collective evaluation",
        title=lambda item: item.title,
        values=lambda item: [item.purpose],
        decision_id=lambda item: item.decision_id,
        url=lambda item: f"/decisions/{item.decision_id}/evaluations",
        limit=10,
    )
    add(
        items=MinorityReport.objects.filter(
            organisation=organisation, status=MinorityReport.Status.PUBLISHED
        ).select_related("exercise"),
        kind="minority report",
        title=lambda item: item.title,
        values=lambda item: [item.analysis, item.recommendation],
        decision_id=lambda item: item.exercise.decision_id,
        url=lambda item: f"/decisions/{item.exercise.decision_id}/evaluations",
        limit=10,
    )
    add(
        items=PrioritisationPortfolio.objects.filter(organisation=organisation),
        kind="prioritisation portfolio",
        title=lambda item: item.title,
        values=lambda item: [item.purpose],
        url=lambda item: f"{organisation_url}/prioritisation",
        limit=10,
    )
    add(
        items=DecisionIssue.objects.filter(organisation=organisation),
        kind="decision analysis issue",
        title=lambda item: item.title,
        values=lambda item: [item.description, item.resolution],
        decision_id=lambda item: item.decision_id,
        url=lambda item: f"/decisions/{item.decision_id}/analysis",
        limit=12,
    )
    add(
        items=ExecutiveDecisionSummary.objects.filter(organisation=organisation)
        .exclude(status=ExecutiveDecisionSummary.Status.SUPERSEDED)
        .select_related("decision"),
        kind="executive decision summary",
        title=lambda item: f"{item.decision.title} - executive summary",
        values=lambda item: [
            item.context_summary,
            item.proposed_judgement,
            item.unresolved_issues,
            item.implementation_implications,
        ],
        decision_id=lambda item: item.decision_id,
        url=lambda item: f"/decisions/{item.decision_id}/analysis",
        limit=10,
    )
    add(
        items=ContributionRequest.objects.filter(organisation=organisation).exclude(
            status=ContributionRequest.Status.DRAFT
        ),
        kind="contribution request",
        title=lambda item: item.title,
        values=lambda item: [item.instructions],
        decision_id=lambda item: item.decision_id,
        url=lambda item: f"/decisions/{item.decision_id}/contributions#request-{item.id}",
        limit=12,
    )
    add(
        items=FacilitationSession.objects.filter(organisation=organisation),
        kind="facilitation session",
        title=lambda item: item.title,
        values=lambda item: [item.objective, item.agenda],
        decision_id=lambda item: item.decision_id,
        url=lambda item: f"/decisions/{item.decision_id}/contributions#session-{item.id}",
        limit=10,
    )
    return sorted(results, key=lambda item: (-item.rank, item.kind, item.title))[:40]


def search_organisation(*, organisation: Organisation, query_text: str) -> list[SearchResult]:
    """Search only records within one established tenant boundary."""
    term = query_text.strip()
    if len(term) < 2:
        return []
    if connection.vendor != "postgresql":
        return _fallback_search_organisation(organisation=organisation, query_text=term)
    query = SearchQuery(term, search_type="websearch", config="english")
    results: list[SearchResult] = []
    # Django's dynamically annotated querysets do not preserve a reusable item
    # type across the many heterogeneous loops in this aggregation function.
    item: Any

    method_vector = (
        SearchVector("name", weight="A", config="english")
        + SearchVector("summary", weight="A", config="english")
        + SearchVector("best_for", weight="B", config="english")
    )
    methods = (
        DecisionMethod.objects.filter(organisation=organisation)
        .exclude(status=DecisionMethod.Status.RETIRED)
        .annotate(search=method_vector, rank=SearchRank(method_vector, query))
        .filter(search=query)
        .order_by("-rank", "name")[:10]
    )
    for item in methods:
        results.append(
            SearchResult(
                kind="decision method",
                object_id=str(item.id),
                decision_id="",
                title=item.name,
                snippet=_snippet([item.summary, item.best_for], term),
                url=f"/organisations/{organisation.id}/methods",
                rank=float(item.rank),
            )
        )

    source_vector = (
        SearchVector("title", weight="A", config="english")
        + SearchVector("author", weight="B", config="english")
        + SearchVector("publisher", weight="B", config="english")
        + SearchVector("reference", weight="C", config="english")
        + SearchVector("notes", weight="C", config="english")
    )
    sources = (
        Source.objects.filter(organisation=organisation)
        .annotate(search=source_vector, rank=SearchRank(source_vector, query))
        .filter(search=query)
        .order_by("-rank", "-updated_at")[:10]
    )
    for item in sources:
        results.append(
            SearchResult(
                kind="source",
                object_id=str(item.id),
                decision_id="",
                title=item.title,
                snippet=_snippet([item.author, item.publisher, item.reference, item.notes], term),
                url=f"/organisations/{organisation.id}/foresight?source={item.id}",
                rank=float(item.rank),
            )
        )

    signal_vector = (
        SearchVector("title", weight="A", config="english")
        + SearchVector("summary", weight="A", config="english")
        + SearchVector("future_implication", weight="B", config="english")
        + SearchVector("domain", weight="C", config="english")
        + SearchVector("geography", weight="C", config="english")
    )
    signals = (
        Signal.objects.filter(organisation=organisation)
        .annotate(search=signal_vector, rank=SearchRank(signal_vector, query))
        .filter(search=query)
        .order_by("-rank", "-updated_at")[:15]
    )
    for item in signals:
        results.append(
            SearchResult(
                kind="signal",
                object_id=str(item.id),
                decision_id="",
                title=item.title,
                snippet=_snippet(
                    [item.summary, item.future_implication, item.domain, item.geography], term
                ),
                url=f"/organisations/{organisation.id}/foresight?signal={item.id}",
                rank=float(item.rank),
            )
        )

    canvas_vector = (
        SearchVector("title", weight="A", config="english")
        + SearchVector("focal_question", weight="A", config="english")
        + SearchVector("scope", weight="B", config="english")
    )
    canvases = (
        ForesightCanvas.objects.filter(organisation=organisation)
        .annotate(search=canvas_vector, rank=SearchRank(canvas_vector, query))
        .filter(search=query)
        .order_by("-rank", "-updated_at")[:10]
    )
    for item in canvases:
        results.append(
            SearchResult(
                kind="foresight_canvas",
                object_id=str(item.id),
                decision_id="",
                title=item.title,
                snippet=_snippet([item.focal_question, item.scope], term),
                url=f"/organisations/{organisation.id}/foresight/canvases/{item.id}",
                rank=float(item.rank),
            )
        )

    driver_vector = SearchVector("title", weight="A", config="english") + SearchVector(
        "description", weight="A", config="english"
    )
    drivers = (
        Driver.objects.filter(canvas__organisation=organisation)
        .select_related("canvas")
        .annotate(search=driver_vector, rank=SearchRank(driver_vector, query))
        .filter(search=query)
        .order_by("-rank", "-updated_at")[:12]
    )
    for item in drivers:
        results.append(
            SearchResult(
                kind="foresight_driver",
                object_id=str(item.id),
                decision_id="",
                title=item.title,
                snippet=_snippet([item.description, item.get_driver_type_display()], term),
                url=f"/organisations/{organisation.id}/foresight/canvases/{item.canvas_id}?tab=drivers",
                rank=float(item.rank),
            )
        )

    loop_vector = (
        SearchVector("name", weight="A", config="english")
        + SearchVector("description", weight="A", config="english")
        + SearchVector("rationale", weight="B", config="english")
    )
    feedback_loops = (
        FeedbackLoop.objects.filter(canvas__organisation=organisation)
        .select_related("canvas")
        .annotate(search=loop_vector, rank=SearchRank(loop_vector, query))
        .filter(search=query)
        .order_by("-rank", "name")[:10]
    )
    for item in feedback_loops:
        results.append(
            SearchResult(
                kind="foresight_feedback_loop",
                object_id=str(item.id),
                decision_id="",
                title=item.name,
                snippet=_snippet([item.description, item.rationale], term),
                url=(
                    f"/organisations/{organisation.id}/foresight/canvases/"
                    f"{item.canvas_id}?tab=system"
                ),
                rank=float(item.rank),
            )
        )

    scenario_set_vector = (
        SearchVector("title", weight="A", config="english")
        + SearchVector("purpose", weight="A", config="english")
        + SearchVector("axis_x_low_label", weight="C", config="english")
        + SearchVector("axis_x_high_label", weight="C", config="english")
        + SearchVector("axis_y_low_label", weight="C", config="english")
        + SearchVector("axis_y_high_label", weight="C", config="english")
    )
    scenario_sets = (
        ScenarioSet.objects.filter(canvas__organisation=organisation)
        .select_related("canvas")
        .annotate(
            search=scenario_set_vector,
            rank=SearchRank(scenario_set_vector, query),
        )
        .filter(search=query)
        .order_by("-rank", "-updated_at")[:10]
    )
    for item in scenario_sets:
        results.append(
            SearchResult(
                kind="foresight_scenario_set",
                object_id=str(item.id),
                decision_id=str(item.linked_decision_id or ""),
                title=item.title,
                snippet=_snippet([item.purpose], term),
                url=(
                    f"/organisations/{organisation.id}/foresight/canvases/"
                    f"{item.canvas_id}/scenarios/{item.id}"
                ),
                rank=float(item.rank),
            )
        )

    scenario_vector = (
        SearchVector("title", weight="A", config="english")
        + SearchVector("headline", weight="A", config="english")
        + SearchVector("narrative", weight="B", config="english")
        + SearchVector("key_assumptions", weight="C", config="english")
    )
    scenarios = (
        Scenario.objects.filter(scenario_set__canvas__organisation=organisation)
        .select_related("scenario_set__canvas")
        .annotate(search=scenario_vector, rank=SearchRank(scenario_vector, query))
        .filter(search=query)
        .order_by("-rank", "title")[:12]
    )
    for item in scenarios:
        results.append(
            SearchResult(
                kind="foresight_scenario",
                object_id=str(item.id),
                decision_id=str(item.scenario_set.linked_decision_id or ""),
                title=item.title,
                snippet=_snippet([item.headline, item.narrative], term),
                url=(
                    f"/organisations/{organisation.id}/foresight/canvases/"
                    f"{item.scenario_set.canvas_id}/scenarios/{item.scenario_set_id}"
                ),
                rank=float(item.rank),
            )
        )

    signpost_vector = (
        SearchVector("title", weight="A", config="english")
        + SearchVector("description", weight="B", config="english")
        + SearchVector("indicator", weight="A", config="english")
        + SearchVector("threshold", weight="B", config="english")
    )
    signposts = (
        Signpost.objects.filter(scenario_set__canvas__organisation=organisation)
        .select_related("scenario_set__canvas")
        .annotate(search=signpost_vector, rank=SearchRank(signpost_vector, query))
        .filter(search=query)
        .order_by("-rank", "title")[:10]
    )
    for item in signposts:
        results.append(
            SearchResult(
                kind="foresight_signpost",
                object_id=str(item.id),
                decision_id=str(item.scenario_set.linked_decision_id or ""),
                title=item.title,
                snippet=_snippet([item.indicator, item.threshold, item.description], term),
                url=(
                    f"/organisations/{organisation.id}/foresight/canvases/"
                    f"{item.scenario_set.canvas_id}/scenarios/{item.scenario_set_id}"
                    "?tab=signposts"
                ),
                rank=float(item.rank),
            )
        )

    implication_vector = SearchVector("title", weight="A", config="english") + SearchVector(
        "description", weight="A", config="english"
    )
    implications = (
        StrategicImplication.objects.filter(canvas__organisation=organisation)
        .select_related("canvas", "linked_decision")
        .annotate(search=implication_vector, rank=SearchRank(implication_vector, query))
        .filter(search=query)
        .order_by("-rank", "-updated_at")[:12]
    )
    for item in implications:
        results.append(
            SearchResult(
                kind="strategic_implication",
                object_id=str(item.id),
                decision_id=str(item.linked_decision_id or ""),
                title=item.title,
                snippet=_snippet([item.description, item.get_implication_type_display()], term),
                url=f"/organisations/{organisation.id}/foresight/canvases/{item.canvas_id}?tab=implications",
                rank=float(item.rank),
            )
        )

    decision_vector = (
        SearchVector("title", weight="A", config="english")
        + SearchVector("decision_question", weight="A", config="english")
        + SearchVector("purpose", weight="B", config="english")
        + SearchVector("context", weight="C", config="english")
        + SearchVector("scope", weight="C", config="english")
    )
    decisions = (
        Decision.objects.filter(organisation=organisation)
        .annotate(search=decision_vector, rank=SearchRank(decision_vector, query))
        .filter(search=query)
        .order_by("-rank", "-updated_at")[:15]
    )
    for item in decisions:
        results.append(
            SearchResult(
                kind="decision",
                object_id=str(item.id),
                decision_id=str(item.id),
                title=item.title,
                snippet=_snippet(
                    [item.decision_question, item.purpose, item.context, item.scope], term
                ),
                url=f"/decisions/{item.id}",
                rank=float(item.rank),
            )
        )

    option_vector = (
        SearchVector("title", weight="A", config="english")
        + SearchVector("description", weight="B", config="english")
        + SearchVector("expected_benefits", weight="C", config="english")
        + SearchVector("tradeoffs", weight="C", config="english")
    )
    options = (
        DecisionOption.objects.filter(organisation=organisation)
        .select_related("decision")
        .annotate(search=option_vector, rank=SearchRank(option_vector, query))
        .filter(search=query)
        .order_by("-rank", "-updated_at")[:10]
    )
    for item in options:
        results.append(
            SearchResult(
                kind="option",
                object_id=str(item.id),
                decision_id=str(item.decision_id),
                title=item.title,
                snippet=_snippet([item.description, item.expected_benefits, item.tradeoffs], term),
                url=f"/decisions/{item.decision_id}/reasoning/options",
                rank=float(item.rank),
            )
        )

    evidence_vector = (
        SearchVector("title", weight="A", config="english")
        + SearchVector("summary", weight="B", config="english")
        + SearchVector("source_reference", weight="C", config="english")
    )
    evidence_items = (
        Evidence.objects.filter(organisation=organisation)
        .select_related("decision")
        .annotate(search=evidence_vector, rank=SearchRank(evidence_vector, query))
        .filter(search=query)
        .order_by("-rank", "-updated_at")[:10]
    )
    for item in evidence_items:
        results.append(
            SearchResult(
                kind="evidence",
                object_id=str(item.id),
                decision_id=str(item.decision_id),
                title=item.title,
                snippet=_snippet([item.summary, item.source_reference], term),
                url=f"/decisions/{item.decision_id}/reasoning/evidence",
                rank=float(item.rank),
            )
        )

    assumption_vector = (
        SearchVector("statement", weight="A", config="english")
        + SearchVector("rationale", weight="B", config="english")
        + SearchVector("impact_if_false", weight="B", config="english")
        + SearchVector("verification_notes", weight="C", config="english")
    )
    assumptions = (
        Assumption.objects.filter(organisation=organisation)
        .select_related("decision")
        .annotate(search=assumption_vector, rank=SearchRank(assumption_vector, query))
        .filter(search=query)
        .order_by("-rank", "-updated_at")[:10]
    )
    for item in assumptions:
        results.append(
            SearchResult(
                kind="assumption",
                object_id=str(item.id),
                decision_id=str(item.decision_id),
                title=item.statement[:160],
                snippet=_snippet(
                    [item.rationale, item.impact_if_false, item.verification_notes], term
                ),
                url=f"/decisions/{item.decision_id}/reasoning/assumptions",
                rank=float(item.rank),
            )
        )

    risk_vector = (
        SearchVector("title", weight="A", config="english")
        + SearchVector("description", weight="B", config="english")
        + SearchVector("mitigation_plan", weight="B", config="english")
    )
    risks = (
        Risk.objects.filter(organisation=organisation)
        .select_related("decision")
        .annotate(search=risk_vector, rank=SearchRank(risk_vector, query))
        .filter(search=query)
        .order_by("-rank", "-updated_at")[:10]
    )
    for item in risks:
        results.append(
            SearchResult(
                kind="risk",
                object_id=str(item.id),
                decision_id=str(item.decision_id),
                title=item.title,
                snippet=_snippet([item.description, item.mitigation_plan], term),
                url=f"/decisions/{item.decision_id}/reasoning/risks",
                rank=float(item.rank),
            )
        )

    review_vector = (
        SearchVector("commitment_statement", weight="A", config="english")
        + SearchVector("success_measures", weight="B", config="english")
        + SearchVector("implementation_plan", weight="B", config="english")
        + SearchVector("implementation_summary", weight="B", config="english")
        + SearchVector("outcome_summary", weight="A", config="english")
        + SearchVector("review_evidence", weight="C", config="english")
        + SearchVector("unintended_consequences", weight="C", config="english")
    )
    reviews = (
        DecisionReview.objects.filter(organisation=organisation)
        .select_related("decision")
        .annotate(search=review_vector, rank=SearchRank(review_vector, query))
        .filter(search=query)
        .order_by("-rank", "-updated_at")[:10]
    )
    for item in reviews:
        results.append(
            SearchResult(
                kind="outcome review",
                object_id=str(item.id),
                decision_id=str(item.decision_id),
                title=f"Outcome: {item.decision.title}",
                snippet=_snippet(
                    [
                        item.commitment_statement,
                        item.implementation_summary,
                        item.outcome_summary,
                        item.review_evidence,
                        item.unintended_consequences,
                    ],
                    term,
                ),
                url=f"/decisions/{item.decision_id}/outcomes",
                rank=float(item.rank),
            )
        )

    lesson_vector = (
        SearchVector("title", weight="A", config="english")
        + SearchVector("insight", weight="A", config="english")
        + SearchVector("applicability", weight="B", config="english")
        + SearchVector("recommended_change", weight="B", config="english")
    )
    lessons = (
        Lesson.objects.filter(organisation=organisation, status=Lesson.Status.ACTIVE)
        .select_related("decision")
        .annotate(search=lesson_vector, rank=SearchRank(lesson_vector, query))
        .filter(search=query)
        .order_by("-rank", "-updated_at")[:15]
    )
    for item in lessons:
        results.append(
            SearchResult(
                kind="lesson",
                object_id=str(item.id),
                decision_id=str(item.decision_id),
                title=item.title,
                snippet=_snippet([item.insight, item.applicability, item.recommended_change], term),
                url=f"/decisions/{item.decision_id}/outcomes",
                rank=float(item.rank),
            )
        )

    evaluation_vector = SearchVector("title", weight="A", config="english") + SearchVector(
        "purpose", weight="A", config="english"
    )
    evaluations = (
        EvaluationExercise.objects.filter(organisation=organisation)
        .select_related("decision")
        .annotate(search=evaluation_vector, rank=SearchRank(evaluation_vector, query))
        .filter(search=query)
        .order_by("-rank", "-updated_at")[:10]
    )
    for item in evaluations:
        results.append(
            SearchResult(
                kind="collective evaluation",
                object_id=str(item.id),
                decision_id=str(item.decision_id),
                title=item.title,
                snippet=_snippet([item.purpose, item.get_method_display()], term),
                url=f"/decisions/{item.decision_id}/evaluations",
                rank=float(item.rank),
            )
        )

    minority_vector = (
        SearchVector("title", weight="A", config="english")
        + SearchVector("analysis", weight="A", config="english")
        + SearchVector("recommendation", weight="B", config="english")
    )
    minority_reports = (
        MinorityReport.objects.filter(
            organisation=organisation, status=MinorityReport.Status.PUBLISHED
        )
        .select_related("exercise__decision")
        .annotate(search=minority_vector, rank=SearchRank(minority_vector, query))
        .filter(search=query)
        .order_by("-rank", "-published_at")[:10]
    )
    for item in minority_reports:
        results.append(
            SearchResult(
                kind="minority report",
                object_id=str(item.id),
                decision_id=str(item.exercise.decision_id),
                title=item.title,
                snippet=_snippet([item.analysis, item.recommendation], term),
                url=f"/decisions/{item.exercise.decision_id}/evaluations",
                rank=float(item.rank),
            )
        )

    prioritisation_vector = SearchVector("title", weight="A", config="english") + SearchVector(
        "purpose", weight="A", config="english"
    )
    prioritisation_items = (
        PrioritisationPortfolio.objects.filter(organisation=organisation)
        .annotate(search=prioritisation_vector, rank=SearchRank(prioritisation_vector, query))
        .filter(search=query)
        .order_by("-rank", "-updated_at")[:10]
    )
    for item in prioritisation_items:
        results.append(
            SearchResult(
                kind="prioritisation portfolio",
                object_id=str(item.id),
                decision_id="",
                title=item.title,
                snippet=_snippet([item.purpose], term),
                url=f"/organisations/{organisation.id}/prioritisation",
                rank=float(item.rank),
            )
        )

    issue_vector = (
        SearchVector("title", weight="A", config="english")
        + SearchVector("description", weight="A", config="english")
        + SearchVector("resolution", weight="B", config="english")
    )
    analysis_issues = (
        DecisionIssue.objects.filter(organisation=organisation)
        .select_related("decision")
        .annotate(search=issue_vector, rank=SearchRank(issue_vector, query))
        .filter(search=query)
        .order_by("-rank", "-updated_at")[:12]
    )
    for item in analysis_issues:
        results.append(
            SearchResult(
                kind="decision analysis issue",
                object_id=str(item.id),
                decision_id=str(item.decision_id),
                title=item.title,
                snippet=_snippet(
                    [item.description, item.resolution, item.get_issue_type_display()], term
                ),
                url=f"/decisions/{item.decision_id}/analysis",
                rank=float(item.rank),
            )
        )

    summary_vector = (
        SearchVector("context_summary", weight="B", config="english")
        + SearchVector("proposed_judgement", weight="A", config="english")
        + SearchVector("unresolved_issues", weight="A", config="english")
        + SearchVector("implementation_implications", weight="B", config="english")
    )
    executive_summaries = (
        ExecutiveDecisionSummary.objects.filter(organisation=organisation)
        .exclude(status=ExecutiveDecisionSummary.Status.SUPERSEDED)
        .select_related("decision")
        .annotate(search=summary_vector, rank=SearchRank(summary_vector, query))
        .filter(search=query)
        .order_by("-rank", "-updated_at")[:10]
    )
    for item in executive_summaries:
        results.append(
            SearchResult(
                kind="executive decision summary",
                object_id=str(item.id),
                decision_id=str(item.decision_id),
                title=f"{item.decision.title} - executive summary",
                snippet=_snippet(
                    [
                        item.proposed_judgement,
                        item.unresolved_issues,
                        item.implementation_implications,
                    ],
                    term,
                ),
                url=f"/decisions/{item.decision_id}/analysis",
                rank=float(item.rank),
            )
        )

    contribution_vector = SearchVector("title", weight="A", config="english") + SearchVector(
        "instructions", weight="A", config="english"
    )
    contribution_requests = (
        ContributionRequest.objects.filter(organisation=organisation)
        .exclude(status=ContributionRequest.Status.DRAFT)
        .select_related("decision")
        .annotate(search=contribution_vector, rank=SearchRank(contribution_vector, query))
        .filter(search=query)
        .order_by("-rank", "due_at")[:12]
    )
    for item in contribution_requests:
        results.append(
            SearchResult(
                kind="contribution request",
                object_id=str(item.id),
                decision_id=str(item.decision_id),
                title=item.title,
                snippet=_snippet(
                    [item.instructions, item.get_kind_display(), item.get_status_display()], term
                ),
                url=f"/decisions/{item.decision_id}/contributions#request-{item.id}",
                rank=float(item.rank),
            )
        )

    session_vector = (
        SearchVector("title", weight="A", config="english")
        + SearchVector("objective", weight="A", config="english")
        + SearchVector("agenda", weight="B", config="english")
    )
    sessions = (
        FacilitationSession.objects.filter(organisation=organisation)
        .select_related("decision")
        .annotate(search=session_vector, rank=SearchRank(session_vector, query))
        .filter(search=query)
        .order_by("-rank", "starts_at")[:10]
    )
    for item in sessions:
        results.append(
            SearchResult(
                kind="facilitation session",
                object_id=str(item.id),
                decision_id=str(item.decision_id),
                title=item.title,
                snippet=_snippet([item.objective, item.agenda], term),
                url=f"/decisions/{item.decision_id}/contributions#session-{item.id}",
                rank=float(item.rank),
            )
        )

    return sorted(results, key=lambda item: (-item.rank, item.kind, item.title))[:40]
