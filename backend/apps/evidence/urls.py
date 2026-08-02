from django.urls import path

from .views import EvidenceDetailView, EvidenceListCreateView

app_name = "evidence"

urlpatterns = [
    path(
        "decisions/<uuid:decision_id>/evidence/",
        EvidenceListCreateView.as_view(),
        name="list-create",
    ),
    path("evidence/<uuid:evidence_id>/", EvidenceDetailView.as_view(), name="detail"),
]
