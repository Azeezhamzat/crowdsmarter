"""Abuse controls for the public demo-request endpoint."""

from rest_framework.throttling import AnonRateThrottle


class DemoRequestThrottle(AnonRateThrottle):
    """Limit repeated anonymous submissions from one network address."""

    scope = "demo_request"
