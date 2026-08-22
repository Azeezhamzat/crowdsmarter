"""Thin REST endpoints for participant workflows."""

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.decision_options.selectors import option_for_user
from apps.decisions.selectors import decision_for_user

from .permissions import CanAccessParticipant
from .selectors import (
    conflict_for_user,
    participant_for_user,
    participants_for_decision,
)
from .serializers import (
    ConflictOfInterestCreateSerializer,
    ConflictOfInterestSerializer,
    ParticipantCreateSerializer,
    ParticipantSerializer,
    ParticipantUpdateSerializer,
)
from .services import (
    add_participant,
    change_participant_role,
    conflicts_for_decision,
    declare_conflict,
    remove_participant,
    withdraw_conflict,
)

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


class ParticipantConflictListCreateView(APIView):
    """Declare a conflict of interest, or list active ones for a decision."""

    permission_classes = [IsAuthenticated]

    def get(self, request, participant_id):  # type: ignore[no-untyped-def]
        participant = participant_for_user(user=request.user, participant_id=participant_id)
        conflicts = conflicts_for_decision(decision=participant.decision)
        return Response(ConflictOfInterestSerializer(conflicts, many=True).data)

    def post(self, request, participant_id):  # type: ignore[no-untyped-def]
        participant = participant_for_user(user=request.user, participant_id=participant_id)
        serializer = ConflictOfInterestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        option_id = data.pop("option_id", None)
        option = (
            option_for_user(user=request.user, option_id=option_id) if option_id else None
        )
        conflict = declare_conflict(
            actor=request.user, participant=participant, option=option, **data
        )
        return Response(
            ConflictOfInterestSerializer(conflict).data, status=status.HTTP_201_CREATED
        )


class ConflictWithdrawView(APIView):
    """Withdraw one active conflict declaration."""

    permission_classes = [IsAuthenticated]

    def post(self, request, conflict_id):  # type: ignore[no-untyped-def]
        conflict = conflict_for_user(user=request.user, conflict_id=conflict_id)
        conflict = withdraw_conflict(actor=request.user, conflict=conflict)
        return Response(ConflictOfInterestSerializer(conflict).data)
