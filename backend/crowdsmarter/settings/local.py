"""Local development settings."""

import os

from .base import *  # noqa: F403

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-local-development-only")
DEBUG = True
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] += [  # noqa: F405
    "rest_framework.renderers.BrowsableAPIRenderer"
]
