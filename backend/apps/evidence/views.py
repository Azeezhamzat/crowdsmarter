"""Thin REST endpoints for evidence."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.decisions.selectors import decision_for_user

from .permissions import CanEditEvidence
from .selectors import evidence_for_decision, evidence_for_user
from .serializers import EvidenceCreateSerializer, EvidenceSerializer, EvidenceUpdateSerializer
from .services import create_evidence, update_evidence


class EvidenceListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, decision_id):  # type: ignore[no-untyped-def]
        items = evidence_for_decision(user=request.user, decision_id=decision_id)
        return Response(EvidenceSerializer(items, many=True, context={"request": request}).data)

    def post(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        serializer = EvidenceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_evidence(actor=request.user, decision=decision, **serializer.validated_data)
        return Response(
            EvidenceSerializer(item, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class EvidenceDetailView(APIView):
    permission_classes = [IsAuthenticated, CanEditEvidence]

    def _get_object(self, request, evidence_id):  # type: ignore[no-untyped-def]
        item = evidence_for_user(user=request.user, evidence_id=evidence_id)
        self.check_object_permissions(request, item)
        return item

    def get(self, request, evidence_id):  # type: ignore[no-untyped-def]
        item = self._get_object(request, evidence_id)
        return Response(EvidenceSerializer(item, context={"request": request}).data)

    def patch(self, request, evidence_id):  # type: ignore[no-untyped-def]
        item = self._get_object(request, evidence_id)
        serializer = EvidenceUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = update_evidence(
            actor=request.user,
            item=item,
            fields=dict(serializer.validated_data),
        )
        return Response(EvidenceSerializer(item, context={"request": request}).data)
