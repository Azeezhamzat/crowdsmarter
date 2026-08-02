"""PostgreSQL full-text search across tenant-owned decision knowledge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

from apps.assumptions.models import Assumption
from apps.decision_options.models import DecisionOption
from apps.decisions.models import Decision
from apps.evidence.models import Evidence
from apps.lessons.models import Lesson
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


def search_organisation(*, organisation: Organisation, query_text: str) -> list[SearchResult]:
    """Search only records within one established tenant boundary."""
    term = query_text.strip()
    if len(term) < 2:
        return []
    query = SearchQuery(term, search_type="websearch", config="english")
    results: list[SearchResult] = []

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
                snippet=_snippet(
                    [item.description, item.expected_benefits, item.tradeoffs], term
                ),
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
                snippet=_snippet(
                    [item.insight, item.applicability, item.recommended_change], term
                ),
                url=f"/decisions/{item.decision_id}/outcomes",
                rank=float(item.rank),
            )
        )

    return sorted(results, key=lambda item: (-item.rank, item.kind, item.title))[:40]
