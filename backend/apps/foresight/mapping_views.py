"""Thin REST endpoints for systems and futures mapping."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organisations.selectors import organisation_for_user

from .mapping_selectors import (
    canvas_for_user,
    canvas_workspace_for_user,
    canvases_for_organisation,
    driver_for_user,
    implication_for_user,
)
from .mapping_serializers import (
    CanvasPatchSerializer,
    CanvasSerializer,
    CanvasWorkspaceSerializer,
    CanvasWriteSerializer,
    ConsequenceSerializer,
    ConsequenceWriteSerializer,
    DriverPatchSerializer,
    DriverSerializer,
    DriverSignalWriteSerializer,
    DriverWriteSerializer,
    FeedbackLoopSerializer,
    FeedbackLoopWriteSerializer,
    HorizonItemSerializer,
    HorizonItemWriteSerializer,
    ImplicationPatchSerializer,
    ImplicationSerializer,
    ImplicationWriteSerializer,
    RelationshipSerializer,
    RelationshipWriteSerializer,
    StakeholderSerializer,
    StakeholderWriteSerializer,
)
from .mapping_services import (
    create_canvas,
    create_consequence,
    create_driver,
    create_feedback_loop,
    create_horizon_item,
    create_implication,
    create_relationship,
    create_stakeholder,
    link_signal_to_driver,
    update_canvas,
    update_driver,
    update_implication,
)


class CanvasListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        items = canvases_for_organisation(user=request.user, organisation_id=organisation_id)
        return Response(CanvasSerializer(items, many=True, context={"request": request}).data)

    def post(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        serializer = CanvasWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_canvas(
            actor=request.user, organisation=organisation, **serializer.validated_data
        )
        return Response(
            CanvasSerializer(item, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class CanvasDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, canvas_id):  # type: ignore[no-untyped-def]
        item = canvas_workspace_for_user(user=request.user, canvas_id=canvas_id)
        return Response(CanvasWorkspaceSerializer(item, context={"request": request}).data)

    def patch(self, request, canvas_id):  # type: ignore[no-untyped-def]
        item = canvas_for_user(user=request.user, canvas_id=canvas_id)
        serializer = CanvasPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = update_canvas(
            actor=request.user, canvas=item, fields=dict(serializer.validated_data)
        )
        return Response(CanvasSerializer(item, context={"request": request}).data)


class DriverListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, canvas_id):  # type: ignore[no-untyped-def]
        canvas = canvas_for_user(user=request.user, canvas_id=canvas_id)
        serializer = DriverWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_driver(actor=request.user, canvas=canvas, **serializer.validated_data)
        return Response(
            DriverSerializer(item, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class DriverDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, driver_id):  # type: ignore[no-untyped-def]
        item = driver_for_user(user=request.user, driver_id=driver_id)
        serializer = DriverPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = update_driver(
            actor=request.user, driver=item, fields=dict(serializer.validated_data)
        )
        return Response(DriverSerializer(item, context={"request": request}).data)


class DriverSignalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, driver_id):  # type: ignore[no-untyped-def]
        item = driver_for_user(user=request.user, driver_id=driver_id)
        serializer = DriverSignalWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        link_signal_to_driver(actor=request.user, driver=item, **serializer.validated_data)
        item = driver_for_user(user=request.user, driver_id=driver_id)
        return Response(DriverSerializer(item, context={"request": request}).data)


class StakeholderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, canvas_id):  # type: ignore[no-untyped-def]
        canvas = canvas_for_user(user=request.user, canvas_id=canvas_id)
        serializer = StakeholderWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_stakeholder(actor=request.user, canvas=canvas, **serializer.validated_data)
        return Response(StakeholderSerializer(item).data, status=status.HTTP_201_CREATED)


class RelationshipListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, canvas_id):  # type: ignore[no-untyped-def]
        canvas = canvas_for_user(user=request.user, canvas_id=canvas_id)
        serializer = RelationshipWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_relationship(actor=request.user, canvas=canvas, **serializer.validated_data)
        return Response(RelationshipSerializer(item).data, status=status.HTTP_201_CREATED)


class FeedbackLoopListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, canvas_id):  # type: ignore[no-untyped-def]
        canvas = canvas_for_user(user=request.user, canvas_id=canvas_id)
        serializer = FeedbackLoopWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_feedback_loop(actor=request.user, canvas=canvas, **serializer.validated_data)
        return Response(FeedbackLoopSerializer(item).data, status=status.HTTP_201_CREATED)


class ConsequenceListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, canvas_id):  # type: ignore[no-untyped-def]
        canvas = canvas_for_user(user=request.user, canvas_id=canvas_id)
        serializer = ConsequenceWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_consequence(actor=request.user, canvas=canvas, **serializer.validated_data)
        return Response(ConsequenceSerializer(item).data, status=status.HTTP_201_CREATED)


class HorizonItemListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, canvas_id):  # type: ignore[no-untyped-def]
        canvas = canvas_for_user(user=request.user, canvas_id=canvas_id)
        serializer = HorizonItemWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_horizon_item(actor=request.user, canvas=canvas, **serializer.validated_data)
        return Response(HorizonItemSerializer(item).data, status=status.HTTP_201_CREATED)


class ImplicationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, canvas_id):  # type: ignore[no-untyped-def]
        canvas = canvas_for_user(user=request.user, canvas_id=canvas_id)
        serializer = ImplicationWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_implication(actor=request.user, canvas=canvas, **serializer.validated_data)
        item = implication_for_user(user=request.user, implication_id=item.id)
        return Response(
            ImplicationSerializer(item, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class ImplicationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, implication_id):  # type: ignore[no-untyped-def]
        item = implication_for_user(user=request.user, implication_id=implication_id)
        serializer = ImplicationPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = update_implication(
            actor=request.user, implication=item, fields=dict(serializer.validated_data)
        )
        return Response(ImplicationSerializer(item, context={"request": request}).data)
