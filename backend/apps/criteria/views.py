from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.decisions.selectors import decision_for_user

from .permissions import CanEditCriterion
from .selectors import criteria_for_decision, criterion_for_user
from .serializers import CriterionCreateSerializer, CriterionSerializer, CriterionUpdateSerializer
from .services import create_criterion, update_criterion


class CriterionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, decision_id):  # type: ignore[no-untyped-def]
        items = criteria_for_decision(user=request.user, decision_id=decision_id)
        return Response(CriterionSerializer(items, many=True, context={"request": request}).data)

    def post(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        serializer = CriterionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_criterion(actor=request.user, decision=decision, **serializer.validated_data)
        return Response(
            CriterionSerializer(item, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class CriterionDetailView(APIView):
    permission_classes = [IsAuthenticated, CanEditCriterion]

    def _get_object(self, request, criterion_id):  # type: ignore[no-untyped-def]
        item = criterion_for_user(user=request.user, criterion_id=criterion_id)
        self.check_object_permissions(request, item)
        return item

    def get(self, request, criterion_id):  # type: ignore[no-untyped-def]
        item = self._get_object(request, criterion_id)
        return Response(CriterionSerializer(item, context={"request": request}).data)

    def patch(self, request, criterion_id):  # type: ignore[no-untyped-def]
        item = self._get_object(request, criterion_id)
        serializer = CriterionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = update_criterion(
            actor=request.user, criterion=item, fields=dict(serializer.validated_data)
        )
        return Response(CriterionSerializer(item, context={"request": request}).data)
