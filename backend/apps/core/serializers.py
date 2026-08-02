"""Shared API serializer primitives."""

from collections.abc import Mapping
from typing import Any

from rest_framework import serializers


class StrictSerializer(serializers.Serializer):
    """Reject unexpected input keys instead of silently discarding them."""

    def to_internal_value(self, data: Any) -> dict[str, Any]:
        if isinstance(data, Mapping):
            unknown_fields = sorted(set(data) - set(self.fields))
            if unknown_fields:
                raise serializers.ValidationError(
                    {
                        field: ["This field is not accepted by this endpoint."]
                        for field in unknown_fields
                    }
                )
        return super().to_internal_value(data)
