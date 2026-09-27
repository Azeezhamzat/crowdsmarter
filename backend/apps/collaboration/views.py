"""Thin collaboration and decision-activity endpoints."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.decisions.selectors import decision_for_user

from .policies import can_contribute
from .selectors import (
    audit_events_for_decision,
    discussion_entry_for_user,
    discussion_for_decision,
)
from .serializers import (
    DecisionActivityItemSerializer,
    DiscussionEntryCreateSerializer,
    DiscussionEntrySerializer,
    DiscussionResolveSerializer,
)
from .services import create_discussion_entry, resolve_discussion_entry


class DecisionDiscussionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, decision_id):  # type: ignore[no-untyped-def]
        entries = discussion_for_decision(user=request.user, decision_id=decision_id)
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        return Response(
            {
                "can_contribute": can_contribute(actor=request.user, decision=decision),
                "entries": DiscussionEntrySerializer(
                    entries,
                    many=True,
                    context={"request": request},
                ).data,
            }
        )

    def post(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        serializer = DiscussionEntryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reply_to_id = serializer.validated_data.pop("reply_to_id", None)
        reply_to = None
        if reply_to_id:
            reply_to = discussion_entry_for_user(
                user=request.user,
                entry_id=reply_to_id,
            )
        entry = create_discussion_entry(
            actor=request.user,
            decision=decision,
            reply_to=reply_to,
            **serializer.validated_data,
        )
        return Response(
            DiscussionEntrySerializer(entry, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class DiscussionEntryResolveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, entry_id):  # type: ignore[no-untyped-def]
        entry = discussion_entry_for_user(user=request.user, entry_id=entry_id)
        serializer = DiscussionResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry = resolve_discussion_entry(
            actor=request.user,
            entry=entry,
            **serializer.validated_data,
        )
        return Response(DiscussionEntrySerializer(entry, context={"request": request}).data)


class DecisionActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        audit_items = [
            {
                "id": str(event.id),
                "source": "audit",
                "action": event.action,
                "title": event.action.replace(".", " ").replace("_", " ").title(),
                "actor": event.actor,
                "created_at": event.created_at,
                "url": f"/decisions/{decision.id}",
                "metadata": event.metadata,
            }
            for event in audit_events_for_decision(
                user=request.user,
                decision_id=decision.id,
            )[:150]
        ]
        discussion_items = [
            {
                "id": str(entry.id),
                "source": "discussion",
                "action": f"collaboration.{entry.kind}",
                "title": f"{entry.get_kind_display()} added",
                "actor": entry.author,
                "created_at": entry.created_at,
                "url": f"/decisions/{decision.id}/collaboration#entry-{entry.id}",
                "metadata": {
                    "discussion_entry_id": str(entry.id),
                    "kind": entry.kind,
                    "is_resolved": entry.is_resolved,
                    "body_excerpt": entry.body[:240],
                },
            }
            for entry in discussion_for_decision(
                user=request.user,
                decision_id=decision.id,
            )
        ]
        items = sorted(
            audit_items + discussion_items,
            key=lambda item: item["created_at"],
            reverse=True,
        )[:200]
        return Response(DecisionActivityItemSerializer(items, many=True).data)
