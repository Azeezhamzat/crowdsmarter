"""Thin REST endpoints for source and signal intelligence."""

from django.db.models import Count
from django.http import FileResponse
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organisations.selectors import organisation_for_user

from .models import Signal
from .policies import can_contribute
from .selectors import (
    attachment_for_user,
    feed_for_user,
    feeds_for_organisation,
    signal_for_user,
    signals_for_organisation,
    source_for_user,
    sources_for_organisation,
    watchlist_for_user,
    watchlists_for_organisation,
)
from .serializers import (
    FeedSubscriptionSerializer,
    FeedSubscriptionWriteSerializer,
    SignalDecisionLinkSerializer,
    SignalPatchSerializer,
    SignalSerializer,
    SignalWriteSerializer,
    SourceAttachmentSerializer,
    SourcePatchSerializer,
    SourceSerializer,
    SourceWriteSerializer,
    WatchlistPatchSerializer,
    WatchlistSerializer,
    WatchlistSignalSerializer,
    WatchlistWriteSerializer,
)
from .throttles import ForesightFeedSyncThrottle
from .services import (
    add_signal_to_watchlist,
    create_feed_subscription,
    attach_source_file,
    create_signal,
    create_source,
    create_watchlist,
    link_signal_to_decision,
    record_source_attachment_download,
    remove_signal_from_watchlist,
    sync_feed_subscription,
    update_signal,
    update_source,
    update_watchlist,
)


class FeedSubscriptionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        items = feeds_for_organisation(user=request.user, organisation_id=organisation_id)
        return Response(
            FeedSubscriptionSerializer(items, many=True, context={"request": request}).data
        )

    def post(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        serializer = FeedSubscriptionWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_feed_subscription(
            actor=request.user, organisation=organisation, **serializer.validated_data
        )
        return Response(
            FeedSubscriptionSerializer(item, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class FeedSubscriptionSyncView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ForesightFeedSyncThrottle]

    def post(self, request, feed_id):  # type: ignore[no-untyped-def]
        item = feed_for_user(user=request.user, feed_id=feed_id)
        result = sync_feed_subscription(actor=request.user, feed=item)
        item = feed_for_user(user=request.user, feed_id=feed_id)
        return Response(
            {
                "feed": FeedSubscriptionSerializer(item, context={"request": request}).data,
                "result": result,
            }
        )


class ForesightOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        base = Signal.objects.filter(organisation=organisation).exclude(status=Signal.Status.RETIRED)
        by_steep = {
            item["steep_category"]: item["count"]
            for item in base.values("steep_category").annotate(count=Count("id"))
        }
        by_horizon = {
            item["time_horizon"]: item["count"]
            for item in base.values("time_horizon").annotate(count=Count("id"))
        }
        return Response(
            {
                "signal_count": base.count(),
                "source_count": organisation.foresight_sources.filter(status="active").count(),
                "watchlist_count": organisation.foresight_watchlists.filter(is_active=True).count(),
                "canvas_count": organisation.foresight_canvases.exclude(status="archived").count(),
                "high_attention_count": base.filter(impact__gte=4, uncertainty__gte=4).count(),
                "by_steep": by_steep,
                "by_horizon": by_horizon,
                "can_contribute": can_contribute(actor=request.user, organisation=organisation),
            }
        )


class SourceListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        items = sources_for_organisation(
            user=request.user,
            organisation_id=organisation_id,
            query=request.query_params.get("q", "").strip(),
            status=request.query_params.get("status", "").strip(),
        )
        return Response(SourceSerializer(items, many=True, context={"request": request}).data)

    def post(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        serializer = SourceWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_source(actor=request.user, organisation=organisation, **serializer.validated_data)
        return Response(
            SourceSerializer(item, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class SourceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, source_id):  # type: ignore[no-untyped-def]
        item = source_for_user(user=request.user, source_id=source_id)
        return Response(SourceSerializer(item, context={"request": request}).data)

    def patch(self, request, source_id):  # type: ignore[no-untyped-def]
        item = source_for_user(user=request.user, source_id=source_id)
        serializer = SourcePatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = update_source(actor=request.user, source=item, fields=dict(serializer.validated_data))
        return Response(SourceSerializer(item, context={"request": request}).data)


class SourceAttachmentUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, source_id):  # type: ignore[no-untyped-def]
        item = source_for_user(user=request.user, source_id=source_id)
        upload = request.FILES.get("file")
        if upload is None:
            return Response({"file": ["Choose a file to upload."]}, status=status.HTTP_400_BAD_REQUEST)
        attachment = attach_source_file(actor=request.user, source=item, upload=upload)
        return Response(
            SourceAttachmentSerializer(attachment).data,
            status=status.HTTP_201_CREATED,
        )


class SourceAttachmentDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, attachment_id):  # type: ignore[no-untyped-def]
        attachment = attachment_for_user(user=request.user, attachment_id=attachment_id)
        file_handle = attachment.file.open("rb")
        record_source_attachment_download(actor=request.user, attachment=attachment)
        response = FileResponse(
            file_handle,
            as_attachment=True,
            filename=attachment.original_name,
            content_type=attachment.content_type,
        )
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response


class SignalListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        items = signals_for_organisation(
            user=request.user,
            organisation_id=organisation_id,
            query=request.query_params.get("q", "").strip(),
            steep_category=request.query_params.get("steep_category", "").strip(),
            time_horizon=request.query_params.get("time_horizon", "").strip(),
            maturity=request.query_params.get("maturity", "").strip(),
            status=request.query_params.get("status", "").strip(),
        )
        return Response(SignalSerializer(items, many=True, context={"request": request}).data)

    def post(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        serializer = SignalWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_signal(actor=request.user, organisation=organisation, **serializer.validated_data)
        return Response(
            SignalSerializer(item, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class SignalDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, signal_id):  # type: ignore[no-untyped-def]
        item = signal_for_user(user=request.user, signal_id=signal_id)
        return Response(SignalSerializer(item, context={"request": request}).data)

    def patch(self, request, signal_id):  # type: ignore[no-untyped-def]
        item = signal_for_user(user=request.user, signal_id=signal_id)
        serializer = SignalPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = update_signal(actor=request.user, signal=item, fields=dict(serializer.validated_data))
        return Response(SignalSerializer(item, context={"request": request}).data)


class SignalDecisionLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, signal_id):  # type: ignore[no-untyped-def]
        item = signal_for_user(user=request.user, signal_id=signal_id)
        serializer = SignalDecisionLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        link_signal_to_decision(actor=request.user, signal=item, **serializer.validated_data)
        item = signal_for_user(user=request.user, signal_id=signal_id)
        return Response(SignalSerializer(item, context={"request": request}).data)


class WatchlistListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        items = watchlists_for_organisation(user=request.user, organisation_id=organisation_id)
        return Response(WatchlistSerializer(items, many=True, context={"request": request}).data)

    def post(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        serializer = WatchlistWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_watchlist(actor=request.user, organisation=organisation, **serializer.validated_data)
        item.signal_count = 0
        return Response(
            WatchlistSerializer(item, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class WatchlistDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, watchlist_id):  # type: ignore[no-untyped-def]
        item = watchlist_for_user(user=request.user, watchlist_id=watchlist_id)
        return Response(WatchlistSerializer(item, context={"request": request}).data)

    def patch(self, request, watchlist_id):  # type: ignore[no-untyped-def]
        item = watchlist_for_user(user=request.user, watchlist_id=watchlist_id)
        serializer = WatchlistPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = update_watchlist(actor=request.user, watchlist=item, fields=dict(serializer.validated_data))
        item.signal_count = item.signal_links.count()
        return Response(WatchlistSerializer(item, context={"request": request}).data)


class WatchlistSignalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, watchlist_id):  # type: ignore[no-untyped-def]
        item = watchlist_for_user(user=request.user, watchlist_id=watchlist_id)
        serializer = WatchlistSignalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        add_signal_to_watchlist(actor=request.user, watchlist=item, **serializer.validated_data)
        item = watchlist_for_user(user=request.user, watchlist_id=watchlist_id)
        item.signal_count = item.signal_links.count()
        return Response(WatchlistSerializer(item, context={"request": request}).data)

    def delete(self, request, watchlist_id, signal_id):  # type: ignore[no-untyped-def]
        item = watchlist_for_user(user=request.user, watchlist_id=watchlist_id)
        remove_signal_from_watchlist(actor=request.user, watchlist=item, signal_id=signal_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
