from unittest.mock import patch

import pytest
from django.test import override_settings

from apps.foresight.feeds import (
    FeedDocument,
    FeedEntry,
    FeedFetchError,
    parse_feed,
    validate_public_feed_url,
)
from apps.foresight.models import FeedSubscription, Source
from apps.foresight.services import create_feed_subscription, sync_feed_subscription


def test_parse_rss_entries_without_interpreting_them_as_signals():
    content = b"""<?xml version='1.0'?>
    <rss version='2.0'><channel><title>Futures feed</title>
      <item><guid>entry-1</guid><title>Emerging regulation</title>
      <link>https://example.org/item-1</link><description><![CDATA[<p>New guidance appeared.</p>]]></description>
      <pubDate>Mon, 27 Jul 2026 08:00:00 GMT</pubDate></item>
    </channel></rss>"""

    entries = parse_feed(content)

    assert len(entries) == 1
    assert entries[0].external_id == "entry-1"
    assert entries[0].summary == "New guidance appeared."
    assert entries[0].published_on.isoformat() == "2026-07-27"


def test_private_feed_destination_is_rejected(monkeypatch):
    monkeypatch.setattr(
        "socket.getaddrinfo",
        lambda *args, **kwargs: [(None, None, None, None, ("127.0.0.1", 80))],
    )

    with pytest.raises(FeedFetchError):
        validate_public_feed_url("http://internal.example/feed", debug=True)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_manual_feed_sync_imports_sources_not_signals(organisation_factory, monkeypatch):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    monkeypatch.setattr(
        "apps.foresight.services.validate_public_feed_url",
        lambda url, debug: url,
    )
    feed = create_feed_subscription(
        actor=organisation.created_by,
        organisation=organisation,
        name="Open futures feed",
        feed_url="https://example.org/feed.xml",
    )
    document = FeedDocument(
        entries=(
            FeedEntry(
                external_id="entry-1",
                title="Emerging field robotics",
                url="/robotics",
                author="Research team",
                published_on=None,
                summary="A new lower-cost platform is entering the market.",
            ),
        ),
        etag='"v1"',
        last_modified="Mon, 27 Jul 2026 08:00:00 GMT",
    )
    with patch("apps.foresight.services.fetch_feed", return_value=document):
        result = sync_feed_subscription(actor=organisation.created_by, feed=feed)

    assert result["created_sources"] == 1
    imported = Source.objects.get(feed=feed)
    assert imported.source_url == "https://example.org/robotics"
    assert organisation.foresight_signals.count() == 0

    with patch("apps.foresight.services.fetch_feed", return_value=document):
        second = sync_feed_subscription(actor=organisation.created_by, feed=feed)
    assert second["created_sources"] == 0
    assert FeedSubscription.objects.get(id=feed.id).last_success_at is not None
