"""Transactional foresight workflows."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.services import record_event
from apps.decisions.models import Decision
from apps.organisations.models import Membership, Organisation

from .feeds import FeedFetchError, fetch_feed, validate_public_feed_url
from .malware import MalwareScannerError, scan_upload
from .models import (
    FeedSubscription,
    ResearchClaim,
    ResearchClaimSource,
    Signal,
    SignalDecisionLink,
    Source,
    SourceAttachment,
    Watchlist,
    WatchlistSignal,
)
from .policies import can_contribute, can_manage_record

logger = logging.getLogger(__name__)


class ForesightServiceError(ValidationError):
    """Expected foresight workflow failure."""


def _active_member(*, organisation: Organisation, user_id: Any) -> User:
    try:
        membership = Membership.objects.select_related("user").get(
            organisation=organisation,
            user_id=user_id,
            status=Membership.Status.ACTIVE,
        )
    except Membership.DoesNotExist as exc:
        raise ForesightServiceError({"owner_id": "Choose an active organisation member."}) from exc
    return membership.user


def _source(*, organisation: Organisation, source_id: Any | None) -> Source | None:
    if source_id is None:
        return None
    try:
        return Source.objects.get(id=source_id, organisation=organisation)
    except Source.DoesNotExist as exc:
        raise ForesightServiceError(
            {"source_id": "The source does not belong to this organisation."}
        ) from exc


def _supersedes(*, organisation: Organisation, source_id: Any | None) -> Source | None:
    if source_id is None:
        return None
    try:
        return Source.objects.get(id=source_id, organisation=organisation)
    except Source.DoesNotExist as exc:
        raise ForesightServiceError(
            {"supersedes_id": "The earlier source does not belong to this organisation."}
        ) from exc


def _decision(*, organisation: Organisation, decision_id: Any | None) -> Decision | None:
    if decision_id is None:
        return None
    try:
        return Decision.objects.get(id=decision_id, organisation=organisation)
    except Decision.DoesNotExist as exc:
        raise ForesightServiceError(
            {"linked_decision_id": "The decision does not belong to this organisation."}
        ) from exc


@transaction.atomic
def create_source(*, actor: User, organisation: Organisation, **fields: Any) -> Source:
    if not can_contribute(actor=actor, organisation=organisation):
        raise PermissionDenied("You cannot add sources to this organisation.")
    supersedes_id = fields.pop("supersedes_id", None)
    if fields.get("credibility", Source.Credibility.UNASSESSED) != Source.Credibility.UNASSESSED:
        fields["last_verified_at"] = timezone.now()
    source = Source(
        organisation=organisation,
        created_by=actor,
        supersedes=_supersedes(organisation=organisation, source_id=supersedes_id),
        **fields,
    )
    source.full_clean(validate_unique=False, validate_constraints=False)
    source.save()
    record_event(
        action="foresight.source.created",
        object_type="foresight_source",
        object_id=str(source.id),
        actor=actor,
        organisation=organisation,
        metadata={"title": source.title, "source_type": source.source_type},
    )
    return source


@transaction.atomic
def update_source(*, actor: User, source: Source, fields: dict[str, Any]) -> Source:
    source = Source.objects.select_for_update().select_related("organisation").get(id=source.id)
    if not can_manage_record(
        actor=actor, organisation=source.organisation, created_by_id=source.created_by_id
    ):
        raise PermissionDenied("You cannot edit this source.")
    before = {key: getattr(source, key) for key in fields if key != "supersedes_id"}
    if "supersedes_id" in fields:
        source.supersedes = _supersedes(
            organisation=source.organisation, source_id=fields.pop("supersedes_id")
        )
    verification_fields = {
        "source_url",
        "archived_url",
        "reference",
        "credibility",
        "credibility_rationale",
        "status",
    }
    if verification_fields.intersection(fields):
        source.last_verified_at = timezone.now()
    for key, value in fields.items():
        setattr(source, key, value)
    source.full_clean(validate_unique=False, validate_constraints=False)
    source.save()
    record_event(
        action="foresight.source.updated",
        object_type="foresight_source",
        object_id=str(source.id),
        actor=actor,
        organisation=source.organisation,
        metadata={"before": before, "status": source.status},
    )
    return source


@transaction.atomic
def create_research_claim(
    *, actor: User, organisation: Organisation, **fields: Any
) -> ResearchClaim:
    """Create a scored, reviewable claim without silently asserting that it is true."""
    if not can_contribute(actor=actor, organisation=organisation):
        raise PermissionDenied("You cannot add research claims to this organisation.")
    owner = _active_member(organisation=organisation, user_id=fields.pop("owner_id", actor.id))
    decision = _decision(
        organisation=organisation, decision_id=fields.pop("linked_decision_id", None)
    )
    if fields.get("state", ResearchClaim.State.UNKNOWN) != ResearchClaim.State.UNKNOWN:
        fields["last_reviewed_at"] = timezone.now()
    claim = ResearchClaim(
        organisation=organisation,
        owner=owner,
        created_by=actor,
        linked_decision=decision,
        **fields,
    )
    claim.full_clean(validate_unique=False, validate_constraints=False)
    claim.save()
    record_event(
        action="foresight.research_claim.created",
        object_type="foresight_research_claim",
        object_id=str(claim.id),
        actor=actor,
        organisation=organisation,
        metadata={
            "state": claim.state,
            "recommendation": claim.recommendation,
            "evidence_score": claim.evidence_score,
        },
    )
    return claim


@transaction.atomic
def update_research_claim(
    *, actor: User, claim: ResearchClaim, fields: dict[str, Any]
) -> ResearchClaim:
    claim = (
        ResearchClaim.objects.select_for_update()
        .select_related("organisation", "owner")
        .get(id=claim.id)
    )
    if not can_manage_record(
        actor=actor,
        organisation=claim.organisation,
        created_by_id=claim.created_by_id,
        owner_id=claim.owner_id,
    ):
        raise PermissionDenied("You cannot edit this research claim.")
    before = {
        "state": claim.state,
        "recommendation": claim.recommendation,
        "evidence_score": claim.evidence_score,
        "lifecycle_status": claim.lifecycle_status,
    }
    if "owner_id" in fields:
        claim.owner = _active_member(
            organisation=claim.organisation, user_id=fields.pop("owner_id")
        )
    if "linked_decision_id" in fields:
        claim.linked_decision = _decision(
            organisation=claim.organisation,
            decision_id=fields.pop("linked_decision_id"),
        )
    review_fields = {
        "state",
        "evidence_summary",
        "limitations",
        "authority_score",
        "directness_score",
        "recency_score",
        "triangulation_score",
    }
    if review_fields.intersection(fields):
        claim.last_reviewed_at = timezone.now()
    for key, value in fields.items():
        setattr(claim, key, value)
    claim.full_clean(validate_unique=False, validate_constraints=False)
    claim.save()
    record_event(
        action="foresight.research_claim.updated",
        object_type="foresight_research_claim",
        object_id=str(claim.id),
        actor=actor,
        organisation=claim.organisation,
        metadata={
            "before": before,
            "state": claim.state,
            "recommendation": claim.recommendation,
            "evidence_score": claim.evidence_score,
            "lifecycle_status": claim.lifecycle_status,
        },
    )
    return claim


@transaction.atomic
def link_source_to_research_claim(
    *,
    actor: User,
    claim: ResearchClaim,
    source_id: Any,
    relationship: str,
    note: str = "",
) -> ResearchClaimSource:
    claim = (
        ResearchClaim.objects.select_for_update().select_related("organisation").get(id=claim.id)
    )
    if not can_manage_record(
        actor=actor,
        organisation=claim.organisation,
        created_by_id=claim.created_by_id,
        owner_id=claim.owner_id,
    ):
        raise PermissionDenied("You cannot edit this research claim.")
    source = _source(organisation=claim.organisation, source_id=source_id)
    assert source is not None
    link, created = ResearchClaimSource.objects.update_or_create(
        claim=claim,
        source=source,
        defaults={"relationship": relationship, "note": note, "linked_by": actor},
    )
    link.full_clean(validate_unique=False, validate_constraints=False)
    link.save()
    record_event(
        action=(
            "foresight.research_claim.source_linked"
            if created
            else "foresight.research_claim.source_updated"
        ),
        object_type="foresight_research_claim",
        object_id=str(claim.id),
        actor=actor,
        organisation=claim.organisation,
        metadata={
            "source_id": str(source.id),
            "relationship": relationship,
        },
    )
    return link


@transaction.atomic
def unlink_source_from_research_claim(*, actor: User, claim: ResearchClaim, source_id: Any) -> None:
    claim = (
        ResearchClaim.objects.select_for_update().select_related("organisation").get(id=claim.id)
    )
    if not can_manage_record(
        actor=actor,
        organisation=claim.organisation,
        created_by_id=claim.created_by_id,
        owner_id=claim.owner_id,
    ):
        raise PermissionDenied("You cannot edit this research claim.")
    try:
        link = ResearchClaimSource.objects.get(claim=claim, source_id=source_id)
    except ResearchClaimSource.DoesNotExist as exc:
        raise ForesightServiceError(
            {"source_id": "This source is not linked to the research claim."}
        ) from exc
    link.delete()
    record_event(
        action="foresight.research_claim.source_unlinked",
        object_type="foresight_research_claim",
        object_id=str(claim.id),
        actor=actor,
        organisation=claim.organisation,
        metadata={"source_id": str(source_id)},
    )


def _validate_upload(upload) -> tuple[int, str, str]:  # type: ignore[no-untyped-def]
    max_bytes = int(getattr(settings, "SOURCE_ATTACHMENT_MAX_BYTES", 15 * 1024 * 1024))
    allowed_types = set(
        getattr(
            settings,
            "SOURCE_ATTACHMENT_ALLOWED_CONTENT_TYPES",
            [
                "application/pdf",
                "text/plain",
                "text/csv",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "image/png",
                "image/jpeg",
                "image/webp",
            ],
        )
    )
    allowed_extensions = set(
        getattr(
            settings,
            "SOURCE_ATTACHMENT_ALLOWED_EXTENSIONS",
            [".pdf", ".txt", ".csv", ".docx", ".xlsx", ".png", ".jpg", ".jpeg", ".webp"],
        )
    )
    name = Path(upload.name).name
    suffix = Path(name).suffix.lower()
    content_type = (getattr(upload, "content_type", "") or "application/octet-stream").lower()
    size = int(getattr(upload, "size", 0))
    if size <= 0:
        raise ForesightServiceError({"file": "The uploaded file is empty."})
    if size > max_bytes:
        raise ForesightServiceError(
            {"file": f"The file exceeds the {max_bytes // (1024 * 1024)} MB limit."}
        )
    if suffix not in allowed_extensions:
        raise ForesightServiceError({"file": "This file extension is not permitted."})
    if content_type not in allowed_types:
        raise ForesightServiceError({"file": "This file type is not permitted."})
    header = upload.read(4096)
    upload.seek(0)
    signature_valid = {
        ".pdf": header.startswith(b"%PDF-"),
        ".png": header.startswith(b"\x89PNG\r\n\x1a\n"),
        ".jpg": header.startswith(b"\xff\xd8\xff"),
        ".jpeg": header.startswith(b"\xff\xd8\xff"),
        ".webp": header.startswith(b"RIFF") and header[8:12] == b"WEBP",
        ".docx": header.startswith(b"PK"),
        ".xlsx": header.startswith(b"PK"),
        ".txt": b"\x00" not in header,
        ".csv": b"\x00" not in header,
    }.get(suffix, False)
    if not signature_valid:
        raise ForesightServiceError(
            {"file": "The file content does not match its permitted extension."}
        )
    digest = hashlib.sha256()
    for chunk in upload.chunks():
        digest.update(chunk)
    upload.seek(0)
    return size, content_type, digest.hexdigest()


@transaction.atomic
def attach_source_file(*, actor: User, source: Source, upload) -> SourceAttachment:  # type: ignore[no-untyped-def]
    source = Source.objects.select_for_update().select_related("organisation").get(id=source.id)
    if not can_manage_record(
        actor=actor, organisation=source.organisation, created_by_id=source.created_by_id
    ):
        raise PermissionDenied("You cannot attach a file to this source.")
    size, content_type, digest = _validate_upload(upload)
    try:
        scan = scan_upload(upload)
    except MalwareScannerError as exc:
        if getattr(settings, "SOURCE_ATTACHMENT_MALWARE_FAIL_CLOSED", True):
            raise ForesightServiceError(
                {"file": "The file could not be scanned safely. Try again later."}
            ) from exc
        scan = None
    if scan is not None and scan.status == "infected":
        logger.warning(
            "upload.malware_blocked",
            extra={"user_id": str(actor.id)},
        )
        raise ForesightServiceError({"file": "The file was rejected by malware scanning."})
    if (
        scan is not None
        and scan.status != "clean"
        and getattr(settings, "SOURCE_ATTACHMENT_MALWARE_FAIL_CLOSED", True)
    ):
        raise ForesightServiceError({"file": "The file could not be scanned safely."})
    if SourceAttachment.objects.filter(source=source, sha256=digest).exists():
        raise ForesightServiceError({"file": "This exact file is already attached."})
    attachment = SourceAttachment(
        source=source,
        file=upload,
        original_name=Path(upload.name).name,
        content_type=content_type,
        size_bytes=size,
        sha256=digest,
        malware_scan_status=scan.status if scan is not None else SourceAttachment.ScanStatus.ERROR,
        malware_scan_engine=scan.engine if scan is not None else "unavailable-fail-open",
        malware_scanned_at=timezone.now(),
        uploaded_by=actor,
    )
    try:
        attachment.full_clean(validate_unique=False, validate_constraints=False)
        attachment.save()
    except IntegrityError as exc:
        raise ForesightServiceError({"file": "This exact file is already attached."}) from exc
    record_event(
        action="foresight.source.attachment_uploaded",
        object_type="foresight_source_attachment",
        object_id=str(attachment.id),
        actor=actor,
        organisation=source.organisation,
        metadata={
            "source_id": str(source.id),
            "original_name": attachment.original_name,
            "size_bytes": attachment.size_bytes,
            "sha256": attachment.sha256,
            "malware_scan_status": attachment.malware_scan_status,
            "malware_scan_engine": attachment.malware_scan_engine,
        },
    )
    return attachment


def record_source_attachment_download(*, actor: User, attachment: SourceAttachment) -> None:
    """Record access to a private customer file without changing the source record."""
    record_event(
        action="foresight.source.attachment_downloaded",
        object_type="foresight_source_attachment",
        object_id=str(attachment.id),
        actor=actor,
        organisation=attachment.source.organisation,
        metadata={
            "source_id": str(attachment.source_id),
            "original_name": attachment.original_name,
            "sha256": attachment.sha256,
        },
    )


@transaction.atomic
def create_signal(*, actor: User, organisation: Organisation, **fields: Any) -> Signal:
    if not can_contribute(actor=actor, organisation=organisation):
        raise PermissionDenied("You cannot add signals to this organisation.")
    source_id = fields.pop("source_id", None)
    owner_id = fields.pop("owner_id", actor.id)
    signal = Signal(
        organisation=organisation,
        source=_source(organisation=organisation, source_id=source_id),
        owner=_active_member(organisation=organisation, user_id=owner_id),
        created_by=actor,
        **fields,
    )
    if signal.status in {Signal.Status.REVIEWED, Signal.Status.MONITORING}:
        signal.last_reviewed_at = timezone.now()
        signal.last_reviewed_by = actor
    signal.full_clean(validate_unique=False, validate_constraints=False)
    signal.save()
    record_event(
        action="foresight.signal.created",
        object_type="foresight_signal",
        object_id=str(signal.id),
        actor=actor,
        organisation=organisation,
        metadata={
            "title": signal.title,
            "steep_category": signal.steep_category,
            "time_horizon": signal.time_horizon,
            "priority_score": signal.priority_score,
        },
    )
    return signal


@transaction.atomic
def update_signal(*, actor: User, signal: Signal, fields: dict[str, Any]) -> Signal:
    signal = Signal.objects.select_for_update().select_related("organisation").get(id=signal.id)
    if not can_manage_record(
        actor=actor,
        organisation=signal.organisation,
        created_by_id=signal.created_by_id,
        owner_id=signal.owner_id,
    ):
        raise PermissionDenied("You cannot edit this signal.")
    before_status = signal.status
    if "source_id" in fields:
        signal.source = _source(organisation=signal.organisation, source_id=fields.pop("source_id"))
    if "owner_id" in fields:
        signal.owner = _active_member(
            organisation=signal.organisation, user_id=fields.pop("owner_id")
        )
    for key, value in fields.items():
        setattr(signal, key, value)
    if signal.status in {Signal.Status.REVIEWED, Signal.Status.MONITORING} and (
        before_status != signal.status or not signal.last_reviewed_at
    ):
        signal.last_reviewed_at = timezone.now()
        signal.last_reviewed_by = actor
    signal.full_clean(validate_unique=False, validate_constraints=False)
    signal.save()
    record_event(
        action="foresight.signal.updated",
        object_type="foresight_signal",
        object_id=str(signal.id),
        actor=actor,
        organisation=signal.organisation,
        metadata={"before_status": before_status, "status": signal.status},
    )
    return signal


@transaction.atomic
def link_signal_to_decision(
    *, actor: User, signal: Signal, decision_id: Any, relevance: str
) -> SignalDecisionLink:
    signal = Signal.objects.select_for_update().select_related("organisation").get(id=signal.id)
    if not can_contribute(actor=actor, organisation=signal.organisation):
        raise PermissionDenied("You cannot link this signal to decisions.")
    try:
        decision = Decision.objects.get(id=decision_id, organisation=signal.organisation)
    except Decision.DoesNotExist as exc:
        raise ForesightServiceError(
            {"decision_id": "The decision does not belong to this organisation."}
        ) from exc
    link, created = SignalDecisionLink.objects.update_or_create(
        signal=signal,
        decision=decision,
        defaults={"relevance": relevance, "linked_by": actor},
    )
    link.full_clean(validate_unique=False, validate_constraints=False)
    record_event(
        action="foresight.signal.linked_to_decision"
        if created
        else "foresight.signal_decision_link.updated",
        object_type="foresight_signal_decision_link",
        object_id=str(link.id),
        actor=actor,
        organisation=signal.organisation,
        metadata={"signal_id": str(signal.id), "decision_id": str(decision.id)},
    )
    return link


@transaction.atomic
def create_watchlist(*, actor: User, organisation: Organisation, **fields: Any) -> Watchlist:
    if not can_contribute(actor=actor, organisation=organisation):
        raise PermissionDenied("You cannot create watchlists in this organisation.")
    owner_id = fields.pop("owner_id", actor.id)
    watchlist = Watchlist(
        organisation=organisation,
        owner=_active_member(organisation=organisation, user_id=owner_id),
        created_by=actor,
        **fields,
    )
    watchlist.full_clean(validate_unique=False, validate_constraints=False)
    watchlist.save()
    record_event(
        action="foresight.watchlist.created",
        object_type="foresight_watchlist",
        object_id=str(watchlist.id),
        actor=actor,
        organisation=organisation,
        metadata={"name": watchlist.name},
    )
    return watchlist


@transaction.atomic
def update_watchlist(*, actor: User, watchlist: Watchlist, fields: dict[str, Any]) -> Watchlist:
    watchlist = (
        Watchlist.objects.select_for_update().select_related("organisation").get(id=watchlist.id)
    )
    if not can_manage_record(
        actor=actor,
        organisation=watchlist.organisation,
        created_by_id=watchlist.created_by_id,
        owner_id=watchlist.owner_id,
    ):
        raise PermissionDenied("You cannot edit this watchlist.")
    if "owner_id" in fields:
        watchlist.owner = _active_member(
            organisation=watchlist.organisation, user_id=fields.pop("owner_id")
        )
    for key, value in fields.items():
        setattr(watchlist, key, value)
    watchlist.full_clean(validate_unique=False, validate_constraints=False)
    watchlist.save()
    record_event(
        action="foresight.watchlist.updated",
        object_type="foresight_watchlist",
        object_id=str(watchlist.id),
        actor=actor,
        organisation=watchlist.organisation,
        metadata={"name": watchlist.name, "is_active": watchlist.is_active},
    )
    return watchlist


@transaction.atomic
def add_signal_to_watchlist(
    *, actor: User, watchlist: Watchlist, signal_id: Any, note: str = ""
) -> WatchlistSignal:
    watchlist = (
        Watchlist.objects.select_for_update().select_related("organisation").get(id=watchlist.id)
    )
    if not can_manage_record(
        actor=actor,
        organisation=watchlist.organisation,
        created_by_id=watchlist.created_by_id,
        owner_id=watchlist.owner_id,
    ):
        raise PermissionDenied("You cannot edit this watchlist.")
    try:
        signal = Signal.objects.get(id=signal_id, organisation=watchlist.organisation)
    except Signal.DoesNotExist as exc:
        raise ForesightServiceError(
            {"signal_id": "The signal does not belong to this organisation."}
        ) from exc
    link, _ = WatchlistSignal.objects.update_or_create(
        watchlist=watchlist,
        signal=signal,
        defaults={"added_by": actor, "note": note},
    )
    link.full_clean(validate_unique=False, validate_constraints=False)
    record_event(
        action="foresight.watchlist.signal_added",
        object_type="foresight_watchlist_signal",
        object_id=str(link.id),
        actor=actor,
        organisation=watchlist.organisation,
        metadata={"watchlist_id": str(watchlist.id), "signal_id": str(signal.id)},
    )
    return link


@transaction.atomic
def remove_signal_from_watchlist(*, actor: User, watchlist: Watchlist, signal_id: Any) -> None:
    watchlist = (
        Watchlist.objects.select_for_update().select_related("organisation").get(id=watchlist.id)
    )
    if not can_manage_record(
        actor=actor,
        organisation=watchlist.organisation,
        created_by_id=watchlist.created_by_id,
        owner_id=watchlist.owner_id,
    ):
        raise PermissionDenied("You cannot edit this watchlist.")
    deleted, _ = WatchlistSignal.objects.filter(watchlist=watchlist, signal_id=signal_id).delete()
    if not deleted:
        raise ForesightServiceError({"signal_id": "The signal is not in this watchlist."})
    record_event(
        action="foresight.watchlist.signal_removed",
        object_type="foresight_watchlist",
        object_id=str(watchlist.id),
        actor=actor,
        organisation=watchlist.organisation,
        metadata={"signal_id": str(signal_id)},
    )


@transaction.atomic
def create_feed_subscription(
    *,
    actor: User,
    organisation: Organisation,
    name: str,
    feed_url: str,
    owner_id: Any | None = None,
) -> FeedSubscription:
    if not can_contribute(actor=actor, organisation=organisation):
        raise PermissionDenied("You cannot add feeds to this organisation.")
    try:
        safe_url = validate_public_feed_url(feed_url, debug=settings.DEBUG)
    except FeedFetchError as exc:
        raise ForesightServiceError({"feed_url": str(exc)}) from exc
    feed = FeedSubscription(
        organisation=organisation,
        name=name,
        feed_url=safe_url,
        owner=_active_member(organisation=organisation, user_id=owner_id or actor.id),
        created_by=actor,
    )
    feed.full_clean(validate_unique=False, validate_constraints=False)
    feed.save()
    record_event(
        action="foresight.feed.created",
        object_type="foresight_feed",
        object_id=str(feed.id),
        actor=actor,
        organisation=organisation,
        metadata={"name": feed.name, "feed_url": feed.feed_url},
    )
    return feed


def sync_feed_subscription(*, actor: User, feed: FeedSubscription) -> dict[str, Any]:
    feed = FeedSubscription.objects.select_related("organisation").get(id=feed.id)
    if not can_manage_record(
        actor=actor,
        organisation=feed.organisation,
        created_by_id=feed.created_by_id,
        owner_id=feed.owner_id,
    ):
        raise PermissionDenied("You cannot synchronise this feed.")
    checked_at = timezone.now()
    try:
        document = fetch_feed(
            feed.feed_url,
            debug=settings.DEBUG,
            etag=feed.etag,
            last_modified=feed.last_modified,
        )
    except FeedFetchError as exc:
        FeedSubscription.objects.filter(id=feed.id).update(
            last_checked_at=checked_at,
            last_error=str(exc)[:1000],
            updated_at=checked_at,
        )
        record_event(
            action="foresight.feed.sync_failed",
            object_type="foresight_feed",
            object_id=str(feed.id),
            actor=actor,
            organisation=feed.organisation,
            metadata={"error": str(exc)},
        )
        raise ForesightServiceError({"feed": str(exc)}) from exc

    created_count = 0
    with transaction.atomic():
        locked_feed = FeedSubscription.objects.select_for_update().get(id=feed.id)
        for entry in document.entries:
            source, was_created = Source.objects.get_or_create(
                feed=locked_feed,
                external_id=entry.external_id,
                defaults={
                    "organisation": locked_feed.organisation,
                    "title": entry.title,
                    "source_type": Source.SourceType.NEWS,
                    "author": entry.author,
                    "publisher": locked_feed.name,
                    "published_on": entry.published_on,
                    "source_url": (urljoin(locked_feed.feed_url, entry.url) if entry.url else ""),
                    "reference": f"Imported from RSS/Atom feed: {locked_feed.name}",
                    "credibility": Source.Credibility.UNASSESSED,
                    "notes": entry.summary,
                    "created_by": actor,
                },
            )
            if was_created:
                source.full_clean(validate_unique=False, validate_constraints=False)
                created_count += 1
        locked_feed.last_checked_at = checked_at
        locked_feed.last_error = ""
        if not document.not_modified:
            locked_feed.last_success_at = checked_at
            locked_feed.etag = document.etag
            locked_feed.last_modified = document.last_modified
        locked_feed.save(
            update_fields=[
                "last_checked_at",
                "last_success_at",
                "last_error",
                "etag",
                "last_modified",
                "updated_at",
            ]
        )
    record_event(
        action="foresight.feed.synced",
        object_type="foresight_feed",
        object_id=str(feed.id),
        actor=actor,
        organisation=feed.organisation,
        metadata={
            "created_sources": created_count,
            "entries_seen": len(document.entries),
            "not_modified": document.not_modified,
        },
    )
    return {
        "created_sources": created_count,
        "entries_seen": len(document.entries),
        "not_modified": document.not_modified,
    }
