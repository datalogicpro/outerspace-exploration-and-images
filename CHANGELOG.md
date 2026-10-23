# Changelog

All notable changes to this project are listed here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-10-23

### Changed

- The Explore and Telescopes and cameras tabs are now one tab, Space telescopes and cameras. Webb is in its telescope list, and picking a telescope shows where it is and what light it sees.
- The Type list follows the telescope, leaving out types that bring up few or no space pictures for it.
- Webb's pictures can be narrowed by Type and search words.
- Previous page and Next page buttons replace the typed page box.

### Fixed

- Pictures checked by hand and found not to be of space are left out, using a list of titles in `blocked_titles.txt`.
- More pictures of people and events are left out, by title words like "team" and "engineers".
- A page whose pictures were all left out now says so, instead of showing nothing.

## [1.0.0] - 2026-10-23

### Added

- Explore tab: search NASA's pictures by name, type of object, and telescope or camera, with pages of results.
- Telescopes and cameras tab: where each one is, what light it sees, and its pictures, narrowed by type.
- Webb's newest pictures from ESA/Webb, observations only, each with its full credit line.
- Spaceflights tab: planned and past launches, a filter by launch provider, and details for each launch.
- Click View under a picture to see it large, with its date, credit, description, and a link to every size.
- Pictures that aren't of space are left out: ground photos, Kennedy Space Center pictures, and drawings, charts, tests, and events.
- Pictures with someone else's copyright are left out, and launch photos show only when their license allows it.
- Calls to every source with retries and backoff, request-ID logging, and hour-long caching.
- Tests with 100% coverage, a browser test in Chrome, and a daily live check of NASA, Launch Library, and ESA/Webb on GitHub.

[1.1.0]: https://github.com/datalogicpro/outerspace-exploration-and-images/releases/tag/v1.1.0
[1.0.0]: https://github.com/datalogicpro/outerspace-exploration-and-images/releases/tag/v1.0.0
