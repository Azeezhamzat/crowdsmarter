from django.core.exceptions import ValidationError

from apps.core.api import exception_handler


def test_django_validation_error_is_translated_for_drf():
    response = exception_handler(ValidationError("Invalid domain state."), {})

    assert response is not None
    assert response.status_code == 400
    assert response.data == {"detail": ["Invalid domain state."]}
