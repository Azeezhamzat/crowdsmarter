from django.urls import path

from .views import DecisionOptionDetailView, DecisionOptionListCreateView

app_name = "decision_options"

urlpatterns = [
    path(
        "decisions/<uuid:decision_id>/options/",
        DecisionOptionListCreateView.as_view(),
        name="list-create",
    ),
    path(
        "decision-options/<uuid:option_id>/",
        DecisionOptionDetailView.as_view(),
        name="detail",
    ),
]
