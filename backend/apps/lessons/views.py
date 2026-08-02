"""Thin lesson and learning-completion endpoints."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.decisions.selectors import decision_for_user

from .selectors import lesson_for_user, lessons_for_decision
from .serializers import (
    ArchiveDecisionSerializer,
    LessonCreateSerializer,
    LessonSerializer,
    LessonUpdateSerializer,
)
from .services import archive_decision, create_lesson, retire_lesson, update_lesson


class LessonListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, decision_id):  # type: ignore[no-untyped-def]
        items = lessons_for_decision(user=request.user, decision_id=decision_id)
        return Response(LessonSerializer(items, many=True).data)

    def post(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        serializer = LessonCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lesson = create_lesson(
            actor=request.user,
            decision=decision,
            **serializer.validated_data,
        )
        return Response(LessonSerializer(lesson).data, status=status.HTTP_201_CREATED)


class LessonDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, lesson_id):  # type: ignore[no-untyped-def]
        lesson = lesson_for_user(user=request.user, lesson_id=lesson_id)
        serializer = LessonUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = update_lesson(
            actor=request.user,
            lesson=lesson,
            fields=dict(serializer.validated_data),
        )
        return Response(LessonSerializer(updated).data)

    def delete(self, request, lesson_id):  # type: ignore[no-untyped-def]
        lesson = lesson_for_user(user=request.user, lesson_id=lesson_id)
        retired = retire_lesson(actor=request.user, lesson=lesson)
        return Response(LessonSerializer(retired).data)


class DecisionArchiveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        serializer = ArchiveDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        archive_decision(
            actor=request.user,
            decision=decision,
            **serializer.validated_data,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
