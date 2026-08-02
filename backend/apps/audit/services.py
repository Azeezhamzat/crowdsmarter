"""Audit recording service."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from apps.accounts.models import User
from apps.organisations.models import Organisation

from .models import AuditEvent


def _json_safe(value: Any) -> Any:
    """Convert common domain values into deterministic JSON-safe representations."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (UUID, Decimal, Enum)):
        return str(value.value if isinstance(value, Enum) else value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return str(value)


def record_event(
    *,
    action: str,
    object_type: str,
    object_id: str,
    actor: User | None,
    organisation: Organisation | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    """Append an attributable audit event with JSON-safe metadata."""
    return AuditEvent.objects.create(
        action=action,
        object_type=object_type,
        object_id=object_id,
        actor=actor,
        organisation=organisation,
        metadata=_json_safe(metadata or {}),
    )
