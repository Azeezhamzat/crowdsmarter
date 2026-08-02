"""Authentication backends for email-first CrowdSmarter accounts."""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

UserModel = get_user_model()


class CaseInsensitiveEmailBackend(ModelBackend):
    """Authenticate active accounts by normalised email, independent of DB collation."""

    def authenticate(  # type: ignore[no-untyped-def]
        self, request, username=None, password=None, **kwargs
    ):
        raw_email = kwargs.get("email") or username
        if not raw_email or password is None:
            return None

        normalised_email = str(raw_email).strip().lower()
        try:
            user = UserModel._default_manager.get(email__iexact=normalised_email)
        except UserModel.DoesNotExist:
            # Match Django's timing mitigation so missing accounts and wrong passwords
            # take broadly similar work.
            UserModel().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
