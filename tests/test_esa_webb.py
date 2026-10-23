from datetime import date

import pytest
from bs4 import BeautifulSoup
from conftest import WEBB_FEED, FakeSession, as_session, read_bytes, webb_routes

from esa_webb import (
    OBSERVATION,
    FeedItem,
    PageDetails,
    about_field,
    newest_pictures,
    parse_feed,
    parse_page,
    to_photo,
)
from http_client import ApiError

CREDIT = (
    "ESA/Webb, NASA & CSA, E. Sabbi, M. Zamani (ESA/Webb) "
    "Acknowledgement: M. H. Özsaraç"
)


def test_parse_feed_skips_items_without_an_image() -> None:
    items = parse_feed(read_bytes("webb_feed.xml"))
    assert [item.id for item in items] == [
        "potm2610a",
        "weic2618a",
        "weic2621b",
        "weic2617e",
    ]
    first = items[0]
    assert first.title == "Stars brewing in a nebulous cauldron"
    assert first.page_url == "https://esawebb.org/images/potm2610a/"
    assert first.image_url.endswith("/screen/potm2610a.jpg")
    assert first.description.startswith("In this Picture of the Month")
    assert "N159 wide view" not in first.description


@pytest.mark.parametrize(
    "feed",
    [b"<rss><channel>", b'<!DOCTYPE x [<!ENTITY a "aaaa">]><rss>&a;</rss>'],
    ids=["broken", "entities"],
)
def test_parse_feed_refuses_bad_feeds(feed: bytes) -> None:
    with pytest.raises(ApiError, match="feed that couldn't be read"):
        parse_feed(feed)


def test_parse_page() -> None:
    details = parse_page(read_bytes("webb_observation.html"))
    assert details == PageDetails(credit=CREDIT, kind=OBSERVATION)
    assert parse_page(read_bytes("webb_artwork.html")).kind == "Artwork"
    assert parse_page(read_bytes("webb_no_credit.html")).credit == ""


def test_about_field_missing() -> None:
    soup = BeautifulSoup("<table><tr><th>Type:</th></tr></table>", "html.parser")
    assert about_field(soup, "Type") == ""
    assert about_field(soup, "Size") == ""


def test_newest_pictures_keeps_credited_observations() -> None:
    fake = FakeSession(webb_routes())
    photos = newest_pictures(as_session(fake))
    assert len(photos) == 1
    photo = photos[0]
    assert photo.id == "potm2610a"
    assert photo.credit == CREDIT
    assert photo.taken == date(2026, 10, 22)
    assert photo.site == "ESA/Webb"
    assert photo.page_url == "https://esawebb.org/images/potm2610a/"
    assert photo.thumbnail_url == photo.large_url
    assert len(fake.calls) == 5


def test_picture_without_a_release_date() -> None:
    item = FeedItem("a", "A", "https://x/a/", "https://x/a.jpg", "", released="")
    assert to_photo(item, PageDetails(credit=CREDIT, kind=OBSERVATION)).taken is None


def test_newest_pictures_feed_failure() -> None:
    fake = FakeSession({WEBB_FEED: 503})
    with pytest.raises(ApiError, match="ESA/Webb didn't answer"):
        newest_pictures(as_session(fake))
