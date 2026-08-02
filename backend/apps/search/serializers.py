"""Search response contracts."""

from rest_framework import serializers


class SearchResultSerializer(serializers.Serializer):
    kind = serializers.CharField()
    object_id = serializers.CharField()
    decision_id = serializers.CharField()
    title = serializers.CharField()
    snippet = serializers.CharField()
    url = serializers.CharField()
    rank = serializers.FloatField()
