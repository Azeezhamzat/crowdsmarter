from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.decisions.selectors import decision_for_user

from .permissions import CanEditAssumption
from .selectors import assumption_for_user, assumptions_for_decision
from .serializers import (
    AssumptionCreateSerializer,
    AssumptionSerializer,
    AssumptionUpdateSerializer,
)
from .services import create_assumption, update_assumption


class AssumptionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, decision_id):  # type: ignore[no-untyped-def]
        items = assumptions_for_decision(user=request.user, decision_id=decision_id)
        return Response(AssumptionSerializer(items, many=True, context={"request": request}).data)

    def post(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        serializer = AssumptionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_assumption(
            actor=request.user,
            decision=decision,
            **serializer.validated_data,
        )
        return Response(
            AssumptionSerializer(item, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class AssumptionDetailView(APIView):
    permission_classes = [IsAuthenticated, CanEditAssumption]

    def _get_object(self, request, assumption_id):  # type: ignore[no-untyped-def]
        item = assumption_for_user(user=request.user, assumption_id=assumption_id)
        self.check_object_permissions(request, item)
        return item

    def get(self, request, assumption_id):  # type: ignore[no-untyped-def]
        item = self._get_object(request, assumption_id)
        return Response(AssumptionSerializer(item, context={"request": request}).data)

    def patch(self, request, assumption_id):  # type: ignore[no-untyped-def]
        item = self._get_object(request, assumption_id)
        serializer = AssumptionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = update_assumption(
            actor=request.user,
            assumption=item,
            fields=dict(serializer.validated_data),
        )
        return Response(AssumptionSerializer(item, context={"request": request}).data)
