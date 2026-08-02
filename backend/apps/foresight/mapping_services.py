"""Transactional workflows for foresight canvases and systems mapping."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction

from apps.accounts.models import User
from apps.audit.services import record_event
from apps.decisions.models import Decision
from apps.organisations.models import Membership, Organisation

from .models import (
    CausalRelationship,
    Driver,
    DriverSignal,
    FeedbackLoop,
    FeedbackLoopDriver,
    ForesightCanvas,
    FuturesWheelConsequence,
    Signal,
    StrategicImplication,
    SystemStakeholder,
    ThreeHorizonItem,
)
from .policies import can_contribute, can_manage_record


class MappingServiceError(ValidationError):
    """Expected systems-mapping workflow failure."""


def _active_member(*, organisation: Organisation, user_id: Any) -> User:
    try:
        return Membership.objects.select_related("user").get(
            organisation=organisation,
            user_id=user_id,
            status=Membership.Status.ACTIVE,
        ).user
    except Membership.DoesNotExist as exc:
        raise MappingServiceError({"owner_id": "Choose an active organisation member."}) from exc


def _can_edit_canvas(*, actor: User, canvas: ForesightCanvas) -> bool:
    return can_manage_record(
        actor=actor,
        organisation=canvas.organisation,
        created_by_id=canvas.created_by_id,
        owner_id=canvas.owner_id,
    )


def _require_contributor(*, actor: User, canvas: ForesightCanvas) -> None:
    if canvas.status == ForesightCanvas.Status.ARCHIVED:
        raise MappingServiceError("Archived foresight canvases are read-only.")
    if not can_contribute(actor=actor, organisation=canvas.organisation):
        raise PermissionDenied("You cannot contribute to this foresight canvas.")


@transaction.atomic
def create_canvas(*, actor: User, organisation: Organisation, **fields: Any) -> ForesightCanvas:
    if not can_contribute(actor=actor, organisation=organisation):
        raise PermissionDenied("You cannot create a foresight canvas in this organisation.")
    owner_id = fields.pop("owner_id", actor.id)
    canvas = ForesightCanvas(
        organisation=organisation,
        owner=_active_member(organisation=organisation, user_id=owner_id),
        created_by=actor,
        **fields,
    )
    canvas.full_clean(validate_unique=False, validate_constraints=False)
    canvas.save()
    record_event(
        action="foresight.canvas.created",
        object_type="foresight_canvas",
        object_id=str(canvas.id),
        actor=actor,
        organisation=organisation,
        metadata={"title": canvas.title, "horizon_year": canvas.horizon_year},
    )
    return canvas


@transaction.atomic
def update_canvas(*, actor: User, canvas: ForesightCanvas, fields: dict[str, Any]) -> ForesightCanvas:
    canvas = ForesightCanvas.objects.select_for_update().select_related("organisation").get(id=canvas.id)
    if not _can_edit_canvas(actor=actor, canvas=canvas):
        raise PermissionDenied("You cannot edit this foresight canvas.")
    if canvas.status == ForesightCanvas.Status.ARCHIVED:
        raise MappingServiceError("Archived foresight canvases are read-only.")
    owner_id = fields.pop("owner_id", None)
    if owner_id is not None:
        canvas.owner = _active_member(organisation=canvas.organisation, user_id=owner_id)
    before = {key: getattr(canvas, key) for key in fields}
    for key, value in fields.items():
        setattr(canvas, key, value)
    canvas.full_clean(validate_unique=False, validate_constraints=False)
    canvas.save()
    record_event(
        action="foresight.canvas.updated",
        object_type="foresight_canvas",
        object_id=str(canvas.id),
        actor=actor,
        organisation=canvas.organisation,
        metadata={"before": before, "status": canvas.status},
    )
    return canvas


@transaction.atomic
def create_driver(*, actor: User, canvas: ForesightCanvas, **fields: Any) -> Driver:
    _require_contributor(actor=actor, canvas=canvas)
    owner_id = fields.pop("owner_id", actor.id)
    driver = Driver(
        canvas=canvas,
        owner=_active_member(organisation=canvas.organisation, user_id=owner_id),
        created_by=actor,
        **fields,
    )
    try:
        driver.full_clean(validate_unique=False, validate_constraints=False)
        driver.save()
    except IntegrityError as exc:
        raise MappingServiceError({"title": "A driver with this title already exists."}) from exc
    record_event(
        action="foresight.driver.created",
        object_type="foresight_driver",
        object_id=str(driver.id),
        actor=actor,
        organisation=canvas.organisation,
        metadata={"canvas_id": str(canvas.id), "driver_type": driver.driver_type},
    )
    return driver


@transaction.atomic
def update_driver(*, actor: User, driver: Driver, fields: dict[str, Any]) -> Driver:
    driver = Driver.objects.select_for_update().select_related("canvas__organisation").get(id=driver.id)
    if not can_manage_record(
        actor=actor,
        organisation=driver.canvas.organisation,
        created_by_id=driver.created_by_id,
        owner_id=driver.owner_id,
    ):
        raise PermissionDenied("You cannot edit this driver.")
    if driver.canvas.status == ForesightCanvas.Status.ARCHIVED:
        raise MappingServiceError("Archived foresight canvases are read-only.")
    owner_id = fields.pop("owner_id", None)
    if owner_id is not None:
        driver.owner = _active_member(
            organisation=driver.canvas.organisation, user_id=owner_id
        )
    for key, value in fields.items():
        setattr(driver, key, value)
    driver.full_clean(validate_unique=False, validate_constraints=False)
    driver.save()
    record_event(
        action="foresight.driver.updated",
        object_type="foresight_driver",
        object_id=str(driver.id),
        actor=actor,
        organisation=driver.canvas.organisation,
        metadata={"canvas_id": str(driver.canvas_id)},
    )
    return driver


@transaction.atomic
def link_signal_to_driver(
    *, actor: User, driver: Driver, signal_id: Any, rationale: str
) -> DriverSignal:
    _require_contributor(actor=actor, canvas=driver.canvas)
    try:
        signal = Signal.objects.get(id=signal_id, organisation=driver.canvas.organisation)
    except Signal.DoesNotExist as exc:
        raise MappingServiceError({"signal_id": "The signal does not belong to this organisation."}) from exc
    link, created = DriverSignal.objects.get_or_create(
        driver=driver,
        signal=signal,
        defaults={"rationale": rationale, "linked_by": actor},
    )
    if not created:
        link.rationale = rationale
        link.linked_by = actor
    link.full_clean(validate_unique=False, validate_constraints=False)
    link.save()
    record_event(
        action="foresight.driver.signal_linked",
        object_type="foresight_driver_signal",
        object_id=str(link.id),
        actor=actor,
        organisation=driver.canvas.organisation,
        metadata={"driver_id": str(driver.id), "signal_id": str(signal.id)},
    )
    return link


@transaction.atomic
def create_stakeholder(*, actor: User, canvas: ForesightCanvas, **fields: Any) -> SystemStakeholder:
    _require_contributor(actor=actor, canvas=canvas)
    item = SystemStakeholder(canvas=canvas, created_by=actor, **fields)
    try:
        item.full_clean(validate_unique=False, validate_constraints=False)
        item.save()
    except IntegrityError as exc:
        raise MappingServiceError(
            {"name": "A stakeholder with this name already exists."}
        ) from exc
    record_event(
        action="foresight.stakeholder.created",
        object_type="foresight_system_stakeholder",
        object_id=str(item.id),
        actor=actor,
        organisation=canvas.organisation,
        metadata={"canvas_id": str(canvas.id), "name": item.name},
    )
    return item


@transaction.atomic
def create_relationship(*, actor: User, canvas: ForesightCanvas, **fields: Any) -> CausalRelationship:
    _require_contributor(actor=actor, canvas=canvas)
    source_id = fields.pop("source_driver_id")
    target_id = fields.pop("target_driver_id")
    drivers = {str(item.id): item for item in Driver.objects.filter(canvas=canvas, id__in=[source_id, target_id])}
    try:
        source = drivers[str(source_id)]
        target = drivers[str(target_id)]
    except KeyError as exc:
        raise MappingServiceError("Both drivers must belong to this canvas.") from exc
    item = CausalRelationship(
        canvas=canvas,
        source_driver=source,
        target_driver=target,
        created_by=actor,
        **fields,
    )
    try:
        item.full_clean(validate_unique=False, validate_constraints=False)
        item.save()
    except IntegrityError as exc:
        raise MappingServiceError("This directed causal relationship already exists.") from exc
    record_event(
        action="foresight.relationship.created",
        object_type="foresight_causal_relationship",
        object_id=str(item.id),
        actor=actor,
        organisation=canvas.organisation,
        metadata={"source_driver_id": str(source.id), "target_driver_id": str(target.id)},
    )
    return item


@transaction.atomic
def create_feedback_loop(
    *, actor: User, canvas: ForesightCanvas, driver_ids: list[Any], **fields: Any
) -> FeedbackLoop:
    _require_contributor(actor=actor, canvas=canvas)
    if len(driver_ids) != len(set(driver_ids)):
        raise MappingServiceError({"driver_ids": "Choose each driver only once."})
    ordered_ids = list(driver_ids)
    if len(ordered_ids) < 2:
        raise MappingServiceError({"driver_ids": "Choose at least two drivers."})
    drivers_by_id = {
        str(driver.id): driver
        for driver in Driver.objects.filter(canvas=canvas, id__in=ordered_ids)
    }
    if len(drivers_by_id) != len(ordered_ids):
        raise MappingServiceError(
            {"driver_ids": "Every selected driver must belong to this canvas."}
        )
    drivers = [drivers_by_id[str(driver_id)] for driver_id in ordered_ids]
    item = FeedbackLoop(canvas=canvas, created_by=actor, **fields)
    try:
        item.full_clean(validate_unique=False, validate_constraints=False)
        item.save()
    except IntegrityError as exc:
        raise MappingServiceError(
            {"name": "A feedback loop with this name already exists."}
        ) from exc
    FeedbackLoopDriver.objects.bulk_create(
        [
            FeedbackLoopDriver(
                feedback_loop=item,
                driver=driver,
                position=position,
            )
            for position, driver in enumerate(drivers, start=1)
        ]
    )
    record_event(
        action="foresight.feedback_loop.created",
        object_type="foresight_feedback_loop",
        object_id=str(item.id),
        actor=actor,
        organisation=canvas.organisation,
        metadata={
            "canvas_id": str(canvas.id),
            "loop_type": item.loop_type,
            "driver_ids": [str(driver.id) for driver in drivers],
        },
    )
    return item


@transaction.atomic
def create_consequence(*, actor: User, canvas: ForesightCanvas, **fields: Any) -> FuturesWheelConsequence:
    _require_contributor(actor=actor, canvas=canvas)
    driver_id = fields.pop("originating_driver_id", None)
    parent_id = fields.pop("parent_id", None)
    driver = None
    parent = None
    if driver_id:
        try:
            driver = Driver.objects.get(id=driver_id, canvas=canvas)
        except Driver.DoesNotExist as exc:
            raise MappingServiceError({"originating_driver_id": "Choose a driver from this canvas."}) from exc
    if parent_id:
        try:
            parent = FuturesWheelConsequence.objects.get(id=parent_id, canvas=canvas)
        except FuturesWheelConsequence.DoesNotExist as exc:
            raise MappingServiceError({"parent_id": "Choose a consequence from this canvas."}) from exc
        fields["order"] = parent.order + 1
        if fields["order"] > 3:
            raise MappingServiceError({"parent_id": "The futures wheel supports three consequence orders."})
    else:
        fields["order"] = 1
    item = FuturesWheelConsequence(
        canvas=canvas,
        originating_driver=driver,
        parent=parent,
        created_by=actor,
        **fields,
    )
    item.full_clean(validate_unique=False, validate_constraints=False)
    item.save()
    record_event(
        action="foresight.consequence.created",
        object_type="foresight_consequence",
        object_id=str(item.id),
        actor=actor,
        organisation=canvas.organisation,
        metadata={"canvas_id": str(canvas.id), "order": item.order},
    )
    return item


@transaction.atomic
def create_horizon_item(*, actor: User, canvas: ForesightCanvas, **fields: Any) -> ThreeHorizonItem:
    _require_contributor(actor=actor, canvas=canvas)
    item = ThreeHorizonItem(canvas=canvas, created_by=actor, **fields)
    try:
        item.full_clean(validate_unique=False, validate_constraints=False)
        item.save()
    except IntegrityError as exc:
        raise MappingServiceError(
            {"title": "This horizon already contains an item with this title."}
        ) from exc
    record_event(
        action="foresight.horizon_item.created",
        object_type="foresight_horizon_item",
        object_id=str(item.id),
        actor=actor,
        organisation=canvas.organisation,
        metadata={"canvas_id": str(canvas.id), "horizon": item.horizon},
    )
    return item


@transaction.atomic
def create_implication(*, actor: User, canvas: ForesightCanvas, **fields: Any) -> StrategicImplication:
    _require_contributor(actor=actor, canvas=canvas)
    owner_id = fields.pop("owner_id", actor.id)
    decision_id = fields.pop("linked_decision_id", None)
    driver_ids = fields.pop("driver_ids", [])
    decision = None
    if decision_id:
        try:
            decision = Decision.objects.get(id=decision_id, organisation=canvas.organisation)
        except Decision.DoesNotExist as exc:
            raise MappingServiceError({"linked_decision_id": "Choose a decision from this organisation."}) from exc
    drivers = list(Driver.objects.filter(canvas=canvas, id__in=driver_ids))
    if len(drivers) != len(set(driver_ids)):
        raise MappingServiceError({"driver_ids": "Every selected driver must belong to this canvas."})
    item = StrategicImplication(
        canvas=canvas,
        owner=_active_member(organisation=canvas.organisation, user_id=owner_id),
        linked_decision=decision,
        created_by=actor,
        **fields,
    )
    item.full_clean(validate_unique=False, validate_constraints=False)
    item.save()
    item.drivers.set(drivers)
    record_event(
        action="foresight.implication.created",
        object_type="foresight_strategic_implication",
        object_id=str(item.id),
        actor=actor,
        organisation=canvas.organisation,
        metadata={
            "canvas_id": str(canvas.id),
            "linked_decision_id": str(decision.id) if decision else None,
            "driver_ids": [str(driver.id) for driver in drivers],
        },
    )
    return item


@transaction.atomic
def update_implication(
    *, actor: User, implication: StrategicImplication, fields: dict[str, Any]
) -> StrategicImplication:
    implication = StrategicImplication.objects.select_for_update().select_related(
        "canvas__organisation"
    ).get(id=implication.id)
    if not can_manage_record(
        actor=actor,
        organisation=implication.canvas.organisation,
        created_by_id=implication.created_by_id,
        owner_id=implication.owner_id,
    ):
        raise PermissionDenied("You cannot edit this strategic implication.")
    if implication.canvas.status == ForesightCanvas.Status.ARCHIVED:
        raise MappingServiceError("Archived foresight canvases are read-only.")
    owner_id = fields.pop("owner_id", None)
    if owner_id is not None:
        implication.owner = _active_member(
            organisation=implication.canvas.organisation, user_id=owner_id
        )
    for key, value in fields.items():
        setattr(implication, key, value)
    implication.full_clean(validate_unique=False, validate_constraints=False)
    implication.save()
    record_event(
        action="foresight.implication.updated",
        object_type="foresight_strategic_implication",
        object_id=str(implication.id),
        actor=actor,
        organisation=implication.canvas.organisation,
        metadata={"status": implication.status, "priority": implication.priority},
    )
    return implication
