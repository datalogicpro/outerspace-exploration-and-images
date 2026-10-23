"""Outer Space Exploration and Images: space pictures from NASA and ESA/Webb,
by object and telescope, and past and planned spaceflights.

Run it with:  uv run python -m streamlit run app.py

This file is the page itself: the tabs, the choices, and the calls to the
sources. Each reply is saved for an hour, so the page doesn't call the
sources on every click.
"""

import logging
from typing import Any

import streamlit as st

import esa_webb
import launch_library
import nasa_images
from http_client import ApiError, make_session
from launches import (
    Launch,
    launch_details,
    launch_rows,
    parse_launches,
    split_launches,
)
from photos import Photo, page_count, parse_photos, total_hits
from telescopes import (
    ANY,
    ESA_WEBB,
    NASA_TELESCOPES,
    OBJECT_TYPES,
    TELESCOPES,
    Telescope,
    build_query,
    telescope_named,
    types_for,
)

CACHE_SECONDS = 60 * 60
COLUMNS = 4
DEFAULT_TYPE = "Nebulae"
PLANNED = "Planned"
PAST = "Past"
LAUNCH_NOTE = (
    "Times are in UTC. Launch data refreshes once an hour, so a launch "
    "happening today, or in the last hour, can show in either list. If you "
    "don't find one, check the other."
)
WEBB_NOTE = (
    "Webb's newest pictures of space, from ESA/Webb, newest first. "
    "Each picture shows its own credit line."
)
CREDIT = (
    "Pictures: NASA Image and Video Library, and ESA/Webb under "
    "[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). "
    "NASA and ESA/Webb don't endorse this site. "
    "Launch data: The Space Devs, Launch Library 2."
)


@st.cache_data(ttl=CACHE_SECONDS, show_spinner="Asking NASA...")
def load_photos(query: str, page: int) -> dict[str, Any]:
    with make_session() as session:
        return nasa_images.search_images(session, query, page)


@st.cache_data(ttl=CACHE_SECONDS, show_spinner="Asking ESA/Webb...")
def load_webb() -> list[Photo]:
    """Webb's newest pictures. Saved for an hour, since each one takes a
    request to its own page for the credit line."""
    with make_session() as session:
        return esa_webb.newest_pictures(session)


@st.cache_data(ttl=CACHE_SECONDS, show_spinner="Asking Launch Library...")
def load_launches() -> tuple[dict[str, Any], dict[str, Any]]:
    """The upcoming and past launch replies. Saved for an hour, since Launch
    Library allows only 15 requests an hour without a key."""
    with make_session() as session:
        upcoming = launch_library.upcoming_launches(session)
        past = launch_library.past_launches(session)
    return upcoming, past


def selected_photo(photos: list[Photo], key: str) -> Photo | None:
    """The picture whose View button was clicked last, if it's still shown."""
    photo_id = st.session_state.get(f"{key}_selected")
    return next((photo for photo in photos if photo.id == photo_id), None)


def show_photo(photo: Photo) -> None:
    """One picture, large, with everything known about it."""
    with st.container(border=True):
        st.subheader(photo.title)
        st.image(photo.large_url, width="stretch")
        lines = [f"**Credit:** {photo.credit}"]
        if photo.taken:
            lines.insert(0, f"**Date:** {photo.taken:%B %d, %Y}")
        st.markdown("  \n".join(lines))
        if photo.description:
            st.write(photo.description)
        st.link_button(f"See every size on {photo.site}'s site", photo.page_url)


def photo_grid(photos: list[Photo], key: str) -> None:
    """Small pictures in rows, each with a View button."""
    for start in range(0, len(photos), COLUMNS):
        row = st.columns(COLUMNS)
        for column, photo in zip(row, photos[start : start + COLUMNS], strict=False):
            with column:
                st.image(photo.thumbnail_url, width="stretch")
                st.caption(f"{photo.title}  \nCredit: {photo.credit}")
                if st.button("View", key=f"{key}_{photo.id}", width="stretch"):
                    st.session_state[f"{key}_selected"] = photo.id
                    st.rerun()


def show_photos(photos: list[Photo], key: str) -> None:
    """The chosen picture, large, above the grid."""
    chosen = selected_photo(photos, key)
    if chosen is not None:
        show_photo(chosen)
    photo_grid(photos, key)


def show_results(query: str, key: str) -> None:
    """The pictures for a search: a count, the chosen picture, and a grid.

    The page box is new for each search, so a new search starts on page 1.
    """
    first = load_photos(query, 1)
    hits = total_hits(first)
    if not hits:
        st.info("No pictures found. Try other words, or a different choice.")
        return
    pages = page_count(hits, nasa_images.PAGE_SIZE)
    page = int(
        st.number_input(
            f"Page (of {pages:,})",
            min_value=1,
            max_value=pages,
            value=1,
            key=f"{key}_page_{query}",
        )
    )
    reply = first if page == 1 else load_photos(query, page)
    photos = parse_photos(reply)
    st.caption(f"{hits:,} pictures found. Click View to see one large.")
    show_photos(photos, key)


def explore_tab() -> None:
    words = st.text_input(
        "Search for an object",
        placeholder="Crab Nebula, Saturn, Andromeda...",
        key="explore_words",
    )
    left, right = st.columns(2)
    types = [ANY, *OBJECT_TYPES]
    object_type = left.selectbox(
        "Type", types, index=types.index(DEFAULT_TYPE), key="explore_type"
    )
    telescope = right.selectbox(
        "Telescope or camera",
        [ANY, *(t.name for t in NASA_TELESCOPES)],
        key="explore_telescope",
    )
    query = build_query(words, object_type or ANY, telescope or ANY)
    if not query:
        st.info("Type a name, or pick a type or a telescope.")
        return
    show_results(query, key="explore")


def webb_pictures() -> None:
    photos = load_webb()
    if not photos:
        st.info("ESA/Webb has no pictures to show right now. Try again later.")
        return
    st.caption(f"{WEBB_NOTE} Click View to see one large.")
    show_photos(photos, key="webb")


def nasa_pictures(telescope: Telescope) -> None:
    """The telescope's pictures in NASA's library, narrowed by type."""
    # Each telescope keeps its own Type box, since their Type lists differ
    object_type = st.selectbox(
        "Type", types_for(telescope), key=f"scope_type_{telescope.name}"
    )
    query = build_query("", object_type or ANY, telescope.name)
    show_results(query, key="scope")


def telescope_tab() -> None:
    name = st.selectbox(
        "Telescope or camera", [t.name for t in TELESCOPES], key="scope_name"
    )
    telescope = telescope_named(name or TELESCOPES[0].name) or TELESCOPES[0]
    st.markdown(f"**Where:** {telescope.where}  \n**What it sees:** {telescope.sees}")
    if telescope.source == ESA_WEBB:
        webb_pictures()
    else:
        nasa_pictures(telescope)


def show_launch(launch: Launch) -> None:
    """One launch, with its mission and an approved photo when there is one."""
    with st.container(border=True):
        st.subheader(launch.name)
        st.markdown("  \n".join(launch_details(launch)))
        if launch.mission_description:
            st.write(launch.mission_description)
        if launch.photo is not None:
            st.image(launch.photo.url, width="stretch")
            license_text = launch.photo.license
            if launch.photo.license_url:
                license_text = f"[{license_text}]({launch.photo.license_url})"
            st.caption(f"Photo: {launch.photo.credit}, {license_text}")


def spaceflight_tab() -> None:
    upcoming_reply, past_reply = load_launches()
    planned, past = split_launches(
        parse_launches(upcoming_reply), parse_launches(past_reply)
    )
    st.caption(LAUNCH_NOTE)
    which = st.radio("Show", [PLANNED, PAST], horizontal=True, key="flights_which")
    launches = past if which == PAST else planned
    providers = sorted({launch.provider for launch in launches if launch.provider})
    chosen = st.multiselect(
        "Launch provider", providers, key=f"flights_providers_{which}"
    )
    if chosen:
        launches = [launch for launch in launches if launch.provider in chosen]
    if not launches:
        st.info("No launches match.")
        return
    st.dataframe(launch_rows(launches), hide_index=True, placeholder="—")
    by_id = {launch.id: launch for launch in launches}
    chosen_id = st.selectbox(
        "See a launch's details",
        list(by_id),
        format_func=lambda i: f"{by_id[i].time:%b %d, %Y} - {by_id[i].name}",
        key=f"flights_launch_{which}",
    )
    show_launch(by_id.get(chosen_id or "", launches[0]))


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    st.set_page_config(page_title="Outer Space Exploration and Images", layout="wide")
    st.title("Outer Space Exploration and Images")
    st.write(
        "Pictures of planets, nebulae, galaxies, and more from NASA and "
        "ESA/Webb, by object and by the telescope or camera that took them, "
        "plus past and planned spaceflights."
    )
    explore, scopes, flights = st.tabs(
        ["Explore", "Telescopes and cameras", "Spaceflights"]
    )
    for tab, show in [
        (explore, explore_tab),
        (scopes, telescope_tab),
        (flights, spaceflight_tab),
    ]:
        with tab:
            try:
                show()
            except ApiError as exc:
                st.error(str(exc))

    st.caption(CREDIT)


if __name__ == "__main__":
    main()
