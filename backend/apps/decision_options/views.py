"""Thin REST endpoints for decision options."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.decisions.selectors import decision_for_user
from apps.organisations.selectors import organisation_for_user

from .permissions import CanEditDecisionOption
from .selectors import option_for_user, options_for_decision
from .serializers import (
    DecisionOptionCreateSerializer,
    DecisionOptionEligibilitySerializer,
    DecisionOptionOutcomeSerializer,
    DecisionOptionSerializer,
    DecisionOptionUpdateSerializer,
    OrganisationBudgetRollupSerializer,
)
from .services import (
    create_option,
    organisation_budget_rollup,
    set_eligibility,
    set_outcome,
    update_option,
)


class DecisionOptionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, decision_id):  # type: ignore[no-untyped-def]
        options = options_for_decision(user=request.user, decision_id=decision_id)
        return Response(
            DecisionOptionSerializer(options, many=True, context={"request": request}).data
        )

    def post(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        serializer = DecisionOptionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        option = create_option(actor=request.user, decision=decision, **serializer.validated_data)
        return Response(
            DecisionOptionSerializer(option, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class DecisionOptionDetailView(APIView):
    permission_classes = [IsAuthenticated, CanEditDecisionOption]

    def _get_object(self, request, option_id):  # type: ignore[no-untyped-def]
        option = option_for_user(user=request.user, option_id=option_id)
        self.check_object_permissions(request, option)
        return option

    def get(self, request, option_id):  # type: ignore[no-untyped-def]
        option = self._get_object(request, option_id)
        return Response(DecisionOptionSerializer(option, context={"request": request}).data)

    def patch(self, request, option_id):  # type: ignore[no-untyped-def]
        option = self._get_object(request, option_id)
        serializer = DecisionOptionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        option = update_option(
            actor=request.user,
            option=option,
            fields=dict(serializer.validated_data),
        )
        return Response(DecisionOptionSerializer(option, context={"request": request}).data)


class DecisionOptionEligibilityView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, option_id):  # type: ignore[no-untyped-def]
        option = option_for_user(user=request.user, option_id=option_id)
        serializer = DecisionOptionEligibilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        option = set_eligibility(actor=request.user, option=option, **serializer.validated_data)
        return Response(DecisionOptionSerializer(option, context={"request": request}).data)


class DecisionOptionOutcomeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, option_id):  # type: ignore[no-untyped-def]
        option = option_for_user(user=request.user, option_id=option_id)
        serializer = DecisionOptionOutcomeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        option = set_outcome(actor=request.user, option=option, **serializer.validated_data)
        return Response(DecisionOptionSerializer(option, context={"request": request}).data)


class OrganisationBudgetRollupView(APIView):
    """Cross-round budget totals and a monthly awarded trend for every grant round in one organisation."""

    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        data = organisation_budget_rollup(organisation=organisation)
        return Response(OrganisationBudgetRollupSerializer(data).data)
