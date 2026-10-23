from telescopes import (
    ANY,
    ESA_WEBB,
    NASA_LIBRARY,
    OBJECT_TYPES,
    TELESCOPES,
    build_query,
    telescope_named,
    types_for,
)


def test_telescope_named() -> None:
    hubble = telescope_named("Hubble Space Telescope")
    assert hubble is not None and hubble.search_words == "Hubble"
    assert telescope_named("Not a telescope") is None


def test_webb_comes_from_esa_webb_not_nasa() -> None:
    webb = telescope_named("James Webb Space Telescope")
    assert webb is not None and webb.source == ESA_WEBB
    others = [t for t in TELESCOPES if t is not webb]
    assert all(t.source == NASA_LIBRARY for t in others)


def test_types_for_leaves_out_skipped_types() -> None:
    juno = telescope_named("Juno")
    assert juno is not None
    assert types_for(juno) == [ANY, "Planets", "Moons"]
    hubble = telescope_named("Hubble Space Telescope")
    assert hubble is not None
    assert types_for(hubble) == [ANY, *OBJECT_TYPES]


def test_build_query() -> None:
    assert build_query(" Crab ", "Nebulae", "Hubble Space Telescope") == (
        "Crab nebula Hubble"
    )
    assert build_query("", "Star clusters", ANY) == "star cluster"
    assert build_query("", ANY, ANY) == ""
