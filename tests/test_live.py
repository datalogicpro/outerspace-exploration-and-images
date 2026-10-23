"""Checks against the real sources, to catch a change in what they send.

They reach the internet, so the usual test run skips them. Run them with:
    uv run pytest -m live --no-cov
"""

import pytest

import esa_webb
import launch_library
import nasa_images
from http_client import make_session
from launches import parse_launches
from photos import parse_photos, total_hits

pytestmark = pytest.mark.live


def test_nasa_search_still_finds_pictures() -> None:
    with make_session() as session:
        reply = nasa_images.search_images(session, "Crab Nebula")
    assert total_hits(reply) > 0
    photos = parse_photos(reply)
    assert photos
    assert all(photo.thumbnail_url and photo.large_url for photo in photos)


def test_launch_library_still_lists_launches() -> None:
    with make_session() as session:
        launches = parse_launches(launch_library.upcoming_launches(session))
    assert launches
    assert all(launch.name and launch.time for launch in launches)


def test_esa_webb_pages_still_have_credit_lines() -> None:
    with make_session() as session:
        photos = esa_webb.newest_pictures(session)
    assert photos
    assert all(photo.credit for photo in photos)
