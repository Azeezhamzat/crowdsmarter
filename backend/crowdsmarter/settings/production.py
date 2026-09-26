"""Production settings with fail-fast security validation."""

import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = False

if not SECRET_KEY:  # noqa: F405
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set in production.")
if not MFA_ENCRYPTION_KEY:  # noqa: F405
    raise ImproperlyConfigured("MFA_ENCRYPTION_KEY must be set in production.")
if MFA_ENCRYPTION_KEY == SECRET_KEY:  # noqa: F405
    raise ImproperlyConfigured("MFA_ENCRYPTION_KEY must be distinct from DJANGO_SECRET_KEY.")
if not os.getenv("DJANGO_ALLOWED_HOSTS"):
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must be set in production.")
if not os.getenv("DATABASE_URL"):
    raise ImproperlyConfigured("DATABASE_URL must be set in production.")
if STORAGE_BACKEND == "s3" and not AWS_STORAGE_BUCKET_NAME:  # noqa: F405
    raise ImproperlyConfigured("AWS_STORAGE_BUCKET_NAME is required for S3 storage.")

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)  # noqa: F405
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "31536000"))  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
