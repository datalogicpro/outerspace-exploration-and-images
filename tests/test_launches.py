from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

import pytest
from conftest import read_json

from launches import (
    LaunchPhoto,
    approved,
    launch_details,
    launch_rows,
    parse_launch,
    parse_launches,
    parse_photo,
    split_launches,
)

CERES = "c6f8b6b0-6bae-460a-99bb-c12a3d29effd"
STARLINK = "f6af629d-39b5-4f86-bc0c-f8776444a858"
BANDWAGON = "3b430f81-0ff1-4d85-8a1a-cef0de326198"

BARE_LAUNCH = {"id": "bare", "name": "Bare launch", "net": "2026-11-01T00:00:00Z"}


def test_parse_a_real_launch() -> None:
    starlink = parse_launches(read_json("upcoming.json"))[1]
    assert starlink.id == STARLINK
    assert starlink.status == "Go for Launch"
    assert not starlink.finished
    assert starlink.time == datetime(2026, 10, 21, 23, 2, 41, tzinfo=UTC)
    assert starlink.provider == "SpaceX"
    assert starlink.provider_type == "Commercial"
    assert starlink.rocket == "Falcon 9 Block 5"
    assert starlink.mission_type == "Communications"
    assert starlink.orbit == "Low Earth Orbit"
    assert starlink.launch_site == "Space Launch Complex 4E, Vandenberg SFB, CA, USA"
    assert starlink.country == "United States of America"
    assert starlink.photo is not None
    assert starlink.photo.credit == "SpaceX"
    assert starlink.photo.license == "CC BY-NC 2.0"
    assert (
        starlink.photo.license_url == "https://creativecommons.org/licenses/by-nc/2.0/"
    )


def test_launch_with_only_the_basics() -> None:
    bare = parse_launch(BARE_LAUNCH)
    assert bare.status == ""
    assert not bare.finished
    assert bare.provider == bare.rocket == bare.mission == bare.launch_site == ""
    assert bare.photo is None


def test_parse_launches_with_no_results() -> None:
    assert parse_launches({}) == []


@pytest.mark.parametrize(
    "license_name",
    ["NASA Image and Media Guidelines", "Public Domain", "CC BY 2.0", "CC BY-SA 4.0"],
)
def test_approved_licenses(license_name: str) -> None:
    assert approved(license_name)


@pytest.mark.parametrize("license_name", ["Unknown", "All rights reserved", ""])
def test_other_licenses(license_name: str) -> None:
    assert not approved(license_name)


@pytest.mark.parametrize(
    "image",
    [
        None,
        {"image_url": ""},
        {"image_url": "https://x/a.jpg", "license": {"name": "Unknown"}},
        {"image_url": "https://x/a.jpg"},
    ],
    ids=["none", "no url", "unknown license", "no license"],
)
def test_photos_left_out(image: dict[str, Any] | None) -> None:
    assert parse_photo(image) is None


def test_photo_without_credit_or_license_link() -> None:
    image = {"image_url": "https://x/a.jpg", "license": {"name": "Public Domain"}}
    assert parse_photo(image) == LaunchPhoto(
        url="https://x/a.jpg",
        credit="Unknown",
        license="Public Domain",
        license_url=None,
    )


def test_split_moves_finished_launches_to_past_once() -> None:
    upcoming = parse_launches(read_json("upcoming.json"))
    past = parse_launches(read_json("past.json"))
    planned, done = split_launches(upcoming, past)
    assert [launch.id for launch in planned] == [STARLINK]
    assert [launch.id for launch in done] == [CERES, BANDWAGON]


def test_split_adds_a_finished_launch_missing_from_past() -> None:
    upcoming = parse_launches(read_json("upcoming.json"))
    _, done = split_launches(upcoming, [])
    assert [launch.id for launch in done] == [CERES]


def test_split_sorts_planned_soonest_first() -> None:
    later = parse_launch(BARE_LAUNCH)
    sooner = replace(later, id="sooner", time=datetime(2026, 10, 30, tzinfo=UTC))
    planned, _ = split_launches([later, sooner], [])
    assert [launch.id for launch in planned] == ["sooner", "bare"]


def test_launch_rows() -> None:
    starlink = parse_launches(read_json("upcoming.json"))[1]
    row = launch_rows([starlink])[0]
    assert row["Launch"] == "Falcon 9 Block 5 | Starlink Group 15-15"
    assert row["Exact to"] == "Second"
    assert list(row) == [
        "Date (UTC)",
        "Exact to",
        "Launch",
        "Provider",
        "Mission",
        "Orbit",
        "Launch site",
        "Country",
        "Status",
    ]


def test_launch_details() -> None:
    starlink = parse_launches(read_json("upcoming.json"))[1]
    assert launch_details(starlink) == [
        "**Date:** October 21, 2026 at 23:02 UTC",
        "**Status:** Go for Launch",
        "**Provider:** SpaceX (commercial)",
        "**Rocket:** Falcon 9 Block 5",
        "**Mission:** Starlink Group 15-15 (Communications)",
        "**Orbit:** Low Earth Orbit",
        "**Launch site:** Space Launch Complex 4E, Vandenberg SFB, CA, USA",
        "**Country:** United States of America",
    ]


def test_launch_details_flags_a_date_that_isnt_final() -> None:
    bare = replace(parse_launch(BARE_LAUNCH), time_precision="Day")
    assert launch_details(bare) == [
        "**Date:** November 01, 2026 at 00:00 UTC (not final: exact to the day)"
    ]
