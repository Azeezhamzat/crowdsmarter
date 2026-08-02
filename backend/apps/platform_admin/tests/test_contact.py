import pytest

from apps.platform_admin.contact import notification_sender_email
from apps.platform_admin.models import PlatformConfiguration


@pytest.mark.django_db
def test_notification_sender_uses_platform_configuration():
    configuration = PlatformConfiguration.load()
    configuration.notification_sender_email = "notifications@crowdsmarter.com"
    configuration.save(update_fields=["notification_sender_email", "updated_at"])

    assert notification_sender_email() == "notifications@crowdsmarter.com"
