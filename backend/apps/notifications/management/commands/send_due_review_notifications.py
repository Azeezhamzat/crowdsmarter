from django.core.management.base import BaseCommand

from apps.notifications.services import deliver_due_review_notifications


class Command(BaseCommand):
    help = "Create in-app notifications for outcome reviews that are due."

    def handle(self, *args, **options):  # type: ignore[no-untyped-def]
        delivered = deliver_due_review_notifications()
        self.stdout.write(self.style.SUCCESS(f"Created {delivered} due-review notification(s)."))
