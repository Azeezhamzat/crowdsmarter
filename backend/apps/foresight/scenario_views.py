"""Thin REST endpoints for scenarios, wind-tunnelling, and adaptive signposts."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .mapping_selectors import canvas_for_user
from .scenario_selectors import (
    scenario_for_user,
    scenario_set_for_user,
    scenario_set_workspace_for_user,
    scenario_sets_for_canvas,
    signpost_for_user,
)
from .scenario_serializers import (
    ScenarioDriverStateSerializer,
    ScenarioDriverStateWriteSerializer,
    ScenarioImplicationLinkSerializer,
    ScenarioImplicationLinkWriteSerializer,
    ScenarioPatchSerializer,
    ScenarioReviewSerializer,
    ScenarioReviewWriteSerializer,
    ScenarioSerializer,
    ScenarioSetPatchSerializer,
    ScenarioSetSerializer,
    ScenarioSetWorkspaceSerializer,
    ScenarioSetWriteSerializer,
    ScenarioWriteSerializer,
    SignpostAssumptionLinkWriteSerializer,
    SignpostObservationSerializer,
    SignpostObservationWriteSerializer,
    SignpostRiskLinkWriteSerializer,
    SignpostSerializer,
    SignpostWriteSerializer,
    WindTunnelAssessmentSerializer,
    WindTunnelAssessmentWriteSerializer,
)
from .scenario_services import (
    assess_option,
    create_scenario,
    create_scenario_set,
    create_signpost,
    create_signpost_observation,
    link_scenario_implication,
    link_signpost_to_assumption,
    link_signpost_to_risk,
    set_scenario_driver_state,
    submit_scenario_review,
    update_scenario,
    update_scenario_set,
)


class ScenarioSetListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, canvas_id):  # type: ignore[no-untyped-def]
        canvas_for_user(user=request.user, canvas_id=canvas_id)
        items = scenario_sets_for_canvas(user=request.user, canvas_id=canvas_id)
        return Response(ScenarioSetSerializer(items, many=True, context={"request": request}).data)

    def post(self, request, canvas_id):  # type: ignore[no-untyped-def]
        canvas = canvas_for_user(user=request.user, canvas_id=canvas_id)
        serializer = ScenarioSetWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_scenario_set(actor=request.user, canvas=canvas, **serializer.validated_data)
        return Response(
            ScenarioSetSerializer(item, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class ScenarioSetDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, scenario_set_id):  # type: ignore[no-untyped-def]
        item = scenario_set_workspace_for_user(user=request.user, scenario_set_id=scenario_set_id)
        return Response(ScenarioSetWorkspaceSerializer(item, context={"request": request}).data)

    def patch(self, request, scenario_set_id):  # type: ignore[no-untyped-def]
        item = scenario_set_for_user(user=request.user, scenario_set_id=scenario_set_id)
        serializer = ScenarioSetPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = update_scenario_set(
            actor=request.user,
            scenario_set=item,
            fields=dict(serializer.validated_data),
        )
        return Response(ScenarioSetSerializer(item, context={"request": request}).data)


class ScenarioListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, scenario_set_id):  # type: ignore[no-untyped-def]
        scenario_set = scenario_set_for_user(user=request.user, scenario_set_id=scenario_set_id)
        serializer = ScenarioWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_scenario(
            actor=request.user,
            scenario_set=scenario_set,
            **serializer.validated_data,
        )
        return Response(
            ScenarioSerializer(item, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class ScenarioDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, scenario_id):  # type: ignore[no-untyped-def]
        item = scenario_for_user(user=request.user, scenario_id=scenario_id)
        serializer = ScenarioPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = update_scenario(
            actor=request.user,
            scenario=item,
            fields=dict(serializer.validated_data),
        )
        return Response(ScenarioSerializer(item, context={"request": request}).data)


class ScenarioDriverStateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, scenario_id):  # type: ignore[no-untyped-def]
        scenario = scenario_for_user(user=request.user, scenario_id=scenario_id)
        serializer = ScenarioDriverStateWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = set_scenario_driver_state(
            actor=request.user,
            scenario=scenario,
            **serializer.validated_data,
        )
        return Response(ScenarioDriverStateSerializer(item).data)


class ScenarioReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, scenario_id):  # type: ignore[no-untyped-def]
        scenario = scenario_for_user(user=request.user, scenario_id=scenario_id)
        serializer = ScenarioReviewWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = submit_scenario_review(
            actor=request.user,
            scenario=scenario,
            **serializer.validated_data,
        )
        return Response(ScenarioReviewSerializer(item).data)


class WindTunnelAssessmentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, scenario_id):  # type: ignore[no-untyped-def]
        scenario = scenario_for_user(user=request.user, scenario_id=scenario_id)
        serializer = WindTunnelAssessmentWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = assess_option(
            actor=request.user,
            scenario=scenario,
            **serializer.validated_data,
        )
        return Response(WindTunnelAssessmentSerializer(item).data)


class SignpostListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, scenario_set_id):  # type: ignore[no-untyped-def]
        scenario_set = scenario_set_for_user(user=request.user, scenario_set_id=scenario_set_id)
        serializer = SignpostWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = dict(serializer.validated_data)
        scenario_links = validated.pop("scenario_links", [])
        item = create_signpost(
            actor=request.user,
            scenario_set=scenario_set,
            scenario_links=scenario_links,
            **validated,
        )
        return Response(SignpostSerializer(item).data, status=status.HTTP_201_CREATED)


class SignpostObservationCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, signpost_id):  # type: ignore[no-untyped-def]
        signpost = signpost_for_user(user=request.user, signpost_id=signpost_id)
        serializer = SignpostObservationWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_signpost_observation(
            actor=request.user,
            signpost=signpost,
            **serializer.validated_data,
        )
        return Response(
            SignpostObservationSerializer(item).data,
            status=status.HTTP_201_CREATED,
        )


class SignpostAssumptionLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, signpost_id):  # type: ignore[no-untyped-def]
        signpost = signpost_for_user(user=request.user, signpost_id=signpost_id)
        serializer = SignpostAssumptionLinkWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        link_signpost_to_assumption(
            actor=request.user,
            signpost=signpost,
            **serializer.validated_data,
        )
        return Response(
            SignpostSerializer(signpost_for_user(user=request.user, signpost_id=signpost_id)).data,
            status=status.HTTP_201_CREATED,
        )


class SignpostRiskLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, signpost_id):  # type: ignore[no-untyped-def]
        signpost = signpost_for_user(user=request.user, signpost_id=signpost_id)
        serializer = SignpostRiskLinkWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        link_signpost_to_risk(
            actor=request.user,
            signpost=signpost,
            **serializer.validated_data,
        )
        return Response(
            SignpostSerializer(signpost_for_user(user=request.user, signpost_id=signpost_id)).data,
            status=status.HTTP_201_CREATED,
        )


class ScenarioImplicationLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, scenario_id):  # type: ignore[no-untyped-def]
        scenario = scenario_for_user(user=request.user, scenario_id=scenario_id)
        serializer = ScenarioImplicationLinkWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = link_scenario_implication(
            actor=request.user,
            scenario=scenario,
            **serializer.validated_data,
        )
        return Response(ScenarioImplicationLinkSerializer(item).data)
