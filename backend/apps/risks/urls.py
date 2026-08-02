from django.urls import path

from .views import RiskDetailView, RiskListCreateView

app_name = "risks"

urlpatterns = [
    path("decisions/<uuid:decision_id>/risks/", RiskListCreateView.as_view(), name="list-create"),
    path("risks/<uuid:risk_id>/", RiskDetailView.as_view(), name="detail"),
]
