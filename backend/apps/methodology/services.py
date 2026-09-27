"""Transactional organisation-method governance workflows."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.audit.services import record_event
from apps.decisions.templates import template_for_key
from apps.organisations.models import Organisation

from .models import DecisionMethod, DecisionMethodVersion
from .policies import can_approve_methods, can_manage_methods


class MethodologyServiceError(ValidationError):
    """Expected validation failure in method governance."""


def _require_active(organisation: Organisation) -> None:
    if organisation.status != Organisation.Status.ACTIVE:
        raise MethodologyServiceError("Reactivate the organisation before changing its methods.")


def _require_manager(*, actor, organisation):  # type: ignore[no-untyped-def]
    if not can_manage_methods(actor=actor, organisation=organisation):
        raise PermissionDenied("This action requires an owner or administrator role.")
    _require_active(organisation)


def _require_owner(*, actor, organisation):  # type: ignore[no-untyped-def]
    if not can_approve_methods(actor=actor, organisation=organisation):
        raise PermissionDenied("Only an organisation owner may approve or retire a method.")
    _require_active(organisation)


def _next_key(*, organisation: Organisation, name: str) -> str:
    base = slugify(name)[:70] or "decision-method"
    key = base
    number = 2
    while DecisionMethod.objects.filter(organisation=organisation, key=key).exists():
        suffix = f"-{number}"
        key = f"{base[: 80 - len(suffix)]}{suffix}"
        number += 1
    return key


def _version_payload(values: dict) -> dict:
    return {
        "question_prompt": values["question_prompt"],
        "purpose_prompt": values["purpose_prompt"],
        "context_prompt": values["context_prompt"],
        "scope_prompt": values["scope_prompt"],
        "contribution_prompt": values["contribution_prompt"],
        "suggested_urgency": values.get("suggested_urgency", "normal"),
        "required_fields": values.get("required_fields", []),
        "checklist": values.get("checklist", []),
        "evidence_prompts": values.get("evidence_prompts", []),
        "assumption_prompts": values.get("assumption_prompts", []),
        "risk_prompts": values.get("risk_prompts", []),
        "stakeholder_prompts": values.get("stakeholder_prompts", []),
        "lifecycle_expectations": values.get("lifecycle_expectations", []),
        "cloned_from_builtin_key": values.get("cloned_from_builtin_key", ""),
    }


@transaction.atomic
def create_method(
    *, actor, organisation: Organisation, name: str, summary: str, best_for: str = "", **values
):  # type: ignore[no-untyped-def]
    _require_manager(actor=actor, organisation=organisation)
    method = DecisionMethod(
        organisation=organisation,
        key=_next_key(organisation=organisation, name=name),
        name=name,
        summary=summary,
        best_for=best_for,
        created_by=actor,
    )
    method.full_clean(validate_unique=False, validate_constraints=False)
    try:
        method.save()
    except IntegrityError as exc:
        raise MethodologyServiceError("The method could not be created safely.") from exc
    version = DecisionMethodVersion(
        method=method,
        organisation=organisation,
        version=1,
        created_by=actor,
        **_version_payload(values),
    )
    version.full_clean(validate_unique=False, validate_constraints=False)
    version.save()
    record_event(
        action="methodology.method_created",
        object_type="decision_method",
        object_id=str(method.id),
        actor=actor,
        organisation=organisation,
        metadata={"name": method.name, "version": 1},
    )
    return method


@transaction.atomic
def clone_builtin_method(*, actor, organisation: Organisation, builtin_key: str, name: str = ""):  # type: ignore[no-untyped-def]
    template = template_for_key(builtin_key)
    if template is None:
        raise MethodologyServiceError({"builtin_key": "Choose a recognised built-in template."})
    return create_method(
        actor=actor,
        organisation=organisation,
        name=name.strip() or f"{template.name} - organisation method",
        summary=template.summary,
        best_for=template.best_for,
        question_prompt=template.question_prompt,
        purpose_prompt=template.purpose_prompt,
        context_prompt=template.context_prompt,
        scope_prompt=template.scope_prompt,
        contribution_prompt=template.contribution_prompt,
        suggested_urgency=template.suggested_urgency,
        checklist=list(template.checklist),
        cloned_from_builtin_key=template.key,
        required_fields=[
            "decision_question",
            "purpose",
            "context",
            "scope",
            "contribution_guidance",
        ],
    )


@transaction.atomic
def update_draft_version(*, actor, version: DecisionMethodVersion, changes: dict):  # type: ignore[no-untyped-def]
    version = (
        DecisionMethodVersion.objects.select_for_update()
        .select_related("organisation", "method")
        .get(id=version.id)
    )
    _require_manager(actor=actor, organisation=version.organisation)
    if version.status != DecisionMethodVersion.Status.DRAFT:
        raise MethodologyServiceError("Approved or retired versions are immutable.")
    for field, value in changes.items():
        setattr(version, field, value)
    version.full_clean(exclude=["approved_by"], validate_unique=False, validate_constraints=False)
    version.save(update_fields=[*changes.keys(), "updated_at"])
    record_event(
        action="methodology.version_updated",
        object_type="decision_method_version",
        object_id=str(version.id),
        actor=actor,
        organisation=version.organisation,
        metadata={"method_id": str(version.method_id), "version": version.version},
    )
    return version


@transaction.atomic
def create_method_version(*, actor, method: DecisionMethod):  # type: ignore[no-untyped-def]
    method = (
        DecisionMethod.objects.select_for_update()
        .select_related("organisation", "current_version")
        .get(id=method.id)
    )
    _require_manager(actor=actor, organisation=method.organisation)
    if method.status == DecisionMethod.Status.RETIRED:
        raise MethodologyServiceError("Retired methods cannot receive new versions.")
    if method.versions.filter(status=DecisionMethodVersion.Status.DRAFT).exists():
        raise MethodologyServiceError("Complete or discard the existing draft version first.")
    source = method.current_version or method.versions.order_by("-version").first()
    if source is None:
        raise MethodologyServiceError("The method has no version to copy.")
    values = {
        field: getattr(source, field)
        for field in (
            "question_prompt",
            "purpose_prompt",
            "context_prompt",
            "scope_prompt",
            "contribution_prompt",
            "suggested_urgency",
            "required_fields",
            "checklist",
            "evidence_prompts",
            "assumption_prompts",
            "risk_prompts",
            "stakeholder_prompts",
            "lifecycle_expectations",
            "cloned_from_builtin_key",
        )
    }
    version = DecisionMethodVersion(
        method=method,
        organisation=method.organisation,
        version=source.version + 1,
        created_by=actor,
        **values,
    )
    version.full_clean(validate_unique=False, validate_constraints=False)
    version.save()
    record_event(
        action="methodology.version_created",
        object_type="decision_method_version",
        object_id=str(version.id),
        actor=actor,
        organisation=method.organisation,
        metadata={"method_id": str(method.id), "version": version.version},
    )
    return version


@transaction.atomic
def approve_method_version(*, actor, version: DecisionMethodVersion):  # type: ignore[no-untyped-def]
    version = (
        DecisionMethodVersion.objects.select_for_update()
        .select_related("organisation", "method")
        .get(id=version.id)
    )
    _require_owner(actor=actor, organisation=version.organisation)
    if version.status != DecisionMethodVersion.Status.DRAFT:
        raise MethodologyServiceError("Only a draft version can be approved.")
    now = timezone.now()
    previous = version.method.current_version
    if previous:
        DecisionMethodVersion.objects.filter(id=previous.id).update(
            status=DecisionMethodVersion.Status.RETIRED, updated_at=now
        )
    version.status = DecisionMethodVersion.Status.APPROVED
    version.approved_by = actor
    version.approved_at = now
    version.full_clean(validate_unique=False, validate_constraints=False)
    version.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
    method = DecisionMethod.objects.select_for_update().get(id=version.method_id)
    method.status = DecisionMethod.Status.APPROVED
    method.current_version = version
    method.retired_at = None
    method.save(update_fields=["status", "current_version", "retired_at", "updated_at"])
    record_event(
        action="methodology.version_approved",
        object_type="decision_method_version",
        object_id=str(version.id),
        actor=actor,
        organisation=version.organisation,
        metadata={"method_id": str(method.id), "version": version.version},
    )
    return version


@transaction.atomic
def retire_method(*, actor, method: DecisionMethod, reason: str):  # type: ignore[no-untyped-def]
    method = (
        DecisionMethod.objects.select_for_update().select_related("organisation").get(id=method.id)
    )
    _require_owner(actor=actor, organisation=method.organisation)
    reason = reason.strip()
    if not reason:
        raise MethodologyServiceError({"reason": "Record why the method is being retired."})
    method.status = DecisionMethod.Status.RETIRED
    method.retired_at = timezone.now()
    method.save(update_fields=["status", "retired_at", "updated_at"])
    if method.current_version_id:
        DecisionMethodVersion.objects.filter(
            id=method.current_version_id, status=DecisionMethodVersion.Status.APPROVED
        ).update(status=DecisionMethodVersion.Status.RETIRED, updated_at=method.retired_at)
    record_event(
        action="methodology.method_retired",
        object_type="decision_method",
        object_id=str(method.id),
        actor=actor,
        organisation=method.organisation,
        metadata={"reason": reason},
    )
    return method
