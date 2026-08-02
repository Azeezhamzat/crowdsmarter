"""Authentication API routes."""

from django.urls import path

from .views import CsrfCookieView, CurrentUserView, SessionLoginView, SessionLogoutView

app_name = "accounts"

urlpatterns = [
    path("csrf/", CsrfCookieView.as_view(), name="csrf"),
    path("session/", SessionLoginView.as_view(), name="login"),
    path("session/logout/", SessionLogoutView.as_view(), name="logout"),
    path("me/", CurrentUserView.as_view(), name="me"),
]
