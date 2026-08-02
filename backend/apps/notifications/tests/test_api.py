import pytest
from django.urls import reverse

from apps.notifications.models import Notification
from apps.notifications.services import create_notification


@pytest.mark.django_db
def test_notification_inbox_is_private_and_can_be_marked_read(
    api_client, user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    recipient = user_factory()
    outsider = user_factory()
    organisation = organisation_factory(owner=recipient)
    notification = create_notification(
        recipient=recipient,
        organisation=organisation,
        kind=Notification.Kind.SYSTEM,
        title="Private message",
        message="Only the recipient may read this.",
    )
    api_client.force_authenticate(recipient)
    response = api_client.get(reverse("notifications:list"))
    assert response.status_code == 200
    assert response.json()["unread_count"] == 1
    assert response.json()["notifications"][0]["id"] == str(notification.id)

    read_url = reverse("notifications:read", kwargs={"notification_id": notification.id})
    assert api_client.post(read_url, {}, format="json").status_code == 200
    notification.refresh_from_db()
    assert notification.read_at is not None

    second = create_notification(
        recipient=recipient,
        organisation=organisation,
        kind=Notification.Kind.SYSTEM,
        title="Second private message",
        message="Mark all should cover this item.",
    )
    assert api_client.post(reverse("notifications:read-all"), {}, format="json").status_code == 200
    second.refresh_from_db()
    assert second.read_at is not None

    api_client.force_authenticate(outsider)
    assert api_client.post(read_url, {}, format="json").status_code == 404
