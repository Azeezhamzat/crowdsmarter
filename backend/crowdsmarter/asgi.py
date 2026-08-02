"""ASGI config for The CrowdSmarter."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crowdsmarter.settings.production")
application = get_asgi_application()
