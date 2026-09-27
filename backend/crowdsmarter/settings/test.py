"""Fast, deterministic test settings."""

import os

from .base import *  # noqa: F403

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "test-only-secret")
MFA_ENCRYPTION_KEY = os.getenv("MFA_ENCRYPTION_KEY", "test-only-mfa-encryption-key")
DEBUG = False
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
ENABLE_METRICS_ENDPOINT = True
SOURCE_ATTACHMENT_MALWARE_SCANNER = "test"
SOURCE_ATTACHMENT_MALWARE_FAIL_CLOSED = True
SOURCE_ATTACHMENT_ENFORCE_CLEAN_DOWNLOADS = False

if "DATABASE_URL" not in os.environ:
    DATABASES = {  # noqa: F405
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
