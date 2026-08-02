"""Thin REST endpoints for decision workflows."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.workspaces.selectors import workspace_for_user

from .finalisation import finalise_decision
from .models import DecisionFinalisation
from .permissions import CanAccessDecision
from .selectors import decision_for_user, decisions_for_workspace, transitions_for_decision
from .serializers import (
    DecisionCreateSerializer,
    DecisionDetailSerializer,
    DecisionFinalisationInputSerializer,
    DecisionFinalisationSerializer,
    DecisionSummarySerializer,
    DecisionTransitionInputSerializer,
    DecisionTransitionSerializer,
    DecisionUpdateSerializer,
)
from .services import create_decision, transition_decision, update_decision


class DecisionListCreateView(APIView):
    """List workspace decisions or create a draft."""

    permission_classes = [IsAuthenticated]

    def get(self, request, workspace_id):  # type: ignore[no-untyped-def]
        decisions = decisions_for_workspace(user=request.user, workspace_id=workspace_id)
        return Response(DecisionSummarySerializer(decisions, many=True).data)

    def post(self, request, workspace_id):  # type: ignore[no-untyped-def]
        workspace = workspace_for_user(user=request.user, workspace_id=workspace_id)
        serializer = DecisionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision = create_decision(
            actor=request.user,
            workspace=workspace,
            **serializer.validated_data,
        )
        return Response(
            DecisionDetailSerializer(decision, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class DecisionDetailView(APIView):
    """Read or edit the framing record without allowing status mutation."""

    permission_classes = [IsAuthenticated, CanAccessDecision]

    def _get_object(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        self.check_object_permissions(request, decision)
        return decision

    def get(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = self._get_object(request, decision_id)
        return Response(DecisionDetailSerializer(decision, context={"request": request}).data)

    def patch(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = self._get_object(request, decision_id)
        serializer = DecisionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision = update_decision(
            actor=request.user,
            decision=decision,
            fields=dict(serializer.validated_data),
        )
        return Response(DecisionDetailSerializer(decision, context={"request": request}).data)


class DecisionTransitionListCreateView(APIView):
    """Read lifecycle history or execute one human-authorised transition."""

    permission_classes = [IsAuthenticated]

    def get(self, request, decision_id):  # type: ignore[no-untyped-def]
        transitions = transitions_for_decision(user=request.user, decision_id=decision_id)
        return Response(DecisionTransitionSerializer(transitions, many=True).data)

    def post(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        serializer = DecisionTransitionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transition = transition_decision(
            actor=request.user,
            decision=decision,
            **serializer.validated_data,
        )
        return Response(
            DecisionTransitionSerializer(transition).data,
            status=status.HTTP_201_CREATED,
        )


class DecisionFinalisationView(APIView):
    """Read or create the immutable human final decision record."""

    permission_classes = [IsAuthenticated]

    def get(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        finalisation = DecisionFinalisation.objects.select_related(
            "selected_option",
            "decided_by",
        ).filter(decision=decision).first()
        return Response(
            {
                "finalisation": (
                    DecisionFinalisationSerializer(finalisation).data
                    if finalisation
                    else None
                )
            }
        )

    def post(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        serializer = DecisionFinalisationInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        finalisation = finalise_decision(
            actor=request.user,
            decision=decision,
            **serializer.validated_data,
        )
        return Response(
            DecisionFinalisationSerializer(finalisation).data,
            status=status.HTTP_201_CREATED,
        )
