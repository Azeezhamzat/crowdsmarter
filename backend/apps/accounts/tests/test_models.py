import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_user_manager_normalises_email():
    user = User.objects.create_user(email="Person@EXAMPLE.COM", password="password-123")
    assert user.email == "person@example.com"
    assert user.check_password("password-123")
    assert user.username is None


@pytest.mark.django_db
def test_superuser_requires_staff_and_superuser_flags():
    with pytest.raises(ValueError, match="is_staff"):
        User.objects.create_superuser(
            email="admin@example.com",
            password="password-123",
            is_staff=False,
        )
