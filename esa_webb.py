"""Get the James Webb Space Telescope's newest pictures from ESA/Webb.

ESA/Webb has no API. Its image feed lists the 25 newest pictures, but not
their credit lines, which the license requires. So each picture's own page
is read for its credit line and its type. Only "Observation" pictures (what
Webb saw, not artwork or charts) with a credit line are kept.

License: CC BY 4.0, with each picture's full credit line shown.
https://esawebb.org/copyright/
"""

import logging
import os
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from xml.etree.ElementTree import ParseError

import defusedxml.ElementTree as SafeXml
import requests
from bs4 import BeautifulSoup

from http_client import ApiError, get_page
from photos import SPACES, Photo, clean_text

# ESA_WEBB_FEED_URL can point the app at a stand-in server, as the browser
# test does
FEED_URL = os.environ.get("ESA_WEBB_FEED_URL", "https://esawebb.org/images/feed/")
SOURCE = "ESA/Webb"
OBSERVATION = "Observation"

# Where a feed description turns into a list of links
LINKS_HEADING = "<h3>Links</h3>"

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class FeedItem:
    id: str
    title: str
    page_url: str
    image_url: str
    description: str
    released: str


@dataclass(frozen=True)
class PageDetails:
    credit: str
    kind: str


def parse_feed(feed: bytes) -> list[FeedItem]:
    """Every picture in the feed that has a page and an image.

    The XML reader is defusedxml, which refuses the tricks a bad feed could
    use to tie up the app. Raises ApiError when the feed can't be read.
    """
    try:
        root = SafeXml.fromstring(feed)
    except (ParseError, ValueError) as exc:  # defusedxml's refusals are ValueErrors
        raise ApiError(f"{SOURCE} sent a feed that couldn't be read.") from exc
    items = []
    for item in root.iterfind("channel/item"):
        page_url = item.findtext("link") or ""
        enclosure = item.find("enclosure")
        image_url = enclosure.get("url", "") if enclosure is not None else ""
        if not page_url or not image_url:
            continue
        description = item.findtext("description") or ""
        items.append(
            FeedItem(
                id=page_url.rstrip("/").rsplit("/", 1)[-1],
                title=clean_text(item.findtext("title") or ""),
                page_url=page_url,
                image_url=image_url,
                description=clean_text(description.split(LINKS_HEADING)[0]),
                released=item.findtext("pubDate") or "",
            )
        )
    return items


def about_field(soup: BeautifulSoup, name: str) -> str:
    """One line of the page's "About the Image" table, like "Type"."""
    for header in soup.select("th"):
        if header.get_text(strip=True) == f"{name}:":
            cell = header.find_next_sibling("td")
            return cell.get_text(strip=True) if cell is not None else ""
    return ""


def parse_page(page: bytes) -> PageDetails:
    """The credit line and the type ("Observation", "Artwork"...) from a
    picture's page."""
    soup = BeautifulSoup(page, "html.parser")
    credit_box = soup.select_one("div.credit")
    credit = credit_box.get_text(" ", strip=True) if credit_box is not None else ""
    return PageDetails(credit=SPACES.sub(" ", credit), kind=about_field(soup, "Type"))


def to_photo(item: FeedItem, details: PageDetails) -> Photo:
    released = parsedate_to_datetime(item.released).date() if item.released else None
    return Photo(
        id=item.id,
        title=item.title,
        description=item.description,
        taken=released,
        credit=details.credit,
        thumbnail_url=item.image_url,
        large_url=item.image_url,
        page_url=item.page_url,
        site=SOURCE,
    )


def newest_pictures(session: requests.Session) -> list[Photo]:
    """Webb's newest observations, newest first.

    A picture whose page can't be read, or that has no credit line, is left
    out, and the rest still show. Raises ApiError when the feed itself fails.
    """
    photos = []
    for item in parse_feed(get_page(session, SOURCE, FEED_URL)):
        try:
            details = parse_page(get_page(session, SOURCE, item.page_url))
        except ApiError:
            log.warning("skipped %s: its page couldn't be read", item.id)
            continue
        if details.kind != OBSERVATION:
            continue
        if not details.credit:
            log.warning("skipped %s: its page has no credit line", item.id)
            continue
        photos.append(to_photo(item, details))
    return photos
