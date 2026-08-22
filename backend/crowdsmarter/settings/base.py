"""Shared Django settings for all environments."""

from __future__ import annotations

import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parents[2]


def env_bool(name: str, default: bool = False) -> bool:
    """Read a boolean environment variable using explicit truthy values."""
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    """Read a comma-separated environment variable."""
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,backend")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.core",
    "apps.accounts",
    "apps.organisations",
    "apps.invitations",
    "apps.audit",
    "apps.workspaces",
    "apps.decisions",
    "apps.participants",
    "apps.positions",
    "apps.decision_options",
    "apps.evidence",
    "apps.assumptions",
    "apps.risks",
    "apps.criteria",
    "apps.reviews",
    "apps.lessons",
    "apps.search",
    "apps.notifications",
    "apps.ai_assistance",
    "apps.analytics",
    "apps.collaboration",
    "apps.portfolio",
    "apps.exports",
    "apps.foresight",
    "apps.evaluations",
    "apps.decision_analysis",
    "apps.demo_requests",
    "apps.contributions",
    "apps.methodology",
    "apps.platform_admin",
    "apps.billing",
    "apps.ideation",
    "apps.applicants",
    "apps.disbursements",
    "apps.org_enrichment",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "crowdsmarter.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "crowdsmarter.wsgi.application"
ASGI_APPLICATION = "crowdsmarter.asgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default="postgresql://crowdsmarter:crowdsmarter@localhost:5432/crowdsmarter",
        conn_max_age=60,
        conn_health_checks=True,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["apps.accounts.backends.CaseInsensitiveEmailBackend"]

LANGUAGE_CODE = "en-gb"
LANGUAGES = [
    ("en-gb", "English"),
    ("fr", "Français"),
    ("pt", "Português"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.getenv("API_ANON_THROTTLE_RATE", "60/min"),
        "user": os.getenv("API_USER_THROTTLE_RATE", "600/min"),
        "login": os.getenv("API_LOGIN_THROTTLE_RATE", "10/min"),
        "password_reset_request": os.getenv("API_PASSWORD_RESET_REQUEST_THROTTLE_RATE", "5/hour"),
        "password_reset_confirm": os.getenv("API_PASSWORD_RESET_CONFIRM_THROTTLE_RATE", "20/hour"),
        "account_security": os.getenv("API_ACCOUNT_SECURITY_THROTTLE_RATE", "20/hour"),
        "mfa_verify": os.getenv("API_MFA_VERIFY_THROTTLE_RATE", "10/min"),
        "data_export": os.getenv("API_DATA_EXPORT_THROTTLE_RATE", "20/hour"),
        "invitation_management": os.getenv("API_INVITATION_MANAGEMENT_THROTTLE_RATE", "120/hour"),
        "invitation_acceptance": os.getenv("API_INVITATION_ACCEPTANCE_THROTTLE_RATE", "60/hour"),
        "ai_review": os.getenv("API_AI_REVIEW_THROTTLE_RATE", "20/hour"),
        "analytics_insights": os.getenv("API_ANALYTICS_INSIGHTS_THROTTLE_RATE", "30/hour"),
        "foresight_feed_sync": os.getenv("API_FORESIGHT_FEED_SYNC_THROTTLE_RATE", "20/hour"),
        "demo_request": os.getenv("API_DEMO_REQUEST_THROTTLE_RATE", "5/hour"),
        "session_join": os.getenv("API_SESSION_JOIN_THROTTLE_RATE", "20/hour"),
        "idea_submit": os.getenv("API_IDEA_SUBMIT_THROTTLE_RATE", "30/hour"),
        "idea_vote": os.getenv("API_IDEA_VOTE_THROTTLE_RATE", "120/hour"),
        "idea_comment": os.getenv("API_IDEA_COMMENT_THROTTLE_RATE", "60/hour"),
        "applicant_magic_link": os.getenv("API_APPLICANT_MAGIC_LINK_THROTTLE_RATE", "10/hour"),
        "applicant_magic_link_consume": os.getenv("API_APPLICANT_MAGIC_LINK_CONSUME_THROTTLE_RATE", "20/hour"),
        "applicant_progress_report": os.getenv("API_APPLICANT_PROGRESS_REPORT_THROTTLE_RATE", "30/hour"),
    },
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "EXCEPTION_HANDLER": "apps.core.api.exception_handler",
}

EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
PUBLIC_CONTACT_EMAIL = os.getenv("PUBLIC_CONTACT_EMAIL", "hello@crowdsmarter.com").strip()
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", PUBLIC_CONTACT_EMAIL).strip()
PRIVACY_EMAIL = os.getenv("PRIVACY_EMAIL", PUBLIC_CONTACT_EMAIL).strip()
SECURITY_EMAIL = os.getenv("SECURITY_EMAIL", PUBLIC_CONTACT_EMAIL).strip()
PLATFORM_ADMIN_EMAIL = os.getenv("PLATFORM_ADMIN_EMAIL", PUBLIC_CONTACT_EMAIL).strip()
DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL", f"CrowdSmarter <{PUBLIC_CONTACT_EMAIL}>"
).strip()
EMAIL_REPLY_TO = os.getenv("EMAIL_REPLY_TO", PUBLIC_CONTACT_EMAIL).strip()
DEMO_REQUEST_RECIPIENT = os.getenv("DEMO_REQUEST_RECIPIENT", PUBLIC_CONTACT_EMAIL).strip()
DEMO_REQUEST_SEND_ACKNOWLEDGEMENT = env_bool(
    "DEMO_REQUEST_SEND_ACKNOWLEDGEMENT", False
)
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")
INVITATION_EXPIRY_HOURS = int(os.getenv("INVITATION_EXPIRY_HOURS", "168"))
PASSWORD_RESET_TIMEOUT = int(os.getenv("PASSWORD_RESET_TIMEOUT", "3600"))
MFA_PENDING_SESSION_SECONDS = int(os.getenv("MFA_PENDING_SESSION_SECONDS", "300"))

SOURCE_ATTACHMENT_MAX_BYTES = int(os.getenv("SOURCE_ATTACHMENT_MAX_BYTES", str(15 * 1024 * 1024)))
SOURCE_ATTACHMENT_ALLOWED_CONTENT_TYPES = env_list(
    "SOURCE_ATTACHMENT_ALLOWED_CONTENT_TYPES",
    "application/pdf,text/plain,text/csv,application/csv,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,image/png,image/jpeg,image/webp",
)
SOURCE_ATTACHMENT_ALLOWED_EXTENSIONS = env_list(
    "SOURCE_ATTACHMENT_ALLOWED_EXTENSIONS",
    ".pdf,.txt,.csv,.docx,.xlsx,.png,.jpg,.jpeg,.webp",
)

AI_PROVIDER_BACKEND = os.getenv(
    "AI_PROVIDER_BACKEND",
    "apps.ai_assistance.providers.rules.RuleBasedAIProvider",
)


CACHE_URL = os.getenv("CACHE_URL", "")
if CACHE_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": CACHE_URL,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "crowdsmarter-local-cache",
        }
    }

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_TRACK_STARTED = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BEAT_SCHEDULE = {
    "send-due-review-notifications-daily": {
        "task": "apps.notifications.tasks.send_due_review_notifications",
        "schedule": 86400.0,
    },
    "send-signpost-watchlist-notifications-daily": {
        "task": "apps.notifications.tasks.send_signpost_watchlist_notifications",
        "schedule": 86400.0,
    },
    "send-contribution-reminders-and-digests-daily": {
        "task": "apps.contributions.tasks.send_contribution_reminders_and_digests",
        "schedule": 86400.0,
    },
}

STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local").lower()
if STORAGE_BACKEND == "s3":
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3.S3Storage"},
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        },
    }
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME", "")
    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL", "")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "")
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = True
else:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        },
    }

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        }
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "verbose"}},
    "root": {"handlers": ["console"], "level": os.getenv("LOG_LEVEL", "INFO")},
}
