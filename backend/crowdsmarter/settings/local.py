"""Local development settings."""

import os

from .base import *  # noqa: F403

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-local-development-only")
MFA_ENCRYPTION_KEY = os.getenv("MFA_ENCRYPTION_KEY", "unsafe-local-mfa-encryption-only")
DEBUG = True
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] += [  # type: ignore[operator]  # noqa: F405
    "rest_framework.renderers.BrowsableAPIRenderer"
]
