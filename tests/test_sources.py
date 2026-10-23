from conftest import NASA_SEARCH, PAST, UPCOMING, FakeSession, as_session, nasa_reply

import launch_library
import nasa_images


def test_search_images_asks_for_one_page_of_pictures() -> None:
    fake = FakeSession({NASA_SEARCH: nasa_reply})
    reply = nasa_images.search_images(as_session(fake), "Crab nebula", page=3)
    assert reply["collection"]["metadata"]["total_hits"] == 14
    assert fake.calls == [
        (
            NASA_SEARCH,
            {
                "q": "Crab nebula",
                "media_type": "image",
                "page": "3",
                "page_size": str(nasa_images.PAGE_SIZE),
            },
        )
    ]


def test_launch_lists() -> None:
    fake = FakeSession({UPCOMING: b'{"results": []}', PAST: b'{"results": [1]}'})
    assert launch_library.upcoming_launches(as_session(fake)) == {"results": []}
    assert launch_library.past_launches(as_session(fake)) == {"results": [1]}
    limit = {"limit": str(launch_library.LIMIT)}
    assert fake.calls == [(UPCOMING, limit), (PAST, limit)]
