"""Tenant-safe read selectors for foresight."""

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from apps.organisations.selectors import organisation_for_user

from .models import FeedSubscription, Signal, Source, SourceAttachment, Watchlist


def feeds_for_organisation(*, user, organisation_id):  # type: ignore[no-untyped-def]
    organisation = organisation_for_user(user=user, organisation_id=organisation_id)
    return FeedSubscription.objects.filter(organisation=organisation).select_related(
        "owner", "created_by"
    )


def feed_for_user(*, user, feed_id):  # type: ignore[no-untyped-def]
    return get_object_or_404(
        FeedSubscription.objects.filter(organisation__in=user_organisations(user)).select_related(
            "organisation", "owner", "created_by"
        ),
        id=feed_id,
    )


def sources_for_organisation(*, user, organisation_id, query="", status=""):  # type: ignore[no-untyped-def]
    organisation = organisation_for_user(user=user, organisation_id=organisation_id)
    items = Source.objects.filter(organisation=organisation).select_related("created_by", "feed")
    if query:
        items = items.filter(
            Q(title__icontains=query)
            | Q(author__icontains=query)
            | Q(publisher__icontains=query)
            | Q(reference__icontains=query)
        )
    if status:
        items = items.filter(status=status)
    return items.prefetch_related("attachments")


def source_for_user(*, user, source_id):  # type: ignore[no-untyped-def]
    return get_object_or_404(
        Source.objects.filter(organisation__in=user_organisations(user))
        .select_related("organisation", "created_by", "supersedes")
        .prefetch_related("attachments"),
        id=source_id,
    )


def attachment_for_user(*, user, attachment_id):  # type: ignore[no-untyped-def]
    return get_object_or_404(
        SourceAttachment.objects.filter(source__organisation__in=user_organisations(user))
        .select_related("source__organisation", "uploaded_by"),
        id=attachment_id,
    )


def signals_for_organisation(
    *, user, organisation_id, query="", steep_category="", time_horizon="", maturity="", status=""
):  # type: ignore[no-untyped-def]
    organisation = organisation_for_user(user=user, organisation_id=organisation_id)
    items = Signal.objects.filter(organisation=organisation).select_related(
        "source", "owner", "created_by", "last_reviewed_by"
    )
    if query:
        items = items.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(future_implication__icontains=query)
            | Q(domain__icontains=query)
            | Q(geography__icontains=query)
        )
    filters = {
        "steep_category": steep_category,
        "time_horizon": time_horizon,
        "maturity": maturity,
        "status": status,
    }
    for field, value in filters.items():
        if value:
            items = items.filter(**{field: value})
    return items.prefetch_related("decision_links__decision", "watchlists")


def signal_for_user(*, user, signal_id):  # type: ignore[no-untyped-def]
    return get_object_or_404(
        Signal.objects.filter(organisation__in=user_organisations(user))
        .select_related("organisation", "source", "owner", "created_by", "last_reviewed_by")
        .prefetch_related("decision_links__decision", "watchlists"),
        id=signal_id,
    )


def watchlists_for_organisation(*, user, organisation_id):  # type: ignore[no-untyped-def]
    organisation = organisation_for_user(user=user, organisation_id=organisation_id)
    return (
        Watchlist.objects.filter(organisation=organisation)
        .select_related("owner", "created_by")
        .annotate(signal_count=Count("signal_links"))
        .prefetch_related("signals")
    )


def watchlist_for_user(*, user, watchlist_id):  # type: ignore[no-untyped-def]
    return get_object_or_404(
        Watchlist.objects.filter(organisation__in=user_organisations(user))
        .select_related("organisation", "owner", "created_by")
        .annotate(signal_count=Count("signal_links"))
        .prefetch_related("signals"),
        id=watchlist_id,
    )


def user_organisations(user):  # type: ignore[no-untyped-def]
    from apps.organisations.models import Organisation

    return Organisation.objects.for_user(user)
