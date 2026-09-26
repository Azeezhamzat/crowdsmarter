from django.urls import path

from .views import (
    DisbursementApiKeyView,
    DisbursementConfigurationView,
    DisbursementConnectionTestView,
    OptionDisbursementListCreateView,
)

app_name = "disbursements"

urlpatterns = [
    path(
        "organisations/<uuid:organisation_id>/disbursement-configuration/",
        DisbursementConfigurationView.as_view(),
        name="configuration",
    ),
    path(
        "organisations/<uuid:organisation_id>/disbursement-configuration/api-key/",
        DisbursementApiKeyView.as_view(),
        name="api-key",
    ),
    path(
        "organisations/<uuid:organisation_id>/disbursement-configuration/test-connection/",
        DisbursementConnectionTestView.as_view(),
        name="test-connection",
    ),
    path(
        "decision-options/<uuid:option_id>/disbursements/",
        OptionDisbursementListCreateView.as_view(),
        name="option-disbursements",
    ),
]
