# Changelog

All notable changes to this project are listed here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[1.0.0]: https://github.com/datalogicpro/outerspace-exploration-and-images/releases/tag/v1.0.0
