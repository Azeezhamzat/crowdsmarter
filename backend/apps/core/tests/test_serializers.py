import pytest
from rest_framework import serializers

from apps.core.serializers import StrictSerializer


class ExampleCommandSerializer(StrictSerializer):
    name = serializers.CharField()


def test_strict_serializer_rejects_unexpected_fields() -> None:
    serializer = ExampleCommandSerializer(data={"name": "Valid", "naem": "Typo"})

    with pytest.raises(serializers.ValidationError) as exc_info:
        serializer.is_valid(raise_exception=True)

    assert "naem" in exc_info.value.detail
