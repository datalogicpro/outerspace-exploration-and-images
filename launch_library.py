"""Get past and planned launches from Launch Library 2, by The Space Devs.

It needs no key, but allows only 15 requests an hour without one, so the
page saves each reply for an hour.

API docs: https://ll.thespacedevs.com/docs/
"""

import os
from typing import Any

import requests

from http_client import get_json

# LAUNCH_LIBRARY_URL can point the app at a stand-in server, as the browser
# test does
BASE_URL = os.environ.get("LAUNCH_LIBRARY_URL", "https://ll.thespacedevs.com/2.3.0")
SOURCE = "Launch Library"
LIMIT = 40


def upcoming_launches(session: requests.Session) -> dict[str, Any]:
    """The next launches. It can include ones from the last few hours, which
    the page moves to the past list."""
    return get_json(
        session, SOURCE, f"{BASE_URL}/launches/upcoming/", {"limit": str(LIMIT)}
    )


def past_launches(session: requests.Session) -> dict[str, Any]:
    """The most recent launches."""
    return get_json(
        session, SOURCE, f"{BASE_URL}/launches/previous/", {"limit": str(LIMIT)}
    )
