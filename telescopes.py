"""The telescopes and cameras, and the kinds of objects, the page can search for.

NASA's keywords aren't consistent, so each choice adds search words that
NASA's library matches against a picture's title, description, and keywords.

Webb's pictures come from ESA/Webb instead, since NASA's library holds
mostly pictures of Webb being built, not pictures Webb took.
"""

from dataclasses import dataclass

# Where a telescope's pictures come from
NASA_LIBRARY = "NASA"
ESA_WEBB = "ESA/Webb"


@dataclass(frozen=True)
class Telescope:
    name: str
    search_words: str
    where: str
    sees: str
    source: str = NASA_LIBRARY
    # Types whose pictures for this telescope are mostly not of space
    skip_types: tuple[str, ...] = ()


TELESCOPES = (
    Telescope(
        "Hubble Space Telescope",
        "Hubble",
        "Orbiting Earth since 1990",
        "Visible, ultraviolet, and near-infrared light",
    ),
    Telescope(
        "James Webb Space Telescope",
        "Webb",
        "About 1.5 million km from Earth, launched in December 2021",
        "Infrared light",
        source=ESA_WEBB,
    ),
    Telescope(
        "Chandra X-ray Observatory",
        "Chandra",
        "Orbiting Earth since 1999",
        "X-rays",
        skip_types=("Comets",),
    ),
    Telescope(
        "Spitzer Space Telescope",
        "Spitzer",
        "Followed Earth around the Sun from 2003 to 2020",
        "Infrared light",
    ),
    Telescope(
        "Cassini",
        "Cassini",
        "Orbited Saturn from 2004 to 2017",
        "Visible and infrared light",
    ),
    Telescope(
        "Juno",
        "Juno",
        "Orbiting Jupiter since 2016",
        "Visible light (JunoCam)",
        skip_types=("The Sun",),
    ),
    Telescope(
        "New Horizons",
        "New Horizons",
        "Flew past Pluto in July 2015",
        "Visible and infrared light",
    ),
    Telescope(
        "Curiosity rover",
        "Curiosity rover",
        "On Mars since August 2012",
        "Visible light",
    ),
    Telescope(
        "Perseverance rover",
        "Perseverance rover",
        "On Mars since February 2021",
        "Visible light",
        skip_types=("Planets",),
    ),
)

# Kinds of objects, and the words that find them
OBJECT_TYPES = {
    "Planets": "planet",
    "Moons": "moon",
    "Nebulae": "nebula",
    "Galaxies": "galaxy",
    "Star clusters": "star cluster",
    "Comets": "comet",
    "The Sun": "sun",
}

ANY = "Any"

# The telescopes NASA's library can be searched for
NASA_TELESCOPES = tuple(t for t in TELESCOPES if t.source == NASA_LIBRARY)


def telescope_named(name: str) -> Telescope | None:
    return next((t for t in TELESCOPES if t.name == name), None)


def types_for(telescope: Telescope) -> list[str]:
    """The Type choices for a telescope: Any, then each type it suits."""
    return [ANY, *(t for t in OBJECT_TYPES if t not in telescope.skip_types)]


def build_query(words: str, object_type: str, telescope: str) -> str:
    """The search words for NASA: what was typed, plus the type and telescope."""
    parts = [words.strip()]
    if object_type in OBJECT_TYPES:
        parts.append(OBJECT_TYPES[object_type])
    chosen = telescope_named(telescope)
    if chosen is not None:
        parts.append(chosen.search_words)
    return " ".join(part for part in parts if part)
