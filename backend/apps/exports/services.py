"""Customer-owned organisation and decision export services."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from openpyxl import Workbook

from apps.accounts.models import User
from apps.ai_assistance.models import AIReview
from apps.assumptions.models import Assumption
from apps.audit.models import AuditEvent
from apps.collaboration.models import DiscussionEntry
from apps.contributions.models import (
    ContributionPreference, ContributionRequest, ContributionReview,
    ContributionSubmission, FacilitationSession, SessionParticipant,
)
from apps.decision_options.models import DecisionOption
from apps.decision_analysis.models import DecisionIssue, DecisionQualityReview, ExecutiveDecisionSummary
from apps.decisions.models import Decision, DecisionFinalisation, DecisionTransition
from apps.evidence.models import Evidence
from apps.evaluations.models import (
    EvaluationCriterion, EvaluationExercise, EvaluationResponse, EvaluationRound,
    EvaluationSubmission, MinorityReport, PortfolioAssessment, PortfolioCandidate,
    PortfolioCriterion, PortfolioSelection, PrioritisationPortfolio,
)
from apps.invitations.models import OrganisationInvitation
from apps.foresight.models import (
    CausalRelationship, Driver, DriverSignal, FeedbackLoop, FeedbackLoopDriver, FeedSubscription, ForesightCanvas,
    FuturesWheelConsequence, Signal, SignalDecisionLink, Source, SourceAttachment,
    Scenario, ScenarioDriverState, ScenarioImplicationLink, ScenarioReview, ScenarioSet,
    ScenarioSignpost, Signpost, SignpostObservation, StrategicImplication, SystemStakeholder,
    ThreeHorizonItem, Watchlist, WatchlistSignal, WindTunnelAssessment,
)
from apps.lessons.models import Lesson
from apps.organisations.models import Membership, MembershipEvent, Organisation, OrganisationDeletionRequest
from apps.methodology.models import DecisionMethod, DecisionMethodUsage, DecisionMethodVersion
from apps.participants.models import Participant
from apps.positions.models import Position
from apps.reviews.models import DecisionReview
from apps.risks.models import Risk
from apps.workspaces.models import Workspace

EXPORT_SCHEMA_VERSION = "1.8"
SENSITIVE_FIELD_NAMES = {"password", "token_digest"}


@dataclass(frozen=True)
class ExportArchive:
    """Binary export payload and download filename."""

    filename: str
    content: bytes


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (UUID, Decimal)):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return str(value)


def _serialise_instance(instance: models.Model) -> dict[str, Any]:
    record: dict[str, Any] = {}
    for field in instance._meta.concrete_fields:
        if field.name in SENSITIVE_FIELD_NAMES:
            continue
        if field.is_relation:
            record[field.name] = _json_safe(getattr(instance, field.attname))
        else:
            record[field.name] = _json_safe(field.value_from_object(instance))
    for field in instance._meta.many_to_many:
        if field.name in SENSITIVE_FIELD_NAMES:
            continue
        record[field.name] = [str(value) for value in getattr(instance, field.name).values_list("pk", flat=True)]
    return record


def _records(queryset: Iterable[models.Model]) -> list[dict[str, Any]]:
    return [_serialise_instance(instance) for instance in queryset]


def _user_records(users: Iterable[User]) -> list[dict[str, Any]]:
    return [
        {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "date_joined": user.date_joined.isoformat(),
        }
        for user in users
    ]


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")


def _csv_bytes(records: list[dict[str, Any]]) -> bytes:
    output = io.StringIO(newline="")
    if not records:
        output.write("No records\n")
        return output.getvalue().encode("utf-8")
    fieldnames = sorted({key for record in records for key in record})
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for record in records:
        writer.writerow(
            {
                key: json.dumps(value, ensure_ascii=False, sort_keys=True)
                if isinstance(value, (dict, list))
                else value
                for key, value in record.items()
            }
        )
    return output.getvalue().encode("utf-8")


def _content_hash(datasets: dict[str, list[dict[str, Any]]]) -> str:
    """SHA-256 over every dataset's canonical JSON, so two exports of the same
    underlying state hash identically and any change is detectable.

    Excludes audit_events: downloading an export is itself an audited action,
    so including the audit trail would make the hash change on every export
    even when nothing else in the record did."""
    hasher = hashlib.sha256()
    for name in sorted(datasets):
        if name == "audit_events":
            continue
        hasher.update(name.encode("utf-8"))
        hasher.update(_json_bytes(datasets[name]))
    return hasher.hexdigest()


def _sheet_title(name: str, used: set[str]) -> str:
    """Excel worksheet titles are capped at 31 characters and must be unique."""
    title = name[:31]
    suffix = 1
    while title in used:
        marker = f"_{suffix}"
        title = f"{name[: 31 - len(marker)]}{marker}"
        suffix += 1
    used.add(title)
    return title


def _xlsx_bytes(datasets: dict[str, list[dict[str, Any]]], *, sheet_names: Iterable[str]) -> bytes:
    workbook = Workbook()
    workbook.remove(workbook.active)
    used_titles: set[str] = set()
    for name in sheet_names:
        records = datasets.get(name, [])
        sheet = workbook.create_sheet(title=_sheet_title(name, used_titles))
        if not records:
            sheet.append(["No records"])
            continue
        fieldnames = sorted({key for record in records for key in record})
        sheet.append(fieldnames)
        for record in records:
            sheet.append(
                [
                    json.dumps(record.get(field), ensure_ascii=False, sort_keys=True)
                    if isinstance(record.get(field), (dict, list))
                    else record.get(field)
                    for field in fieldnames
                ]
            )
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


def _write_dataset(
    archive: zipfile.ZipFile,
    name: str,
    records: list[dict[str, Any]],
    *,
    csv_copy: bool = False,
) -> None:
    archive.writestr(f"json/{name}.json", _json_bytes(records))
    if csv_copy:
        archive.writestr(f"csv/{name}.csv", _csv_bytes(records))


def _write_source_attachment_files(
    archive: zipfile.ZipFile,
    attachments: Iterable[SourceAttachment],
) -> None:
    """Include customer-owned private files when storage can provide them."""
    for attachment in attachments:
        suffix = attachment.original_name.rsplit(".", 1)[-1] if "." in attachment.original_name else "bin"
        archive_name = (
            f"attachments/foresight/{attachment.source_id}/"
            f"{attachment.id}.{suffix.lower()}"
        )
        try:
            with attachment.file.open("rb") as source_file:
                archive.writestr(archive_name, source_file.read())
        except (FileNotFoundError, OSError):
            archive.writestr(
                f"attachments/foresight/{attachment.source_id}/{attachment.id}.unavailable.txt",
                (
                    f"The stored file {attachment.original_name!r} was unavailable when "
                    "this export was generated. Its metadata and SHA-256 remain in "
                    "json/foresight_source_attachments.json.\n"
                ).encode("utf-8"),
            )


def _organisation_datasets(organisation: Organisation) -> dict[str, list[dict[str, Any]]]:
    memberships = Membership.objects.filter(organisation=organisation).select_related("user")
    users = (
        User.objects.filter(organisation_memberships__organisation=organisation)
        .distinct()
        .order_by("email")
    )
    return {
        "users": _user_records(users),
        "memberships": _records(memberships),
        "membership_history": _records(MembershipEvent.objects.filter(organisation=organisation)),
        "organisation_deletion_requests": _records(OrganisationDeletionRequest.objects.filter(organisation=organisation)),
        "decision_methods": _records(DecisionMethod.objects.filter(organisation=organisation)),
        "decision_method_versions": _records(DecisionMethodVersion.objects.filter(organisation=organisation)),
        "decision_method_usage": _records(DecisionMethodUsage.objects.filter(organisation=organisation)),
        "workspaces": _records(Workspace.objects.filter(organisation=organisation)),
        "decisions": _records(Decision.objects.filter(organisation=organisation)),
        "decision_transitions": _records(
            DecisionTransition.objects.filter(organisation=organisation)
        ),
        "decision_finalisations": _records(
            DecisionFinalisation.objects.filter(organisation=organisation)
        ),
        "participants": _records(Participant.objects.filter(organisation=organisation)),
        "positions": _records(Position.objects.filter(organisation=organisation)),
        "options": _records(DecisionOption.objects.filter(organisation=organisation)),
        "evidence": _records(Evidence.objects.filter(organisation=organisation)),
        "assumptions": _records(Assumption.objects.filter(organisation=organisation)),
        "risks": _records(Risk.objects.filter(organisation=organisation)),
        "reviews": _records(DecisionReview.objects.filter(organisation=organisation)),
        "lessons": _records(Lesson.objects.filter(organisation=organisation)),
        "discussion_entries": _records(
            DiscussionEntry.objects.filter(organisation=organisation).prefetch_related(
                "mentioned_users"
            )
        ),
        "contribution_requests": _records(ContributionRequest.objects.filter(organisation=organisation)),
        "contribution_submissions": _records(ContributionSubmission.objects.filter(organisation=organisation)),
        "contribution_reviews": _records(ContributionReview.objects.filter(organisation=organisation)),
        "facilitation_sessions": _records(FacilitationSession.objects.filter(organisation=organisation)),
        "facilitation_participants": _records(SessionParticipant.objects.filter(organisation=organisation)),
        "contribution_preferences": _records(ContributionPreference.objects.filter(organisation=organisation)),
        "ai_reviews": _records(AIReview.objects.filter(organisation=organisation)),
        "invitations": _records(
            OrganisationInvitation.objects.filter(organisation=organisation)
        ),
        "decision_analysis_issues": _records(DecisionIssue.objects.filter(organisation=organisation)),
        "decision_quality_reviews": _records(DecisionQualityReview.objects.filter(organisation=organisation)),
        "executive_decision_summaries": _records(ExecutiveDecisionSummary.objects.filter(organisation=organisation)),
        "evaluation_exercises": _records(EvaluationExercise.objects.filter(organisation=organisation)),
        "evaluation_criteria": _records(EvaluationCriterion.objects.filter(organisation=organisation)),
        "evaluation_rounds": _records(EvaluationRound.objects.filter(organisation=organisation)),
        "evaluation_submissions": _records(EvaluationSubmission.objects.filter(organisation=organisation)),
        "evaluation_responses": _records(EvaluationResponse.objects.filter(organisation=organisation)),
        "evaluation_minority_reports": _records(MinorityReport.objects.filter(organisation=organisation)),
        "prioritisation_portfolios": _records(PrioritisationPortfolio.objects.filter(organisation=organisation)),
        "prioritisation_criteria": _records(PortfolioCriterion.objects.filter(organisation=organisation)),
        "prioritisation_candidates": _records(PortfolioCandidate.objects.filter(organisation=organisation)),
        "prioritisation_assessments": _records(PortfolioAssessment.objects.filter(organisation=organisation)),
        "prioritisation_selections": _records(PortfolioSelection.objects.filter(organisation=organisation)),
        "foresight_feeds": _records(FeedSubscription.objects.filter(organisation=organisation)),
        "foresight_sources": _records(Source.objects.filter(organisation=organisation)),
        "foresight_source_attachments": _records(SourceAttachment.objects.filter(source__organisation=organisation)),
        "foresight_signals": _records(Signal.objects.filter(organisation=organisation)),
        "foresight_signal_decision_links": _records(SignalDecisionLink.objects.filter(signal__organisation=organisation)),
        "foresight_watchlists": _records(Watchlist.objects.filter(organisation=organisation).prefetch_related("signals")),
        "foresight_watchlist_signals": _records(WatchlistSignal.objects.filter(watchlist__organisation=organisation)),
        "foresight_canvases": _records(ForesightCanvas.objects.filter(organisation=organisation)),
        "foresight_drivers": _records(Driver.objects.filter(canvas__organisation=organisation).prefetch_related("signals")),
        "foresight_driver_signals": _records(DriverSignal.objects.filter(driver__canvas__organisation=organisation)),
        "foresight_system_stakeholders": _records(SystemStakeholder.objects.filter(canvas__organisation=organisation)),
        "foresight_causal_relationships": _records(CausalRelationship.objects.filter(canvas__organisation=organisation)),
        "foresight_feedback_loops": _records(
            FeedbackLoop.objects.filter(canvas__organisation=organisation).prefetch_related(
                "drivers"
            )
        ),
        "foresight_feedback_loop_drivers": _records(
            FeedbackLoopDriver.objects.filter(
                feedback_loop__canvas__organisation=organisation
            )
        ),
        "foresight_consequences": _records(FuturesWheelConsequence.objects.filter(canvas__organisation=organisation)),
        "foresight_three_horizons": _records(ThreeHorizonItem.objects.filter(canvas__organisation=organisation)),
        "foresight_strategic_implications": _records(StrategicImplication.objects.filter(canvas__organisation=organisation).prefetch_related("drivers")),
        "foresight_scenario_sets": _records(ScenarioSet.objects.filter(canvas__organisation=organisation)),
        "foresight_scenarios": _records(Scenario.objects.filter(scenario_set__canvas__organisation=organisation)),
        "foresight_scenario_driver_states": _records(ScenarioDriverState.objects.filter(scenario__scenario_set__canvas__organisation=organisation)),
        "foresight_scenario_reviews": _records(ScenarioReview.objects.filter(scenario__scenario_set__canvas__organisation=organisation)),
        "foresight_wind_tunnel_assessments": _records(WindTunnelAssessment.objects.filter(scenario__scenario_set__canvas__organisation=organisation)),
        "foresight_signposts": _records(Signpost.objects.filter(scenario_set__canvas__organisation=organisation).prefetch_related("scenarios")),
        "foresight_scenario_signposts": _records(ScenarioSignpost.objects.filter(signpost__scenario_set__canvas__organisation=organisation)),
        "foresight_signpost_observations": _records(SignpostObservation.objects.filter(signpost__scenario_set__canvas__organisation=organisation)),
        "foresight_scenario_implications": _records(ScenarioImplicationLink.objects.filter(scenario__scenario_set__canvas__organisation=organisation)),
        "audit_events": _records(AuditEvent.objects.filter(organisation=organisation)),
    }


def build_organisation_export(*, organisation: Organisation) -> ExportArchive:
    """Build a complete, portable organisation archive."""

    generated_at = timezone.now()
    datasets = _organisation_datasets(organisation)
    content_hash = _content_hash(datasets)
    files: dict[str, bytes] = {
        "README.txt": (
            "The CrowdSmarter organisation export\n\n"
            "This archive belongs to the customer organisation named below. JSON files "
            "preserve complete structured records; CSV files and a single multi-sheet "
            "xlsx/export.xlsx workbook provide tabular copies for key registers. "
            "manifest.json's content_sha256 is a fingerprint of every dataset's JSON "
            "content, letting you confirm two exports were generated from identical "
            "underlying records. Passwords and invitation token digests are never exported.\n"
        ).encode("utf-8"),
        "manifest.json": _json_bytes(
            {
                "schema_version": EXPORT_SCHEMA_VERSION,
                "export_type": "organisation",
                "generated_at": generated_at.isoformat(),
                "content_sha256": content_hash,
                "organisation": {
                    "id": str(organisation.id),
                    "name": organisation.name,
                    "slug": organisation.slug,
                },
                "datasets": {name: len(records) for name, records in datasets.items()},
            }
        ),
        "organisation.json": _json_bytes(_serialise_instance(organisation)),
    }
    csv_names = {
        "users",
        "memberships",
        "workspaces",
        "decisions",
        "participants",
        "positions",
        "options",
        "evidence",
        "assumptions",
        "risks",
        "reviews",
        "lessons",
        "discussion_entries",
        "contribution_requests",
        "contribution_submissions",
        "contribution_reviews",
        "facilitation_sessions",
        "facilitation_participants",
        "contribution_preferences",
        "decision_method_version",
        "decision_method_usage",
        "decision_analysis_issues",
        "decision_quality_reviews",
        "executive_decision_summaries",
        "evaluation_exercises",
        "evaluation_criteria",
        "evaluation_rounds",
        "evaluation_submissions",
        "evaluation_responses",
        "evaluation_minority_reports",
        "prioritisation_portfolios",
        "prioritisation_criteria",
        "prioritisation_candidates",
        "prioritisation_assessments",
        "prioritisation_selections",
        "foresight_feeds",
        "foresight_sources",
        "foresight_signals",
        "foresight_watchlists",
        "foresight_canvases",
        "foresight_drivers",
        "foresight_system_stakeholders",
        "foresight_causal_relationships",
        "foresight_feedback_loops",
        "foresight_feedback_loop_drivers",
        "foresight_consequences",
        "foresight_three_horizons",
        "foresight_strategic_implications",
        "foresight_scenario_sets",
        "foresight_scenarios",
        "foresight_scenario_driver_states",
        "foresight_scenario_reviews",
        "foresight_wind_tunnel_assessments",
        "foresight_signposts",
        "foresight_signpost_observations",
        "foresight_scenario_implications",
        "audit_events",
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(files.items()):
            archive.writestr(name, content)
        for name, records in sorted(datasets.items()):
            _write_dataset(archive, name, records, csv_copy=name in csv_names)
        archive.writestr("xlsx/export.xlsx", _xlsx_bytes(datasets, sheet_names=sorted(csv_names)))
        _write_source_attachment_files(
            archive,
            SourceAttachment.objects.filter(source__organisation=organisation).select_related("source"),
        )
    timestamp = generated_at.strftime("%Y%m%dT%H%M%SZ")
    return ExportArchive(
        filename=f"crowdsmarter-{slugify(organisation.slug) or 'organisation'}-{timestamp}.zip",
        content=buffer.getvalue(),
    )


def _decision_datasets(decision: Decision) -> dict[str, list[dict[str, Any]]]:
    organisation_users = (
        User.objects.filter(organisation_memberships__organisation=decision.organisation)
        .distinct()
        .order_by("email")
    )
    linked_signal_ids = SignalDecisionLink.objects.filter(decision=decision).values_list("signal_id", flat=True)
    evidence_source_ids = Evidence.objects.filter(decision=decision, source_id__isnull=False).values_list("source_id", flat=True)
    signal_source_ids = Signal.objects.filter(id__in=linked_signal_ids, source_id__isnull=False).values_list("source_id", flat=True)
    related_source_ids = set(evidence_source_ids) | set(signal_source_ids)
    return {
        "users": _user_records(organisation_users),
        "organisation": [_serialise_instance(decision.organisation)],
        "workspace": [_serialise_instance(decision.workspace)],
        "decision_method_version": _records(
            DecisionMethodVersion.objects.filter(decisions=decision)
        ),
        "decision_method_usage": _records(DecisionMethodUsage.objects.filter(decision=decision)),
        "transitions": _records(DecisionTransition.objects.filter(decision=decision)),
        "finalisation": _records(DecisionFinalisation.objects.filter(decision=decision)),
        "participants": _records(Participant.objects.filter(decision=decision)),
        "positions": _records(Position.objects.filter(decision=decision)),
        "options": _records(DecisionOption.objects.filter(decision=decision)),
        "evidence": _records(Evidence.objects.filter(decision=decision)),
        "assumptions": _records(Assumption.objects.filter(decision=decision)),
        "risks": _records(Risk.objects.filter(decision=decision)),
        "review": _records(DecisionReview.objects.filter(decision=decision)),
        "lessons": _records(Lesson.objects.filter(decision=decision)),
        "discussion_entries": _records(
            DiscussionEntry.objects.filter(decision=decision).prefetch_related(
                "mentioned_users"
            )
        ),
        "contribution_requests": _records(ContributionRequest.objects.filter(decision=decision)),
        "contribution_submissions": _records(ContributionSubmission.objects.filter(decision=decision)),
        "contribution_reviews": _records(ContributionReview.objects.filter(decision=decision)),
        "facilitation_sessions": _records(FacilitationSession.objects.filter(decision=decision)),
        "facilitation_participants": _records(SessionParticipant.objects.filter(session__decision=decision)),
        "ai_reviews": _records(AIReview.objects.filter(decision=decision)),
        "decision_analysis_issues": _records(DecisionIssue.objects.filter(decision=decision)),
        "decision_quality_reviews": _records(DecisionQualityReview.objects.filter(decision=decision)),
        "executive_decision_summaries": _records(ExecutiveDecisionSummary.objects.filter(decision=decision)),
        "evaluation_exercises": _records(EvaluationExercise.objects.filter(decision=decision)),
        "evaluation_criteria": _records(EvaluationCriterion.objects.filter(exercise__decision=decision)),
        "evaluation_rounds": _records(EvaluationRound.objects.filter(exercise__decision=decision)),
        "evaluation_submissions": _records(EvaluationSubmission.objects.filter(round__exercise__decision=decision)),
        "evaluation_responses": _records(EvaluationResponse.objects.filter(submission__round__exercise__decision=decision)),
        "evaluation_minority_reports": _records(MinorityReport.objects.filter(exercise__decision=decision)),
        "prioritisation_candidates": _records(PortfolioCandidate.objects.filter(decision=decision)),
        "prioritisation_assessments": _records(PortfolioAssessment.objects.filter(candidate__decision=decision)),
        "prioritisation_selections": _records(PortfolioSelection.objects.filter(candidate__decision=decision)),
        "linked_signals": _records(Signal.objects.filter(id__in=linked_signal_ids)),
        "signal_decision_links": _records(SignalDecisionLink.objects.filter(decision=decision)),
        "foresight_sources": _records(Source.objects.filter(id__in=related_source_ids)),
        "foresight_source_attachments": _records(SourceAttachment.objects.filter(source_id__in=related_source_ids)),
        "foresight_strategic_implications": _records(StrategicImplication.objects.filter(linked_decision=decision).prefetch_related("drivers")),
        "foresight_scenario_sets": _records(ScenarioSet.objects.filter(linked_decision=decision)),
        "foresight_scenarios": _records(Scenario.objects.filter(scenario_set__linked_decision=decision)),
        "foresight_scenario_driver_states": _records(
            ScenarioDriverState.objects.filter(scenario__scenario_set__linked_decision=decision)
        ),
        "foresight_scenario_reviews": _records(
            ScenarioReview.objects.filter(scenario__scenario_set__linked_decision=decision)
        ),
        "foresight_wind_tunnel_assessments": _records(
            WindTunnelAssessment.objects.filter(option__decision=decision)
        ),
        "foresight_signposts": _records(
            Signpost.objects.filter(scenario_set__linked_decision=decision).prefetch_related(
                "scenarios"
            )
        ),
        "foresight_scenario_signposts": _records(
            ScenarioSignpost.objects.filter(signpost__scenario_set__linked_decision=decision)
        ),
        "foresight_signpost_observations": _records(
            SignpostObservation.objects.filter(
                signpost__scenario_set__linked_decision=decision
            )
        ),
        "foresight_scenario_implications": _records(
            ScenarioImplicationLink.objects.filter(
                scenario__scenario_set__linked_decision=decision
            )
        ),
    }


def _decision_summary_text(
    decision: Decision,
    datasets: dict[str, list[dict[str, Any]]],
) -> str:
    owner_name = (
        " ".join(filter(None, [decision.owner.first_name, decision.owner.last_name]))
        or decision.owner.email
    )
    lines = [
        "THE CROWDSMARTER DECISION DOSSIER",
        "",
        f"Title: {decision.title}",
        f"Question: {decision.decision_question}",
        f"Status: {decision.get_status_display()}",
        f"Urgency: {decision.get_urgency_display()}",
        f"Organisation: {decision.organisation.name}",
        f"Workspace: {decision.workspace.name}",
        f"Decision owner: {owner_name}",
        f"Target decision date: {decision.target_decision_date or 'Not set'}",
        "",
        "Purpose",
        decision.purpose or "Not recorded.",
        "",
        "Context",
        decision.context or "Not recorded.",
        "",
        "Scope",
        decision.scope or "Not recorded.",
        "",
        "Record counts",
    ]
    lines.extend(f"- {name.replace('_', ' ').title()}: {len(records)}" for name, records in sorted(datasets.items()))
    return "\n".join(lines) + "\n"


def build_decision_export(*, decision: Decision) -> ExportArchive:
    """Build a human-readable and machine-readable decision dossier."""

    generated_at = timezone.now()
    datasets = _decision_datasets(decision)
    content_hash = _content_hash(datasets)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("README.txt", (
            "The CrowdSmarter decision dossier\n\n"
            "summary.txt provides a readable overview. JSON preserves complete structured "
            "records; CSV and a single multi-sheet xlsx/export.xlsx workbook provide "
            "tabular registers suitable for spreadsheet review. manifest.json's "
            "content_sha256 is a fingerprint of every dataset's JSON content, letting you "
            "confirm two exports were generated from identical underlying records.\n"
        ).encode("utf-8"))
        archive.writestr("summary.txt", _decision_summary_text(decision, datasets).encode("utf-8"))
        archive.writestr("manifest.json", _json_bytes({
            "schema_version": EXPORT_SCHEMA_VERSION,
            "export_type": "decision",
            "generated_at": generated_at.isoformat(),
            "content_sha256": content_hash,
            "decision": {"id": str(decision.id), "title": decision.title, "status": decision.status},
            "datasets": {name: len(records) for name, records in datasets.items()},
        }))
        archive.writestr("json/decision.json", _json_bytes(_serialise_instance(decision)))
        for name, records in sorted(datasets.items()):
            _write_dataset(archive, name, records, csv_copy=True)
        archive.writestr("xlsx/export.xlsx", _xlsx_bytes(datasets, sheet_names=sorted(datasets)))
        related_source_ids = [record["id"] for record in datasets.get("foresight_sources", [])]
        _write_source_attachment_files(
            archive,
            SourceAttachment.objects.filter(source_id__in=related_source_ids).select_related("source"),
        )
    timestamp = generated_at.strftime("%Y%m%dT%H%M%SZ")
    title_slug = slugify(decision.title)[:60] or "decision"
    return ExportArchive(
        filename=f"crowdsmarter-decision-{title_slug}-{timestamp}.zip",
        content=buffer.getvalue(),
    )
