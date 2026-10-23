"""The real page in a real browser (Chrome, through Playwright).

Streamlit runs the app in its own process, and a small stand-in server
answers for NASA, Launch Library, and ESA/Webb from the saved replies, so
the test doesn't reach those sites.
"""

import os
import socket
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
import requests
from conftest import read_bytes
from playwright.sync_api import Page, expect

PROJECT = Path(__file__).parent.parent
STARTUP_SECONDS = 60


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port: int = sock.getsockname()[1]
        return port


def stand_in_handler(base: str) -> type[BaseHTTPRequestHandler]:
    """Answers each source's paths from the saved replies. The Webb feed's
    links point back at this server."""
    feed = read_bytes("webb_feed.xml").replace(b"https://esawebb.org", base.encode())
    replies = {
        "/search": read_bytes("images.json"),
        "/launches/upcoming/": read_bytes("upcoming.json"),
        "/launches/previous/": read_bytes("past.json"),
        "/images/feed/": feed,
        "/images/potm2610a/": read_bytes("webb_observation.html"),
    }

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            body = replies.get(self.path.split("?")[0])
            self.send_response(200 if body is not None else 404)
            self.end_headers()
            self.wfile.write(body or b"")

        def log_message(self, format: str, *args: object) -> None:
            return None

    return Handler


def is_ready(url: str) -> bool:
    try:
        return requests.get(f"{url}/_stcore/health", timeout=2).ok
    except requests.ConnectionError:
        return False


def wait_until_ready(url: str) -> bool:
    """True once Streamlit answers its health check, False if it never does."""
    deadline = time.monotonic() + STARTUP_SECONDS
    while time.monotonic() < deadline:
        if is_ready(url):
            return True
        time.sleep(0.5)
    return False


@pytest.fixture(scope="module")
def stand_in() -> Iterator[str]:
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    server = ThreadingHTTPServer(("127.0.0.1", port), stand_in_handler(base))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield base
    server.shutdown()
    server.server_close()


@pytest.fixture(scope="module")
def app_url(stand_in: str) -> Iterator[str]:
    """Starts Streamlit pointed at the stand-in server, and waits until it's
    ready."""
    port = free_port()
    env = os.environ | {
        "NASA_IMAGES_URL": stand_in,
        "LAUNCH_LIBRARY_URL": stand_in,
        "ESA_WEBB_FEED_URL": f"{stand_in}/images/feed/",
    }
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.headless=true",
        f"--server.port={port}",
        "--browser.gatherUsageStats=false",
    ]
    process = subprocess.Popen(
        command,
        cwd=PROJECT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://localhost:{port}"
    try:
        if not wait_until_ready(url):
            pytest.fail("Streamlit didn't start")
        yield url
    finally:
        process.terminate()
        process.wait(timeout=30)


def test_view_a_picture_large(page: Page, app_url: str) -> None:
    page.goto(app_url)
    explore = page.get_by_role("tabpanel", name="Explore")
    expect(explore.get_by_text("14 pictures found")).to_be_visible(timeout=30_000)
    explore.get_by_role("button", name="View").first.click()
    expect(
        explore.get_by_role("heading", name="Most Detailed Image of the Crab Nebula")
    ).to_be_visible()
    expect(explore.get_by_text("See every size on NASA's site")).to_be_visible()


def test_webb_pictures(page: Page, app_url: str) -> None:
    page.goto(app_url)
    page.get_by_role("tab", name="Telescopes and cameras").click()
    scopes = page.get_by_role("tabpanel", name="Telescopes and cameras")
    scopes.get_by_role("combobox", name="Telescope or camera").click()
    page.get_by_role("option", name="James Webb Space Telescope").click()
    expect(scopes.get_by_text("Stars brewing in a nebulous cauldron")).to_be_visible(
        timeout=30_000
    )
    expect(scopes.get_by_text("Credit: ESA/Webb, NASA & CSA").first).to_be_visible()


def test_spaceflights(page: Page, app_url: str) -> None:
    page.goto(app_url)
    page.get_by_role("tab", name="Spaceflights").click()
    flights = page.get_by_role("tabpanel", name="Spaceflights")
    expect(
        flights.get_by_role("heading", name="Falcon 9 Block 5 | Starlink Group 15-15")
    ).to_be_visible(timeout=30_000)
    flights.get_by_text("Past", exact=True).click()
    expect(
        flights.get_by_role("heading", name="Ceres-1S | Xiguang-4 01")
    ).to_be_visible()
