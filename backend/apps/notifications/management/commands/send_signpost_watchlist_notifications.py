from django.core.management.base import BaseCommand

from apps.notifications.services import deliver_signpost_watchlist_notifications


class Command(BaseCommand):
    help = "Create in-app notifications for signpost movements and overdue signpost reviews."

    def handle(self, *args, **options):  # type: ignore[no-untyped-def]
        delivered = deliver_signpost_watchlist_notifications()
        self.stdout.write(
            self.style.SUCCESS(f"Created {delivered} signpost-watchlist notification(s).")
        )
