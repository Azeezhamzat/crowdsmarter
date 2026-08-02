"""Authentication and account self-service API routes."""

from django.urls import path

from .views import (
    CsrfCookieView,
    CurrentUserView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    SessionLoginView,
    SessionLogoutView,
)

app_name = "accounts"

urlpatterns = [
    path("csrf/", CsrfCookieView.as_view(), name="csrf"),
    path("session/", SessionLoginView.as_view(), name="login"),
    path("session/logout/", SessionLogoutView.as_view(), name="logout"),
    path("me/", CurrentUserView.as_view(), name="me"),
    path("password/change/", PasswordChangeView.as_view(), name="password-change"),
    path("password/reset/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
]
