from django.urls import path

from .views import OrganisationSearchView

app_name = "search"

urlpatterns = [
    path(
        "organisations/<uuid:organisation_id>/search/",
        OrganisationSearchView.as_view(),
        name="organisation-search",
    ),
]
