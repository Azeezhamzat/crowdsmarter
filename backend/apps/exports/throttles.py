"""Rate limits for potentially expensive customer exports."""

from rest_framework.throttling import UserRateThrottle


class ExportRateThrottle(UserRateThrottle):
    """Limit repeated synchronous export generation."""

    scope = "data_export"
