"""Transactional scenario-planning, wind-tunnelling, and signpost workflows."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction

from apps.accounts.models import User
from apps.assumptions.models import Assumption
from apps.audit.services import record_event
from apps.decision_options.models import DecisionOption
from apps.decisions.models import Decision
from apps.organisations.models import Membership
from apps.risks.models import Risk

from .models import (
    Driver,
    ForesightCanvas,
    Scenario,
    ScenarioDriverState,
    ScenarioImplicationLink,
    ScenarioReview,
    ScenarioSet,
    ScenarioSignpost,
    Signpost,
    SignpostAssumptionLink,
    SignpostObservation,
    SignpostRiskLink,
    Source,
    StrategicImplication,
    WindTunnelAssessment,
)
from .policies import can_contribute, can_manage_record


class ScenarioServiceError(ValidationError):
    """Expected scenario-planning workflow failure."""


def _active_member(*, organisation, user_id: Any) -> User:  # type: ignore[no-untyped-def]
    try:
        return (
            Membership.objects.select_related("user")
            .get(
                organisation=organisation,
                user_id=user_id,
                status=Membership.Status.ACTIVE,
            )
            .user
        )
    except Membership.DoesNotExist as exc:
        raise ScenarioServiceError({"owner_id": "Choose an active organisation member."}) from exc


def _require_canvas_contributor(*, actor: User, canvas: ForesightCanvas) -> None:
    if canvas.status == ForesightCanvas.Status.ARCHIVED:
        raise ScenarioServiceError("Archived foresight canvases are read-only.")
    if not can_contribute(actor=actor, organisation=canvas.organisation):
        raise PermissionDenied("You cannot contribute to this foresight canvas.")


def _require_scenario_set_contributor(*, actor: User, scenario_set: ScenarioSet) -> None:
    _require_canvas_contributor(actor=actor, canvas=scenario_set.canvas)
    if scenario_set.status == ScenarioSet.Status.ARCHIVED:
        raise ScenarioServiceError("Archived scenario sets are read-only.")


def _driver_for_axis(*, canvas: ForesightCanvas, driver_id: Any, field_name: str) -> Driver:
    try:
        driver = Driver.objects.get(id=driver_id, canvas=canvas, is_active=True)
    except Driver.DoesNotExist as exc:
        raise ScenarioServiceError(
            {field_name: "Choose an active driver from this canvas."}
        ) from exc
    if driver.driver_type != Driver.DriverType.CRITICAL_UNCERTAINTY:
        raise ScenarioServiceError({field_name: "Scenario axes must be critical uncertainties."})
    return driver


@transaction.atomic
def create_scenario_set(*, actor: User, canvas: ForesightCanvas, **fields: Any) -> ScenarioSet:
    _require_canvas_contributor(actor=actor, canvas=canvas)
    axis_x_driver = _driver_for_axis(
        canvas=canvas,
        driver_id=fields.pop("axis_x_driver_id"),
        field_name="axis_x_driver_id",
    )
    axis_y_driver = _driver_for_axis(
        canvas=canvas,
        driver_id=fields.pop("axis_y_driver_id"),
        field_name="axis_y_driver_id",
    )
    if axis_x_driver.id == axis_y_driver.id:
        raise ScenarioServiceError(
            {"axis_y_driver_id": "Choose two different critical uncertainties."}
        )
    owner_id = fields.pop("owner_id", actor.id)
    linked_decision_id = fields.pop("linked_decision_id", None)
    linked_decision = None
    if linked_decision_id:
        try:
            linked_decision = Decision.objects.get(
                id=linked_decision_id, organisation=canvas.organisation
            )
        except Decision.DoesNotExist as exc:
            raise ScenarioServiceError(
                {"linked_decision_id": "Choose a decision from this organisation."}
            ) from exc
    item = ScenarioSet(
        canvas=canvas,
        axis_x_driver=axis_x_driver,
        axis_y_driver=axis_y_driver,
        linked_decision=linked_decision,
        owner=_active_member(organisation=canvas.organisation, user_id=owner_id),
        created_by=actor,
        **fields,
    )
    try:
        item.full_clean(validate_unique=False, validate_constraints=False)
        item.save()
    except IntegrityError as exc:
        raise ScenarioServiceError(
            {"title": "A scenario set with this title already exists."}
        ) from exc
    record_event(
        action="foresight.scenario_set.created",
        object_type="foresight_scenario_set",
        object_id=str(item.id),
        actor=actor,
        organisation=canvas.organisation,
        metadata={
            "canvas_id": str(canvas.id),
            "axis_x_driver_id": str(axis_x_driver.id),
            "axis_y_driver_id": str(axis_y_driver.id),
            "linked_decision_id": str(linked_decision_id or ""),
        },
    )
    return item


@transaction.atomic
def update_scenario_set(
    *, actor: User, scenario_set: ScenarioSet, fields: dict[str, Any]
) -> ScenarioSet:
    item = (
        ScenarioSet.objects.select_for_update()
        .select_related("canvas__organisation", "axis_x_driver", "axis_y_driver")
        .get(id=scenario_set.id)
    )
    if not can_manage_record(
        actor=actor,
        organisation=item.canvas.organisation,
        created_by_id=item.created_by_id,
        owner_id=item.owner_id,
    ):
        raise PermissionDenied("You cannot edit this scenario set.")
    _require_scenario_set_contributor(actor=actor, scenario_set=item)
    owner_id = fields.pop("owner_id", None)
    if owner_id is not None:
        item.owner = _active_member(organisation=item.canvas.organisation, user_id=owner_id)
    marker = object()
    linked_decision_id = fields.pop("linked_decision_id", marker)
    if linked_decision_id is not marker:
        requested_decision_id = str(linked_decision_id or "")
        current_decision_id = str(item.linked_decision_id or "")
        if (
            requested_decision_id != current_decision_id
            and item.scenarios.filter(wind_tunnel_assessments__isnull=False).exists()
        ):
            raise ScenarioServiceError(
                {
                    "linked_decision_id": (
                        "The linked decision cannot change after wind-tunnel "
                        "assessments have been recorded."
                    )
                }
            )
        if linked_decision_id:
            try:
                item.linked_decision = Decision.objects.get(
                    id=linked_decision_id, organisation=item.canvas.organisation
                )
            except Decision.DoesNotExist as exc:
                raise ScenarioServiceError(
                    {"linked_decision_id": "Choose a decision from this organisation."}
                ) from exc
        else:
            item.linked_decision = None
    before = {key: getattr(item, key) for key in fields}
    for key, value in fields.items():
        setattr(item, key, value)
    item.full_clean(validate_unique=False, validate_constraints=False)
    item.save()
    record_event(
        action="foresight.scenario_set.updated",
        object_type="foresight_scenario_set",
        object_id=str(item.id),
        actor=actor,
        organisation=item.canvas.organisation,
        metadata={"before": before, "status": item.status},
    )
    return item


@transaction.atomic
def create_scenario(*, actor: User, scenario_set: ScenarioSet, **fields: Any) -> Scenario:
    _require_scenario_set_contributor(actor=actor, scenario_set=scenario_set)
    item = Scenario(scenario_set=scenario_set, created_by=actor, **fields)
    try:
        item.full_clean(validate_unique=False, validate_constraints=False)
        item.save()
    except IntegrityError as exc:
        raise ScenarioServiceError(
            "Each scenario set supports one world per quadrant and unique titles and codes."
        ) from exc
    record_event(
        action="foresight.scenario.created",
        object_type="foresight_scenario",
        object_id=str(item.id),
        actor=actor,
        organisation=scenario_set.canvas.organisation,
        metadata={
            "scenario_set_id": str(scenario_set.id),
            "quadrant": [item.axis_x_position, item.axis_y_position],
        },
    )
    return item


@transaction.atomic
def update_scenario(*, actor: User, scenario: Scenario, fields: dict[str, Any]) -> Scenario:
    item = (
        Scenario.objects.select_for_update()
        .select_related("scenario_set__canvas__organisation")
        .get(id=scenario.id)
    )
    if not can_manage_record(
        actor=actor,
        organisation=item.scenario_set.canvas.organisation,
        created_by_id=item.created_by_id,
        owner_id=item.scenario_set.owner_id,
    ):
        raise PermissionDenied("You cannot edit this scenario.")
    _require_scenario_set_contributor(actor=actor, scenario_set=item.scenario_set)
    for key, value in fields.items():
        setattr(item, key, value)
    item.full_clean(validate_unique=False, validate_constraints=False)
    try:
        item.save()
    except IntegrityError as exc:
        raise ScenarioServiceError(
            "The scenario title, code, and quadrant must be unique."
        ) from exc
    record_event(
        action="foresight.scenario.updated",
        object_type="foresight_scenario",
        object_id=str(item.id),
        actor=actor,
        organisation=item.scenario_set.canvas.organisation,
        metadata={"status": item.status},
    )
    return item


@transaction.atomic
def set_scenario_driver_state(
    *, actor: User, scenario: Scenario, driver_id: Any, **fields: Any
) -> ScenarioDriverState:
    _require_scenario_set_contributor(actor=actor, scenario_set=scenario.scenario_set)
    try:
        driver = Driver.objects.get(id=driver_id, canvas=scenario.scenario_set.canvas)
    except Driver.DoesNotExist as exc:
        raise ScenarioServiceError(
            {"driver_id": "Choose a driver from the scenario canvas."}
        ) from exc
    item, created = ScenarioDriverState.objects.update_or_create(
        scenario=scenario,
        driver=driver,
        defaults={"created_by": actor, **fields},
    )
    item.full_clean(validate_unique=False, validate_constraints=False)
    item.save()
    record_event(
        action=(
            "foresight.scenario_driver_state.created"
            if created
            else "foresight.scenario_driver_state.updated"
        ),
        object_type="foresight_scenario_driver_state",
        object_id=str(item.id),
        actor=actor,
        organisation=scenario.scenario_set.canvas.organisation,
        metadata={"scenario_id": str(scenario.id), "driver_id": str(driver.id)},
    )
    return item


@transaction.atomic
def submit_scenario_review(*, actor: User, scenario: Scenario, **fields: Any) -> ScenarioReview:
    _require_scenario_set_contributor(actor=actor, scenario_set=scenario.scenario_set)
    item, created = ScenarioReview.objects.update_or_create(
        scenario=scenario,
        reviewer=actor,
        defaults=fields,
    )
    item.full_clean(validate_unique=False, validate_constraints=False)
    item.save()
    record_event(
        action=(
            "foresight.scenario_review.created" if created else "foresight.scenario_review.updated"
        ),
        object_type="foresight_scenario_review",
        object_id=str(item.id),
        actor=actor,
        organisation=scenario.scenario_set.canvas.organisation,
        metadata={"scenario_id": str(scenario.id), "confidence": item.confidence},
    )
    return item


@transaction.atomic
def assess_option(
    *, actor: User, scenario: Scenario, option_id: Any, **fields: Any
) -> WindTunnelAssessment:
    _require_scenario_set_contributor(actor=actor, scenario_set=scenario.scenario_set)
    if not scenario.scenario_set.linked_decision_id:
        raise ScenarioServiceError({"option_id": "Link the scenario set to a decision first."})
    try:
        option = DecisionOption.objects.get(
            id=option_id,
            decision_id=scenario.scenario_set.linked_decision_id,
            organisation=scenario.scenario_set.canvas.organisation,
            status=DecisionOption.Status.ACTIVE,
        )
    except DecisionOption.DoesNotExist as exc:
        raise ScenarioServiceError(
            {"option_id": "Choose an option from the linked decision."}
        ) from exc
    item, created = WindTunnelAssessment.objects.update_or_create(
        scenario=scenario,
        option=option,
        defaults={"assessed_by": actor, **fields},
    )
    item.full_clean(validate_unique=False, validate_constraints=False)
    item.save()
    record_event(
        action=(
            "foresight.wind_tunnel_assessment.created"
            if created
            else "foresight.wind_tunnel_assessment.updated"
        ),
        object_type="foresight_wind_tunnel_assessment",
        object_id=str(item.id),
        actor=actor,
        organisation=scenario.scenario_set.canvas.organisation,
        metadata={
            "scenario_id": str(scenario.id),
            "option_id": str(option.id),
            "verdict": item.verdict,
        },
    )
    return item


@transaction.atomic
def create_signpost(
    *, actor: User, scenario_set: ScenarioSet, scenario_links: list[dict[str, Any]], **fields: Any
) -> Signpost:
    _require_scenario_set_contributor(actor=actor, scenario_set=scenario_set)
    owner_id = fields.pop("owner_id", actor.id)
    item = Signpost(
        scenario_set=scenario_set,
        owner=_active_member(organisation=scenario_set.canvas.organisation, user_id=owner_id),
        created_by=actor,
        **fields,
    )
    try:
        item.full_clean(validate_unique=False, validate_constraints=False)
        item.save()
    except IntegrityError as exc:
        raise ScenarioServiceError({"title": "A signpost with this title already exists."}) from exc
    scenario_ids = [link["scenario_id"] for link in scenario_links]
    scenarios = {
        str(scenario.id): scenario
        for scenario in Scenario.objects.filter(scenario_set=scenario_set, id__in=scenario_ids)
    }
    if len(scenarios) != len(set(map(str, scenario_ids))):
        raise ScenarioServiceError(
            {"scenario_links": "Every linked scenario must belong to this scenario set."}
        )
    for link in scenario_links:
        scenario = scenarios[str(link["scenario_id"])]
        relation = ScenarioSignpost(
            signpost=item,
            scenario=scenario,
            relationship=link["relationship"],
            rationale=link["rationale"],
            linked_by=actor,
        )
        relation.full_clean(validate_unique=False, validate_constraints=False)
        relation.save()
    record_event(
        action="foresight.signpost.created",
        object_type="foresight_signpost",
        object_id=str(item.id),
        actor=actor,
        organisation=scenario_set.canvas.organisation,
        metadata={
            "scenario_set_id": str(scenario_set.id),
            "scenario_ids": [str(value) for value in scenario_ids],
        },
    )
    return item


@transaction.atomic
def create_signpost_observation(
    *, actor: User, signpost: Signpost, source_id: Any = None, **fields: Any
) -> SignpostObservation:
    _require_scenario_set_contributor(actor=actor, scenario_set=signpost.scenario_set)
    source = None
    if source_id:
        try:
            source = Source.objects.get(
                id=source_id,
                organisation=signpost.scenario_set.canvas.organisation,
            )
        except Source.DoesNotExist as exc:
            raise ScenarioServiceError(
                {"source_id": "Choose a source from this organisation."}
            ) from exc
    item = SignpostObservation(
        signpost=signpost,
        source=source,
        created_by=actor,
        **fields,
    )
    item.full_clean(validate_unique=False, validate_constraints=False)
    item.save()
    record_event(
        action="foresight.signpost_observation.created",
        object_type="foresight_signpost_observation",
        object_id=str(item.id),
        actor=actor,
        organisation=signpost.scenario_set.canvas.organisation,
        metadata={
            "signpost_id": str(signpost.id),
            "assessment": item.assessment,
            "observed_on": item.observed_on,
        },
    )
    return item


@transaction.atomic
def link_signpost_to_assumption(
    *, actor: User, signpost: Signpost, assumption_id: Any, rationale: str
) -> SignpostAssumptionLink:
    _require_scenario_set_contributor(actor=actor, scenario_set=signpost.scenario_set)
    organisation = signpost.scenario_set.canvas.organisation
    try:
        assumption = Assumption.objects.get(id=assumption_id, organisation=organisation)
    except Assumption.DoesNotExist as exc:
        raise ScenarioServiceError(
            {"assumption_id": "The assumption does not belong to this organisation."}
        ) from exc
    link, created = SignpostAssumptionLink.objects.update_or_create(
        signpost=signpost,
        assumption=assumption,
        defaults={"rationale": rationale, "linked_by": actor},
    )
    link.full_clean(validate_unique=False, validate_constraints=False)
    record_event(
        action="foresight.signpost.linked_to_assumption"
        if created
        else "foresight.signpost_assumption_link.updated",
        object_type="foresight_signpost_assumption_link",
        object_id=str(link.id),
        actor=actor,
        organisation=organisation,
        metadata={"signpost_id": str(signpost.id), "assumption_id": str(assumption.id)},
    )
    return link


@transaction.atomic
def link_signpost_to_risk(
    *, actor: User, signpost: Signpost, risk_id: Any, rationale: str
) -> SignpostRiskLink:
    _require_scenario_set_contributor(actor=actor, scenario_set=signpost.scenario_set)
    organisation = signpost.scenario_set.canvas.organisation
    try:
        risk = Risk.objects.get(id=risk_id, organisation=organisation)
    except Risk.DoesNotExist as exc:
        raise ScenarioServiceError(
            {"risk_id": "The risk does not belong to this organisation."}
        ) from exc
    link, created = SignpostRiskLink.objects.update_or_create(
        signpost=signpost,
        risk=risk,
        defaults={"rationale": rationale, "linked_by": actor},
    )
    link.full_clean(validate_unique=False, validate_constraints=False)
    record_event(
        action="foresight.signpost.linked_to_risk"
        if created
        else "foresight.signpost_risk_link.updated",
        object_type="foresight_signpost_risk_link",
        object_id=str(link.id),
        actor=actor,
        organisation=organisation,
        metadata={"signpost_id": str(signpost.id), "risk_id": str(risk.id)},
    )
    return link


@transaction.atomic
def link_scenario_implication(
    *, actor: User, scenario: Scenario, implication_id: Any, **fields: Any
) -> ScenarioImplicationLink:
    _require_scenario_set_contributor(actor=actor, scenario_set=scenario.scenario_set)
    try:
        implication = StrategicImplication.objects.get(
            id=implication_id, canvas=scenario.scenario_set.canvas
        )
    except StrategicImplication.DoesNotExist as exc:
        raise ScenarioServiceError(
            {"implication_id": "Choose an implication from the scenario canvas."}
        ) from exc
    item, created = ScenarioImplicationLink.objects.update_or_create(
        scenario=scenario,
        implication=implication,
        defaults={"linked_by": actor, **fields},
    )
    item.full_clean(validate_unique=False, validate_constraints=False)
    item.save()
    record_event(
        action=(
            "foresight.scenario_implication.created"
            if created
            else "foresight.scenario_implication.updated"
        ),
        object_type="foresight_scenario_implication",
        object_id=str(item.id),
        actor=actor,
        organisation=scenario.scenario_set.canvas.organisation,
        metadata={
            "scenario_id": str(scenario.id),
            "implication_id": str(implication.id),
            "effect": item.effect,
        },
    )
    return item
