"""Safe, dependency-light RSS and Atom retrieval and parsing."""

from __future__ import annotations

import html
import ipaddress
import os
import socket
from dataclasses import dataclass
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from defusedxml import ElementTree


class FeedFetchError(ValueError):
    """A safe, user-visible feed retrieval failure."""


@dataclass(frozen=True)
class FeedEntry:
    external_id: str
    title: str
    url: str
    author: str
    published_on: date | None
    summary: str


@dataclass(frozen=True)
class FeedDocument:
    entries: tuple[FeedEntry, ...]
    etag: str
    last_modified: str
    not_modified: bool = False


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        value = data.strip()
        if value:
            self.parts.append(value)


def _plain_text(value: str, limit: int = 5000) -> str:
    parser = _TextExtractor()
    try:
        parser.feed(html.unescape(value))
        text = " ".join(parser.parts)
    except (ValueError, TypeError):
        text = value
    return " ".join(text.split())[:limit]


def _allowed_domains() -> set[str]:
    return {
        value.strip().lower()
        for value in os.getenv("FORESIGHT_FEED_ALLOWED_DOMAINS", "").split(",")
        if value.strip()
    }


def validate_public_feed_url(url: str, *, debug: bool = False) -> str:
    """Reject credentials, non-HTTP URLs, and private or unapproved destinations."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise FeedFetchError("RSS and Atom feeds must use http or https.")
    if not parsed.hostname or parsed.username or parsed.password:
        raise FeedFetchError("The feed URL must contain a public hostname and no credentials.")
    hostname = parsed.hostname.rstrip(".").lower()
    allowed = _allowed_domains()
    if not debug and not allowed:
        raise FeedFetchError(
            "Production feed retrieval requires FORESIGHT_FEED_ALLOWED_DOMAINS to be configured."
        )
    if (
        allowed
        and hostname not in allowed
        and not any(hostname.endswith(f".{item}") for item in allowed)
    ):
        raise FeedFetchError("This feed domain is not in the organisation deployment allowlist.")
    try:
        addresses = {
            result[4][0]
            for result in socket.getaddrinfo(
                hostname,
                parsed.port or (443 if parsed.scheme == "https" else 80),
                type=socket.SOCK_STREAM,
            )
        }
    except socket.gaierror as exc:
        raise FeedFetchError("The feed hostname could not be resolved.") from exc
    if not addresses:
        raise FeedFetchError("The feed hostname did not resolve to an address.")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if any(
            (
                ip.is_private,
                ip.is_loopback,
                ip.is_link_local,
                ip.is_multicast,
                ip.is_reserved,
                ip.is_unspecified,
            )
        ):
            raise FeedFetchError("Feeds cannot resolve to private or local network addresses.")
    return parsed.geturl()


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        raise FeedFetchError(
            "The feed redirected. Save the final public feed URL instead of a redirecting URL."
        )


def _date(value: str) -> date | None:
    value = value.strip()
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).date()
    except (TypeError, ValueError, OverflowError):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            return None


def _text(element, names: tuple[str, ...]) -> str:  # type: ignore[no-untyped-def]
    for child in element.iter():
        local_name = child.tag.rsplit("}", 1)[-1].lower()
        if local_name in names and child.text:
            return child.text.strip()
    return ""


def _entry_link(element) -> str:  # type: ignore[no-untyped-def]
    for child in element.iter():
        if child.tag.rsplit("}", 1)[-1].lower() != "link":
            continue
        href = child.attrib.get("href", "").strip()
        rel = child.attrib.get("rel", "alternate").strip().lower()
        if href and rel in {"alternate", ""}:
            return href
        if child.text and child.text.strip():
            return child.text.strip()
    return ""


def parse_feed(content: bytes, *, limit: int = 50) -> tuple[FeedEntry, ...]:
    """Parse common RSS and Atom records without executing external entities."""
    try:
        root = ElementTree.fromstring(content)
    except (ElementTree.ParseError, ValueError) as exc:
        raise FeedFetchError("The response was not valid RSS or Atom XML.") from exc
    entries = [
        element
        for element in root.iter()
        if element.tag.rsplit("}", 1)[-1].lower() in {"item", "entry"}
    ]
    records: list[FeedEntry] = []
    for element in entries[:limit]:
        title = _plain_text(_text(element, ("title",)), 300)
        url = _entry_link(element)
        external_id = _text(element, ("guid", "id")) or url or title
        if not title or not external_id:
            continue
        summary = _plain_text(_text(element, ("description", "summary", "content")))
        author = _plain_text(_text(element, ("author", "creator", "name")), 240)
        published = _date(_text(element, ("pubdate", "published", "updated", "date")))
        records.append(
            FeedEntry(
                external_id=external_id[:500],
                title=title,
                url=url[:1200],
                author=author,
                published_on=published,
                summary=summary,
            )
        )
    if not records:
        raise FeedFetchError("The feed did not contain readable entries.")
    return tuple(records)


def fetch_feed(
    url: str,
    *,
    debug: bool,
    etag: str = "",
    last_modified: str = "",
    timeout: float = 10.0,
    max_bytes: int = 2 * 1024 * 1024,
) -> FeedDocument:
    safe_url = validate_public_feed_url(url, debug=debug)
    headers = {
        "Accept": "application/atom+xml, application/rss+xml, application/xml, text/xml;q=0.9",
        "User-Agent": "CrowdSmarter-Foresight/1.0",
    }
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified
    request = Request(safe_url, headers=headers)
    opener = build_opener(_NoRedirectHandler())
    try:
        with opener.open(request, timeout=timeout) as response:
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > max_bytes:
                raise FeedFetchError("The feed exceeds the 2 MB retrieval limit.")
            content = response.read(max_bytes + 1)
            if len(content) > max_bytes:
                raise FeedFetchError("The feed exceeds the 2 MB retrieval limit.")
            return FeedDocument(
                entries=parse_feed(content),
                etag=response.headers.get("ETag", "")[:500],
                last_modified=response.headers.get("Last-Modified", "")[:500],
            )
    except HTTPError as exc:
        if exc.code == 304:
            return FeedDocument(
                entries=(), etag=etag, last_modified=last_modified, not_modified=True
            )
        raise FeedFetchError(f"The feed returned HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise FeedFetchError("The feed could not be retrieved safely.") from exc
