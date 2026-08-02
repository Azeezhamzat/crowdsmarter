"""Thin endpoints for stakeholder position submission and history."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.decisions.selectors import decision_for_user

from .selectors import current_positions_for_decision, position_history_for_decision
from .serializers import PositionSerializer, PositionSubmitSerializer
from .services import submit_position


class PositionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, decision_id):  # type: ignore[no-untyped-def]
        items = current_positions_for_decision(
            user=request.user,
            decision_id=decision_id,
        )
        return Response(PositionSerializer(items, many=True).data)

    def post(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        serializer = PositionSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        position = submit_position(
            actor=request.user,
            decision=decision,
            **serializer.validated_data,
        )
        return Response(
            PositionSerializer(position).data,
            status=status.HTTP_201_CREATED,
        )


class PositionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, decision_id):  # type: ignore[no-untyped-def]
        items = position_history_for_decision(
            user=request.user,
            decision_id=decision_id,
        )
        return Response(PositionSerializer(items, many=True).data)
