from django.urls import path

from .views import (
    LookupApiKeyView,
    LookupConfigurationView,
    LookupConnectionTestView,
    LookupOrganisationView,
)

app_name = "org_enrichment"

urlpatterns = [
    path(
        "organisations/<uuid:organisation_id>/lookup-configuration/",
        LookupConfigurationView.as_view(),
        name="configuration",
    ),
    path(
        "organisations/<uuid:organisation_id>/lookup-configuration/api-key/",
        LookupApiKeyView.as_view(),
        name="api-key",
    ),
    path(
        "organisations/<uuid:organisation_id>/lookup-configuration/test-connection/",
        LookupConnectionTestView.as_view(),
        name="test-connection",
    ),
    path(
        "organisations/<uuid:organisation_id>/lookup-organisation/",
        LookupOrganisationView.as_view(),
        name="lookup",
    ),
]
