"""Calls to the outside sources: NASA's image library, ESA/Webb, and Launch
Library 2.

Busy-server replies are retried with backoff, every request is logged with
its own ID so a failure can be traced, and any failure becomes an ApiError
with a message the page can show.
"""

import logging
import uuid
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TIMEOUT = 30  # seconds

# Replies that mean "try again later"
RETRY_STATUSES = (429, 500, 502, 503, 504)

# Tells each site which app is calling and where to find it
USER_AGENT = (
    "outerspace-exploration-and-images "
    "(https://github.com/datalogicpro/outerspace-exploration-and-images)"
)

log = logging.getLogger(__name__)


class ApiError(Exception):
    """An outside source could not be reached or sent a bad reply."""


def make_session() -> requests.Session:
    """A session that retries busy-server replies: after 1, 2, then 4 seconds.

    A server's "Retry-After" wait is ignored, since it can ask for a long
    wait and the page shouldn't hang that long.
    """
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=RETRY_STATUSES,
        allowed_methods=["GET"],
        respect_retry_after_header=False,
    )
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch(
    session: requests.Session,
    source: str,
    url: str,
    params: dict[str, str] | None,
    request_id: str,
) -> requests.Response:
    """One GET request. Raises ApiError when it fails."""
    log.info("request_id=%s GET %s params=%s", request_id, url, params)
    try:
        response = session.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        log.error("request_id=%s failed: %s", request_id, exc)
        raise ApiError(
            f"{source} didn't answer (request {request_id}). "
            "Please try again in a few minutes."
        ) from exc
    return response


def get_json(
    session: requests.Session, source: str, url: str, params: dict[str, str]
) -> dict[str, Any]:
    """Call one API and return its reply.

    source names the API in log lines and error messages, like
    "NASA's image library". Raises ApiError when the call fails.
    """
    request_id = uuid.uuid4().hex[:8]
    response = fetch(session, source, url, params, request_id)
    try:
        reply = response.json()
    except ValueError as exc:
        log.error("request_id=%s sent a reply that isn't JSON", request_id)
        raise ApiError(
            f"{source} sent a reply that couldn't be read (request {request_id})."
        ) from exc

    if not isinstance(reply, dict):
        log.error("request_id=%s sent an unexpected reply", request_id)
        raise ApiError(
            f"{source} sent a reply that couldn't be read (request {request_id})."
        )

    log.info("request_id=%s OK", request_id)
    return reply


def get_page(session: requests.Session, source: str, url: str) -> bytes:
    """Get one web page or feed. Raises ApiError when it fails.

    It returns bytes, not text, so the reader can use the character set the
    page itself names (like "utf-8"), since the server doesn't always say.
    """
    request_id = uuid.uuid4().hex[:8]
    response = fetch(session, source, url, None, request_id)
    log.info("request_id=%s OK", request_id)
    return response.content
