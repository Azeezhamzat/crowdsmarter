"""Authentication and account self-service API routes."""

from django.urls import path

from .views import (
    CsrfCookieView,
    CurrentUserView,
    EmailChangeConfirmView,
    EmailChangeRequestView,
    MFADisableView,
    MFAEnrollBeginView,
    MFAEnrollConfirmView,
    MFAStatusView,
    MFAVerifyView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    SessionLoginView,
    SessionLogoutView,
    SignupView,
)

app_name = "accounts"

urlpatterns = [
    path("csrf/", CsrfCookieView.as_view(), name="csrf"),
    path("signup/", SignupView.as_view(), name="signup"),
    path("session/", SessionLoginView.as_view(), name="login"),
    path("session/logout/", SessionLogoutView.as_view(), name="logout"),
    path("me/", CurrentUserView.as_view(), name="me"),
    path("password/change/", PasswordChangeView.as_view(), name="password-change"),
    path("email/change/", EmailChangeRequestView.as_view(), name="email-change-request"),
    path(
        "email/change/confirm/",
        EmailChangeConfirmView.as_view(),
        name="email-change-confirm",
    ),
    path("password/reset/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path(
        "password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"
    ),
    path("mfa/verify/", MFAVerifyView.as_view(), name="mfa-verify"),
    path("mfa/status/", MFAStatusView.as_view(), name="mfa-status"),
    path("mfa/enroll/begin/", MFAEnrollBeginView.as_view(), name="mfa-enroll-begin"),
    path("mfa/enroll/confirm/", MFAEnrollConfirmView.as_view(), name="mfa-enroll-confirm"),
    path("mfa/disable/", MFADisableView.as_view(), name="mfa-disable"),
]
