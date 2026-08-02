"""Shared REST API exception translation."""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):  # type: ignore[no-untyped-def]
    """Translate domain validation failures without coupling services to DRF."""
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            exc = DRFValidationError(exc.message_dict)
        else:
            exc = DRFValidationError({"detail": exc.messages})
    return drf_exception_handler(exc, context)
