"""Shared test helpers: saved replies from the real sources, and a stand-in
for requests.Session that answers from them instead of the internet."""

import io
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, Self, cast

import pytest
import requests

DATA = Path(__file__).parent / "data"

NASA_SEARCH = "https://images-api.nasa.gov/search"
UPCOMING = "https://ll.thespacedevs.com/2.3.0/launches/upcoming/"
PAST = "https://ll.thespacedevs.com/2.3.0/launches/previous/"
WEBB_FEED = "https://esawebb.org/images/feed/"
WEBB_PAGE = "https://esawebb.org/images/{}/"

# What a stand-in route sends back: the reply's bytes, an error status code,
# an exception to raise, or a function of the request's params
Reply = bytes | int | Exception | Callable[[dict[str, str]], bytes]


def read_bytes(name: str) -> bytes:
    return (DATA / name).read_bytes()


def read_json(name: str) -> dict[str, Any]:
    reply: dict[str, Any] = json.loads(read_bytes(name))
    return reply


def to_bytes(reply: dict[str, Any]) -> bytes:
    return json.dumps(reply).encode()


def make_response(url: str, status: int, body: bytes) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    response.url = url
    response.raw = io.BytesIO(body)
    return response


class FakeSession:
    """Answers GET requests from a table of routes, and records each one."""

    def __init__(self, routes: dict[str, Reply]) -> None:
        self.routes = routes
        self.headers: dict[str, str] = {}
        self.calls: list[tuple[str, dict[str, str] | None]] = []

    def get(
        self, url: str, params: dict[str, str] | None = None, timeout: float = 0
    ) -> requests.Response:
        self.calls.append((url, params))
        reply = self.routes.get(url, 404)
        if isinstance(reply, Exception):
            raise reply
        if isinstance(reply, int):
            return make_response(url, reply, b"")
        if callable(reply):
            return make_response(url, 200, reply(params or {}))
        return make_response(url, 200, reply)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def as_session(fake: FakeSession) -> requests.Session:
    """The stand-in, typed as the real session the app's functions take."""
    return cast(requests.Session, fake)


def nasa_reply(params: dict[str, str]) -> bytes:
    """NASA's library: no pictures for "nothing here", many for "Saturn",
    and the saved reply for anything else."""
    reply = read_json("images.json")
    if "nothing here" in params.get("q", ""):
        reply["collection"]["items"] = []
        reply["collection"]["metadata"]["total_hits"] = 0
    elif "Saturn" in params.get("q", ""):
        reply["collection"]["metadata"]["total_hits"] = 100
    return to_bytes(reply)


def webb_routes() -> dict[str, Reply]:
    """The Webb feed, and its pages: an observation, an artwork, one with no
    credit line, and one that fails."""
    return {
        WEBB_FEED: read_bytes("webb_feed.xml"),
        WEBB_PAGE.format("potm2610a"): read_bytes("webb_observation.html"),
        WEBB_PAGE.format("weic2618a"): read_bytes("webb_artwork.html"),
        WEBB_PAGE.format("weic2621b"): read_bytes("webb_no_credit.html"),
        WEBB_PAGE.format("weic2617e"): 500,
    }


@pytest.fixture
def routes() -> dict[str, Reply]:
    """Every source the app calls, answered from saved replies."""
    return {
        NASA_SEARCH: nasa_reply,
        UPCOMING: read_bytes("upcoming.json"),
        PAST: read_bytes("past.json"),
        **webb_routes(),
    }
