"""Fast, deterministic test settings."""

import os

from .base import *  # noqa: F403

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "test-only-secret")
DEBUG = False
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

if "DATABASE_URL" not in os.environ:
    DATABASES = {  # noqa: F405
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
