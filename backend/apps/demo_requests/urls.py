"""Public demo-request API route."""

from django.urls import path

from .views import DemoRequestCreateView

app_name = "demo_requests"

urlpatterns = [
    path("public/demo-requests/", DemoRequestCreateView.as_view(), name="create"),
]
