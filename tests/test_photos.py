from datetime import date
from typing import Any

import pytest
from conftest import read_json

from photos import (
    DEFAULT_CREDIT,
    MAX_PAGES,
    clean_text,
    find_credit,
    is_space_picture,
    page_count,
    parse_photo,
    parse_photos,
    picture_links,
    taken_on,
    total_hits,
)


def item(
    data: dict[str, Any], links: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """One search result, with a thumbnail unless other links are given."""
    base = {"nasa_id": "TEST1", "title": "Saturn", "media_type": "image"}
    if links is None:
        links = [{"href": "https://x/TEST1~thumb.jpg", "render": "image"}]
    return {"data": [base | data], "links": links}


def test_parse_photos_from_a_real_reply() -> None:
    photos = parse_photos(read_json("images.json"))
    assert [photo.id for photo in photos] == [
        "PIA03606",
        "GSFC_20171208_Archive_e000273",
        "7890338",
    ]
    crab = photos[0]
    assert crab.title == "Most Detailed Image of the Crab Nebula"
    assert crab.credit == "NASA/ESA/JPL/Arizona State Univ."
    assert crab.page_url == "https://images.nasa.gov/details/PIA03606"
    assert crab.site == "NASA"
    assert crab.thumbnail_url.endswith("PIA03606~thumb.jpg")
    assert crab.large_url.endswith("PIA03606~large.jpg")


def test_credit_from_the_description_and_boilerplate_removed() -> None:
    hubble = parse_photos(read_json("images.json"))[1]
    assert hubble.credit.startswith("NASA and ESA, Acknowledgment")
    assert "Follow us on" not in hubble.description
    assert "<" not in hubble.description
    assert hubble.large_url.endswith("~small.jpg")


def test_credit_defaults_to_nasa() -> None:
    heao = parse_photos(read_json("images.json"))[2]
    assert heao.credit == DEFAULT_CREDIT
    assert heao.large_url.endswith("~medium.jpg")


def test_photo_with_a_date_and_without() -> None:
    dated = parse_photo(item({"date_created": "2005-12-01T00:00:00Z"}))
    assert dated is not None and dated.taken == date(2005, 12, 1)
    undated = parse_photo(item({}))
    assert undated is not None and undated.taken is None


@pytest.mark.parametrize(
    "data",
    [
        {"media_type": "video"},
        {"photographer": "NASA/Bill Ingalls"},
        {"nasa_id": "KSC-99pp0976"},
        {"title": "Mars Odyssey Orbiter By the Numbers"},
        {"description": "© 2010 Someone Else"},
        {"secondary_creator": "Copyright Someone Else"},
    ],
    ids=["video", "photographer", "KSC", "title word", "copyright", "credit"],
)
def test_pictures_left_out(data: dict[str, Any]) -> None:
    assert parse_photo(item(data)) is None


def test_picture_without_an_image_left_out() -> None:
    assert parse_photo(item({}, links=[{"href": "x.srt", "render": "caption"}])) is None


def test_no_data_left_out() -> None:
    assert parse_photo({}) is None


@pytest.mark.parametrize(
    "title",
    [
        "Twin Rover Twins",
        "Perseverance Test Rover's First Drive",
        "Rocket to Mars (Artist's Concept)",
        "Environmental Plot at Jezero",
        "Apollo 40th Newseum Panel Discussion",
        "Computer-Design Drawing for NASA 2020 Mars Rover",
    ],
)
def test_not_space_titles(title: str) -> None:
    assert not is_space_picture({"title": title})


@pytest.mark.parametrize(
    "title", ["Hubble Sharpest View Of Mars", "Ant Nebula", "Testudo crater"]
)
def test_space_titles(title: str) -> None:
    assert is_space_picture({"title": title})


def test_long_credit_line_is_not_a_credit() -> None:
    description = "Credit: " + "word " * 40
    assert find_credit({}, description) == DEFAULT_CREDIT


def test_clean_text() -> None:
    text = "<p>Saturn&amp;rings</p>\n\n  big. Follow us on Twitter"
    assert clean_text(text) == "Saturn&rings big."


def test_picture_links() -> None:
    assert picture_links([]) is None
    only_original = [{"href": "https://x/A~orig.jpg", "render": "image"}]
    assert picture_links(only_original) == (
        "https://x/A~orig.jpg",
        "https://x/A~orig.jpg",
    )


def test_taken_on() -> None:
    assert taken_on(None) is None
    assert taken_on("2020-02-03T10:00:00Z") == date(2020, 2, 3)


def test_total_hits() -> None:
    assert total_hits(read_json("images.json")) == 14
    assert total_hits({}) == 0


@pytest.mark.parametrize(
    ("hits", "pages"), [(0, 1), (24, 1), (25, 2), (100_000, MAX_PAGES)]
)
def test_page_count(hits: int, pages: int) -> None:
    assert page_count(hits, 24) == pages
