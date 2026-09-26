"""Preview retention candidates; intentionally performs no deletion."""

import json

from django.core.management.base import BaseCommand, CommandError

from apps.organisations.retention import retention_report


class Command(BaseCommand):
    help = "Preview pending organisation deletions without changing customer data."

    def add_arguments(self, parser):  # type: ignore[no-untyped-def]
        parser.add_argument("--json", action="store_true", dest="as_json")
        parser.add_argument("--fail-if-due", action="store_true")

    def handle(self, *args, **options):  # type: ignore[no-untyped-def]
        rows = retention_report()
        if options["as_json"]:
            self.stdout.write(json.dumps(rows, indent=2, sort_keys=True))
        elif not rows:
            self.stdout.write("No pending organisation deletion requests.")
        else:
            for row in rows:
                state = "DUE" if row["due"] else "waiting"
                blockers = ",".join(row["blockers"]) or "none"
                self.stdout.write(
                    f"{state} {row['request_id']} {row['organisation_name']} "
                    f"earliest={row['earliest_deletion_at']} blockers={blockers}"
                )
        due = [row for row in rows if row["eligible_for_manual_review"]]
        if due and options["fail_if_due"]:
            raise CommandError(f"{len(due)} deletion request(s) require manual review.")
