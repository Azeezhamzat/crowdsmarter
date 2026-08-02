from django.urls import path

from .views import OrganisationPortfolioView, PersonalWorkView

app_name = "portfolio"

urlpatterns = [
    path("me/work/", PersonalWorkView.as_view(), name="personal-work"),
    path(
        "organisations/<uuid:organisation_id>/portfolio/",
        OrganisationPortfolioView.as_view(),
        name="organisation-portfolio",
    ),
]
