"""Turn NASA image library replies into clean picture records.

The Photo record is shared with ESA/Webb's pictures (see esa_webb.py).

NASA's replies are uneven, so each record evens them out:
- descriptions lose their web code and "follow us" lines
- the credit comes from whichever place NASA put it
- the picture links are the best sizes that actually exist
- pictures marked with someone else's copyright are left out, since NASA's
  permission doesn't cover them
- pictures that aren't of space are left out: ones taken by a photographer
  on the ground, ones from Kennedy Space Center (rockets and spacecraft
  being prepared), drawings, charts, tests, people, and events found by
  words in their titles, and the titles listed in blocked_titles.txt
"""

import html
import math
import re
from dataclasses import dataclass
from datetime import date, datetime
from functools import cache
from pathlib import Path
from typing import Any

DEFAULT_CREDIT = "NASA"
# A credit longer than this is a sentence caught by mistake, not a credit
MAX_CREDIT_LENGTH = 150
# The page shows at most this many pages of results for one search
MAX_PAGES = 100

TAG = re.compile(r"<[^>]+>")
SPACES = re.compile(r"\s+")
HASHTAG = re.compile(r"#\w+")
CREDIT = re.compile(r"Credits?:\s*(.+?)(?:\s{2,}|$)", re.IGNORECASE)
COPYRIGHT = re.compile(r"©|copyright", re.IGNORECASE)

# Kennedy Space Center's pictures, whose IDs start "KSC", show rockets and
# spacecraft being prepared on the ground
GROUND_ID_PREFIXES = ("KSC",)

# Pictures checked by hand and left out by their exact title
BLOCKED_TITLES_FILE = Path(__file__).parent / "blocked_titles.txt"

# Title words that mean a drawing, chart, test, people, or an event, not a
# picture of space
NOT_SPACE_WORDS = (
    "concept",
    "illustration",
    "drawing",
    "visualization",
    "plot",
    "chart",
    "by the numbers",
    "tests?",
    "twins",
    "glasses",
    "panel",
    "discussion",
    "sample tube",
    "parking spot",
    "rockets?",
    "managers?",
    "teams?",
    "engineers?",
    "scientists?",
    r"celebrat\w*",
    "end of mission",
)
NOT_SPACE_TITLE = re.compile(
    r"\b(?:" + "|".join(NOT_SPACE_WORDS) + r")\b", re.IGNORECASE
)

# Where NASA's descriptions turn into links and social media lines
BOILERPLATE = (
    "Follow us on",
    "Like us on",
    "Join us on",
    "Find us on",
    "NASA image use policy",
    "NASA Goddard Space Flight Center enables",
    "NASA Goddard Space Flight Center is home",
    "To learn more about the Hubble Space Telescope go here",
)

# A picture's page on NASA's website
NASA_PAGE_URL = "https://images.nasa.gov/details/"
NASA_SITE = "NASA"

# Picture sizes, biggest first, for the large view
LARGE_SIZES = ("~large.", "~medium.", "~small.")


@dataclass(frozen=True)
class Photo:
    """One picture, from NASA or from ESA/Webb.

    page_url is the picture's page on its site, with every size to download,
    and site names that site, like "NASA".
    """

    id: str
    title: str
    description: str
    taken: date | None
    credit: str
    thumbnail_url: str
    large_url: str
    page_url: str
    site: str


def clean_text(text: str) -> str:
    """Plain text from a site's text: no web code, links, or extra spaces."""
    text = html.unescape(TAG.sub(" ", text))
    for marker in BOILERPLATE:
        text = text.split(marker)[0]
    return SPACES.sub(" ", text).strip()


def find_credit(data: dict[str, Any], description: str) -> str:
    """Who made the picture: NASA's credit field, a "Credit:" line, or NASA."""
    if data.get("secondary_creator"):
        return str(data["secondary_creator"]).strip()
    match = CREDIT.search(TAG.sub("  ", html.unescape(description)))
    if match:
        credit = SPACES.sub(" ", HASHTAG.sub("", match.group(1))).strip(" .")
        if 0 < len(credit) <= MAX_CREDIT_LENGTH:
            return credit
    return DEFAULT_CREDIT


def picture_links(links: list[dict[str, Any]]) -> tuple[str, str] | None:
    """The thumbnail and the biggest picture that suits a web page, or None."""
    images = [link["href"] for link in links if link.get("render") == "image"]
    if not images:
        return None
    thumbnail = next((url for url in images if "~thumb." in url), images[0])
    for size in LARGE_SIZES:
        large = next((url for url in images if size in url), None)
        if large:
            return thumbnail, large
    return thumbnail, thumbnail


def taken_on(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.fromisoformat(value).date()


@cache
def blocked_titles() -> frozenset[str]:
    """The titles in blocked_titles.txt, in lowercase. The file is read once."""
    lines = BLOCKED_TITLES_FILE.read_text(encoding="utf-8").splitlines()
    return frozenset(
        line.strip().casefold()
        for line in lines
        if line.strip() and not line.startswith("#")
    )


def is_space_picture(data: dict[str, Any]) -> bool:
    """False for pictures taken on the ground, for drawings, charts, tests,
    people, and events, and for the titles in blocked_titles.txt.

    NASA fills in "photographer" for pictures a person took with a camera,
    like at an event.
    """
    if data.get("photographer"):
        return False
    if str(data.get("nasa_id", "")).startswith(GROUND_ID_PREFIXES):
        return False
    title = clean_text(str(data.get("title") or ""))
    if title.casefold() in blocked_titles():
        return False
    return not NOT_SPACE_TITLE.search(title)


def matching(photos: list[Photo], query: str) -> list[Photo]:
    """The pictures whose title or description has every word of the search,
    in any capitals. An empty search keeps them all."""
    words = query.casefold().split()
    return [
        photo
        for photo in photos
        if all(
            word in f"{photo.title} {photo.description}".casefold() for word in words
        )
    ]


def parse_photo(item: dict[str, Any]) -> Photo | None:
    """One picture, or None if it can't be shown."""
    data = (item.get("data") or [{}])[0]
    if data.get("media_type") != "image" or not is_space_picture(data):
        return None
    description = data.get("description") or data.get("description_508") or ""
    credit = find_credit(data, description)
    if COPYRIGHT.search(description) or COPYRIGHT.search(credit):
        return None
    links = picture_links(item.get("links") or [])
    if links is None:
        return None
    thumbnail, large = links
    return Photo(
        id=data["nasa_id"],
        title=clean_text(data.get("title") or data["nasa_id"]),
        description=clean_text(description),
        taken=taken_on(data.get("date_created")),
        credit=credit,
        thumbnail_url=thumbnail,
        large_url=large,
        page_url=f"{NASA_PAGE_URL}{data['nasa_id']}",
        site=NASA_SITE,
    )


def parse_photos(reply: dict[str, Any]) -> list[Photo]:
    """Every picture in a search reply that can be shown, in NASA's order."""
    items = reply.get("collection", {}).get("items", [])
    photos = (parse_photo(item) for item in items)
    return [photo for photo in photos if photo is not None]


def total_hits(reply: dict[str, Any]) -> int:
    return int(reply.get("collection", {}).get("metadata", {}).get("total_hits", 0))


def page_count(hits: int, page_size: int) -> int:
    """How many pages of results to offer, from 1 up to MAX_PAGES."""
    return max(1, min(math.ceil(hits / page_size), MAX_PAGES))
