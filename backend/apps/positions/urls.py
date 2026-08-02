from django.urls import path

from .views import PositionHistoryView, PositionListCreateView

app_name = "positions"

urlpatterns = [
    path(
        "decisions/<uuid:decision_id>/positions/",
        PositionListCreateView.as_view(),
        name="list-create",
    ),
    path(
        "decisions/<uuid:decision_id>/positions/history/",
        PositionHistoryView.as_view(),
        name="history",
    ),
]
