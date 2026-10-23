"""Turn Launch Library 2 replies into clean launch records.

Every photo in a reply comes with its own license. Only photos under a
license on the approved list are kept; any other photo is left out, and the
launch shows without one.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

# Licenses that allow showing a photo on a non-commercial site, with credit
APPROVED_LICENSES = (
    "NASA Image and Media Guidelines",
    "Copernicus Image Use Policy",
    "Public Domain",
    "CC0",
)
# Creative Commons licenses that start this way all allow it with credit
APPROVED_LICENSE_PREFIX = "CC BY"

# Statuses that mean the launch already happened
FINISHED = ("Success", "Failure", "Partial Failure")


@dataclass(frozen=True)
class LaunchPhoto:
    url: str
    credit: str
    license: str
    license_url: str | None


@dataclass(frozen=True)
class Launch:
    id: str
    name: str
    status: str
    finished: bool
    time: datetime
    time_precision: str
    provider: str
    provider_type: str
    rocket: str
    mission: str
    mission_type: str
    mission_description: str
    orbit: str
    launch_site: str
    country: str
    photo: LaunchPhoto | None


def approved(license_name: str) -> bool:
    return license_name in APPROVED_LICENSES or license_name.startswith(
        APPROVED_LICENSE_PREFIX
    )


def parse_photo(image: dict[str, Any] | None) -> LaunchPhoto | None:
    """The launch photo, or None when it has no approved license."""
    if not image or not image.get("image_url"):
        return None
    license_info = image.get("license") or {}
    license_name = license_info.get("name") or ""
    if not approved(license_name):
        return None
    return LaunchPhoto(
        url=image["image_url"],
        credit=image.get("credit") or "Unknown",
        license=license_name,
        license_url=license_info.get("link"),
    )


def name_of(value: dict[str, Any] | None, key: str = "name") -> str:
    return str((value or {}).get(key) or "")


def parse_launch(item: dict[str, Any]) -> Launch:
    status = item.get("status") or {}
    provider = item.get("launch_service_provider") or {}
    mission = item.get("mission") or {}
    pad = item.get("pad") or {}
    return Launch(
        id=item["id"],
        name=item["name"],
        status=name_of(status),
        finished=status.get("abbrev") in FINISHED,
        time=datetime.fromisoformat(item["net"]),
        time_precision=name_of(item.get("net_precision")),
        provider=name_of(provider),
        provider_type=name_of(provider.get("type")),
        rocket=name_of((item.get("rocket") or {}).get("configuration"), "full_name"),
        mission=name_of(mission),
        mission_type=str(mission.get("type") or ""),
        mission_description=str(mission.get("description") or ""),
        orbit=name_of(mission.get("orbit")),
        launch_site=", ".join(
            part for part in (name_of(pad), name_of(pad.get("location"))) if part
        ),
        country=name_of(pad.get("country")),
        photo=parse_photo(item.get("image")),
    )


def parse_launches(reply: dict[str, Any]) -> list[Launch]:
    return [parse_launch(item) for item in reply.get("results", [])]


def split_launches(
    upcoming: list[Launch], past: list[Launch]
) -> tuple[list[Launch], list[Launch]]:
    """Planned launches soonest first, and past launches newest first.

    Launches from the last few hours can come back in both lists, so any
    finished launch moves to the past list, and each launch shows only once.
    """
    planned = [launch for launch in upcoming if not launch.finished]
    finished = {launch.id: launch for launch in past}
    for launch in upcoming:
        if launch.finished:
            finished.setdefault(launch.id, launch)
    done = sorted(finished.values(), key=lambda launch: launch.time, reverse=True)
    return sorted(planned, key=lambda launch: launch.time), done


def launch_rows(launches: list[Launch]) -> list[dict[str, Any]]:
    """One table row per launch."""
    return [
        {
            "Date (UTC)": launch.time,
            "Exact to": launch.time_precision,
            "Launch": launch.name,
            "Provider": launch.provider,
            "Mission": launch.mission,
            "Orbit": launch.orbit,
            "Launch site": launch.launch_site,
            "Country": launch.country,
            "Status": launch.status,
        }
        for launch in launches
    ]


def launch_details(launch: Launch) -> list[str]:
    """Everything about one launch, one line each, for the details box."""
    when = f"{launch.time:%B %d, %Y at %H:%M} UTC"
    if launch.time_precision and launch.time_precision not in ("Second", "Minute"):
        when += f" (not final: exact to the {launch.time_precision.lower()})"
    provider = launch.provider
    if launch.provider_type:
        provider += f" ({launch.provider_type.lower()})"
    mission = launch.mission
    if launch.mission_type:
        mission += f" ({launch.mission_type})"
    lines = [
        f"**Date:** {when}",
        f"**Status:** {launch.status}",
        f"**Provider:** {provider}",
        f"**Rocket:** {launch.rocket}",
        f"**Mission:** {mission}",
        f"**Orbit:** {launch.orbit}",
        f"**Launch site:** {launch.launch_site}",
        f"**Country:** {launch.country}",
    ]
    return [line for line in lines if not line.endswith(":** ")]
