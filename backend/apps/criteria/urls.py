from django.urls import path

from .views import CriterionDetailView, CriterionListCreateView

app_name = "criteria"

urlpatterns = [
    path("decisions/<uuid:decision_id>/criteria/", CriterionListCreateView.as_view(), name="list-create"),
    path("criteria/<uuid:criterion_id>/", CriterionDetailView.as_view(), name="detail"),
]
