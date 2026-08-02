from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.decisions.selectors import decision_for_user

from .permissions import CanEditRisk
from .selectors import risk_for_user, risks_for_decision
from .serializers import RiskCreateSerializer, RiskSerializer, RiskUpdateSerializer
from .services import create_risk, update_risk


class RiskListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, decision_id):  # type: ignore[no-untyped-def]
        items = risks_for_decision(user=request.user, decision_id=decision_id)
        return Response(RiskSerializer(items, many=True, context={"request": request}).data)

    def post(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        serializer = RiskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_risk(actor=request.user, decision=decision, **serializer.validated_data)
        return Response(
            RiskSerializer(item, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class RiskDetailView(APIView):
    permission_classes = [IsAuthenticated, CanEditRisk]

    def _get_object(self, request, risk_id):  # type: ignore[no-untyped-def]
        item = risk_for_user(user=request.user, risk_id=risk_id)
        self.check_object_permissions(request, item)
        return item

    def get(self, request, risk_id):  # type: ignore[no-untyped-def]
        item = self._get_object(request, risk_id)
        return Response(RiskSerializer(item, context={"request": request}).data)

    def patch(self, request, risk_id):  # type: ignore[no-untyped-def]
        item = self._get_object(request, risk_id)
        serializer = RiskUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = update_risk(actor=request.user, risk=item, fields=dict(serializer.validated_data))
        return Response(RiskSerializer(item, context={"request": request}).data)
