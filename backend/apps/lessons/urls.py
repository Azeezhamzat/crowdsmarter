from django.urls import path

from .views import DecisionArchiveView, LessonDetailView, LessonListCreateView

app_name = "lessons"

urlpatterns = [
    path(
        "decisions/<uuid:decision_id>/lessons/",
        LessonListCreateView.as_view(),
        name="list-create",
    ),
    path("lessons/<uuid:lesson_id>/", LessonDetailView.as_view(), name="detail"),
    path(
        "decisions/<uuid:decision_id>/archive/",
        DecisionArchiveView.as_view(),
        name="archive",
    ),
]
