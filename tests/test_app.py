"""The page itself, run with Streamlit's AppTest. Every source answers from
saved replies (see conftest.py), so no test reaches the internet."""

from collections.abc import Iterator
from pathlib import Path

import pytest
import streamlit as st
from conftest import (
    NASA_SEARCH,
    UPCOMING,
    WEBB_FEED,
    FakeSession,
    Reply,
    read_json,
    to_bytes,
)
from streamlit.testing.v1 import AppTest

import http_client

APP = str(Path(__file__).parent.parent / "app.py")
WEBB = "James Webb Space Telescope"
EMPTY_FEED = b"<rss><channel></channel></rss>"


@pytest.fixture(autouse=True)
def fresh_cache() -> Iterator[None]:
    """Each test starts with no saved replies."""
    st.cache_data.clear()
    yield
    st.cache_data.clear()


def run_app(monkeypatch: pytest.MonkeyPatch, routes: dict[str, Reply]) -> AppTest:
    monkeypatch.setattr(http_client, "make_session", lambda: FakeSession(routes))
    app = AppTest.from_file(APP, default_timeout=30)
    app.run()
    assert not app.exception
    return app


def captions(app: AppTest) -> list[str]:
    return [caption.value for caption in app.caption]


def subheaders(app: AppTest) -> list[str]:
    return [subheader.value for subheader in app.subheader]


def infos(app: AppTest) -> list[str]:
    return [info.value for info in app.info]


def test_page_opens_with_three_tabs(
    monkeypatch: pytest.MonkeyPatch, routes: dict[str, Reply]
) -> None:
    app = run_app(monkeypatch, routes)
    assert app.title[0].value == "Outer Space Exploration and Images"
    assert [tab.label for tab in app.tabs] == [
        "Explore",
        "Telescopes and cameras",
        "Spaceflights",
    ]
    assert any("NASA and ESA/Webb don't endorse" in text for text in captions(app))


def test_explore_shows_nebulae_and_a_large_view(
    monkeypatch: pytest.MonkeyPatch, routes: dict[str, Reply]
) -> None:
    app = run_app(monkeypatch, routes)
    assert "14 pictures found. Click View to see one large." in captions(app)
    app.button(key="explore_PIA03606").click().run()
    assert "Most Detailed Image of the Crab Nebula" in subheaders(app)
    assert any("**Date:** December 01, 2005" in md.value for md in app.markdown)


def test_explore_without_a_date_or_description(
    monkeypatch: pytest.MonkeyPatch, routes: dict[str, Reply]
) -> None:
    reply = read_json("images.json")
    data = reply["collection"]["items"][2]["data"][0]
    del data["date_created"]
    data["description"] = ""
    routes[NASA_SEARCH] = to_bytes(reply)
    app = run_app(monkeypatch, routes)
    app.button(key="explore_7890338").click().run()
    assert "High Energy Astronomy Observatory (HEAO)" in subheaders(app)
    assert "**Credit:** NASA" in [md.value for md in app.markdown]


def test_explore_page_two(
    monkeypatch: pytest.MonkeyPatch, routes: dict[str, Reply]
) -> None:
    app = run_app(monkeypatch, routes)
    app.text_input(key="explore_words").input("Saturn").run()
    page = app.number_input(key="explore_page_Saturn nebula")
    assert page.label == "Page (of 5)"
    page.set_value(2).run()
    assert not app.exception
    assert "100 pictures found. Click View to see one large." in captions(app)


def test_explore_with_nothing_chosen(
    monkeypatch: pytest.MonkeyPatch, routes: dict[str, Reply]
) -> None:
    app = run_app(monkeypatch, routes)
    app.selectbox(key="explore_type").set_value("Any").run()
    assert "Type a name, or pick a type or a telescope." in infos(app)


def test_explore_no_pictures_found(
    monkeypatch: pytest.MonkeyPatch, routes: dict[str, Reply]
) -> None:
    app = run_app(monkeypatch, routes)
    app.text_input(key="explore_words").input("nothing here").run()
    assert "No pictures found. Try other words, or a different choice." in infos(app)


def test_explore_leaves_webb_out(
    monkeypatch: pytest.MonkeyPatch, routes: dict[str, Reply]
) -> None:
    app = run_app(monkeypatch, routes)
    assert WEBB not in app.selectbox(key="explore_telescope").options


def test_source_failure_shows_an_error(
    monkeypatch: pytest.MonkeyPatch, routes: dict[str, Reply]
) -> None:
    routes[NASA_SEARCH] = 503
    app = run_app(monkeypatch, routes)
    assert any("NASA's image library didn't answer" in e.value for e in app.error)


def test_telescope_tab_types_follow_the_telescope(
    monkeypatch: pytest.MonkeyPatch, routes: dict[str, Reply]
) -> None:
    app = run_app(monkeypatch, routes)
    assert "Comets" in app.selectbox(key="scope_type_Hubble Space Telescope").options
    app.selectbox(key="scope_name").set_value("Chandra X-ray Observatory").run()
    types = app.selectbox(key="scope_type_Chandra X-ray Observatory")
    assert "Comets" not in types.options
    types.set_value("Galaxies").run()
    assert not app.exception


def test_telescope_tab_webb_pictures(
    monkeypatch: pytest.MonkeyPatch, routes: dict[str, Reply]
) -> None:
    app = run_app(monkeypatch, routes)
    app.selectbox(key="scope_name").set_value(WEBB).run()
    assert any("Webb's newest pictures of space" in text for text in captions(app))
    app.button(key="webb_potm2610a").click().run()
    assert "Stars brewing in a nebulous cauldron" in subheaders(app)
    assert "webb_weic2618a" not in [button.key for button in app.button]


def test_telescope_tab_webb_with_no_pictures(
    monkeypatch: pytest.MonkeyPatch, routes: dict[str, Reply]
) -> None:
    routes[WEBB_FEED] = EMPTY_FEED
    app = run_app(monkeypatch, routes)
    app.selectbox(key="scope_name").set_value(WEBB).run()
    assert "ESA/Webb has no pictures to show right now. Try again later." in infos(app)


def test_spaceflights_planned_and_past(
    monkeypatch: pytest.MonkeyPatch, routes: dict[str, Reply]
) -> None:
    app = run_app(monkeypatch, routes)
    assert any("can show in either list" in text for text in captions(app))
    assert "Falcon 9 Block 5 | Starlink Group 15-15" in subheaders(app)
    assert any("Photo: SpaceX, [CC BY-NC 2.0]" in text for text in captions(app))
    app.multiselect(key="flights_providers_Planned").set_value(["SpaceX"]).run()
    assert "Falcon 9 Block 5 | Starlink Group 15-15" in subheaders(app)

    app.radio(key="flights_which").set_value("Past").run()
    assert "Ceres-1S | Xiguang-4 01" in subheaders(app)
    bandwagon = "3b430f81-0ff1-4d85-8a1a-cef0de326198"
    app.selectbox(key="flights_launch_Past").set_value(bandwagon).run()
    assert any("Bandwagon 5" in name for name in subheaders(app))


def test_spaceflights_photo_without_a_license_link(
    monkeypatch: pytest.MonkeyPatch, routes: dict[str, Reply]
) -> None:
    reply = read_json("upcoming.json")
    image = reply["results"][1]["image"]
    image["license"] = {"name": "Public Domain", "link": None}
    reply["results"][1]["mission"]["description"] = ""
    routes[UPCOMING] = to_bytes(reply)
    app = run_app(monkeypatch, routes)
    assert "Photo: SpaceX, Public Domain" in captions(app)


def test_spaceflights_with_no_planned_launches(
    monkeypatch: pytest.MonkeyPatch, routes: dict[str, Reply]
) -> None:
    routes[UPCOMING] = b'{"results": []}'
    app = run_app(monkeypatch, routes)
    assert "No launches match." in infos(app)
