"""Search NASA's Image and Video Library. It needs no key.

API docs: https://images.nasa.gov/docs/images.nasa.gov_api_docs.pdf
"""

import os
from typing import Any

import requests

from http_client import get_json

# NASA_IMAGES_URL can point the app at a stand-in server, as the browser test does
BASE_URL = os.environ.get("NASA_IMAGES_URL", "https://images-api.nasa.gov")
SOURCE = "NASA's image library"
PAGE_SIZE = 24


def search_images(
    session: requests.Session, query: str, page: int = 1
) -> dict[str, Any]:
    """One page of pictures matching the search words."""
    params = {
        "q": query,
        "media_type": "image",
        "page": str(page),
        "page_size": str(PAGE_SIZE),
    }
    return get_json(session, SOURCE, f"{BASE_URL}/search", params)
