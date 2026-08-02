"""Thin REST endpoints for participant workflows."""

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.decisions.selectors import decision_for_user

from .permissions import CanAccessParticipant
from .selectors import participant_for_user, participants_for_decision
from .serializers import (
    ParticipantCreateSerializer,
    ParticipantSerializer,
    ParticipantUpdateSerializer,
)
from .services import add_participant, change_participant_role, remove_participant

User = get_user_model()


class ParticipantListCreateView(APIView):
    """List active stakeholders or add an organisation member."""

    permission_classes = [IsAuthenticated]

    def get(self, request, decision_id):  # type: ignore[no-untyped-def]
        participants = participants_for_decision(
            user=request.user, decision_id=decision_id
        )
        return Response(ParticipantSerializer(participants, many=True).data)

    def post(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        serializer = ParticipantCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(
            User,
            email__iexact=serializer.validated_data["email"],
            organisation_memberships__organisation=decision.organisation,
            organisation_memberships__status="active",
        )
        participant = add_participant(
            actor=request.user,
            decision=decision,
            user=user,
            role=serializer.validated_data["role"],
        )
        return Response(
            ParticipantSerializer(participant).data,
            status=status.HTTP_201_CREATED,
        )


class ParticipantDetailView(APIView):
    """Change or remove one tenant-scoped participant."""

    permission_classes = [IsAuthenticated, CanAccessParticipant]

    def _get_object(self, request, participant_id):  # type: ignore[no-untyped-def]
        participant = participant_for_user(
            user=request.user, participant_id=participant_id
        )
        self.check_object_permissions(request, participant)
        return participant

    def patch(self, request, participant_id):  # type: ignore[no-untyped-def]
        participant = self._get_object(request, participant_id)
        serializer = ParticipantUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        participant = change_participant_role(
            actor=request.user,
            participant=participant,
            role=serializer.validated_data["role"],
        )
        return Response(ParticipantSerializer(participant).data)

    def delete(self, request, participant_id):  # type: ignore[no-untyped-def]
        participant = self._get_object(request, participant_id)
        remove_participant(actor=request.user, participant=participant)
        return Response(status=status.HTTP_204_NO_CONTENT)
