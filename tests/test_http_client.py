import pytest
import requests
from conftest import FakeSession, as_session
from requests.adapters import HTTPAdapter

from http_client import (
    RETRY_STATUSES,
    USER_AGENT,
    ApiError,
    get_json,
    get_page,
    make_session,
)

URL = "https://example.com/api"


def test_session_retries_busy_replies_and_names_the_app() -> None:
    with make_session() as session:
        adapter = session.get_adapter("https://example.com")
        assert isinstance(adapter, HTTPAdapter)
        retry = adapter.max_retries
        assert retry.total == 3
        assert retry.backoff_factor == 1
        assert set(retry.status_forcelist or []) == set(RETRY_STATUSES)
        assert retry.respect_retry_after_header is False
        assert session.headers["User-Agent"] == USER_AGENT


def test_get_json_returns_the_reply() -> None:
    fake = FakeSession({URL: b'{"answer": 42}'})
    assert get_json(as_session(fake), "Test API", URL, {"q": "x"}) == {"answer": 42}
    assert fake.calls == [(URL, {"q": "x"})]


@pytest.mark.parametrize(
    "reply",
    [requests.ConnectionError("no network"), 503],
    ids=["no network", "server error"],
)
def test_get_json_failure_says_which_api(reply: Exception | int) -> None:
    fake = FakeSession({URL: reply})
    with pytest.raises(ApiError, match="Test API didn't answer"):
        get_json(as_session(fake), "Test API", URL, {})


@pytest.mark.parametrize("body", [b"not json", b"[1, 2]"], ids=["not json", "list"])
def test_get_json_unreadable_reply(body: bytes) -> None:
    fake = FakeSession({URL: body})
    with pytest.raises(ApiError, match="couldn't be read"):
        get_json(as_session(fake), "Test API", URL, {})


def test_get_page_returns_bytes() -> None:
    fake = FakeSession({URL: "Özsaraç".encode()})
    assert get_page(as_session(fake), "Test site", URL) == "Özsaraç".encode()
    assert fake.calls == [(URL, None)]


def test_get_page_failure() -> None:
    fake = FakeSession({})
    with pytest.raises(ApiError, match="Test site didn't answer"):
        get_page(as_session(fake), "Test site", URL)
