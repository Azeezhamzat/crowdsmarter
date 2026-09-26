from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.foresight.malware import MalwareScannerError, scan_upload
from apps.foresight.models import SourceAttachment


class Command(BaseCommand):
    help = "Scan legacy or non-clean source attachments; use --apply to save results."

    def add_arguments(self, parser) -> None:  # type: ignore[no-untyped-def]
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Persist scan results. The default is a non-mutating preview.",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Rescan clean attachments as well as unresolved attachments.",
        )

    def handle(self, *args, **options) -> None:  # type: ignore[no-untyped-def]
        apply_results = bool(options["apply"])
        attachments = SourceAttachment.objects.order_by("created_at")
        if not options["all"]:
            attachments = attachments.exclude(malware_scan_status=SourceAttachment.ScanStatus.CLEAN)

        totals = {"clean": 0, "infected": 0, "error": 0}
        for attachment in attachments.iterator():
            try:
                with attachment.file.open("rb") as upload:
                    result = scan_upload(upload)
                status = result.status
                engine = result.engine
            except (FileNotFoundError, OSError, MalwareScannerError):
                status = SourceAttachment.ScanStatus.ERROR
                engine = "scan-error"

            if status not in totals:
                status = SourceAttachment.ScanStatus.ERROR
                engine = "untrusted-result"
            totals[status] += 1
            self.stdout.write(f"{attachment.id} {status} ({engine})")

            if apply_results:
                attachment.malware_scan_status = status
                attachment.malware_scan_engine = engine
                attachment.malware_scanned_at = timezone.now()
                attachment.save(
                    update_fields=[
                        "malware_scan_status",
                        "malware_scan_engine",
                        "malware_scanned_at",
                        "updated_at",
                    ]
                )

        mode = "APPLIED" if apply_results else "PREVIEW"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: clean={totals['clean']} infected={totals['infected']} "
                f"error={totals['error']}"
            )
        )
        if totals["infected"] or totals["error"]:
            raise CommandError("One or more attachments are infected or could not be scanned.")
