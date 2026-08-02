"""WSGI config for The CrowdSmarter."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crowdsmarter.settings.production")
application = get_wsgi_application()
