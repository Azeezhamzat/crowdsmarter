from django.urls import path

from .views import AssumptionDetailView, AssumptionListCreateView

app_name = "assumptions"

urlpatterns = [
    path(
        "decisions/<uuid:decision_id>/assumptions/",
        AssumptionListCreateView.as_view(),
        name="list-create",
    ),
    path("assumptions/<uuid:assumption_id>/", AssumptionDetailView.as_view(), name="detail"),
]
