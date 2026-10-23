# Outer Space Exploration and Images

[![Tests](https://github.com/datalogicpro/outerspace-exploration-and-images/actions/workflows/tests.yml/badge.svg)](https://github.com/datalogicpro/outerspace-exploration-and-images/actions/workflows/tests.yml)
[![Live source check](https://github.com/datalogicpro/outerspace-exploration-and-images/actions/workflows/live.yml/badge.svg)](https://github.com/datalogicpro/outerspace-exploration-and-images/actions/workflows/live.yml)

A dashboard of space pictures from NASA and ESA/Webb, by object and by the telescope or camera that took them, plus past and planned spaceflights.

**Live demo:** https://datalogicpro-outerspace-exploration-and-images.streamlit.app

## What it shows

The page has three tabs:

| Tab | What's in it |
|---|---|
| Explore | Search NASA's pictures by name, type of object, and telescope or camera |
| Telescopes and cameras | Where each telescope or camera is, what light it sees, and its pictures |
| Spaceflights | Planned and past rocket launches from around the world, with details for each |

On the picture tabs, click **View** under a picture to see it large, with its date, credit, description, and a link to every size on its site.

## The telescopes and cameras

| Telescope or camera | Where | What it sees |
|---|---|---|
| Hubble Space Telescope | Orbiting Earth since 1990 | Visible, ultraviolet, and near-infrared light |
| James Webb Space Telescope | About 1.5 million km from Earth, launched in December 2021 | Infrared light |
| Chandra X-ray Observatory | Orbiting Earth since 1999 | X-rays |
| Spitzer Space Telescope | Followed Earth around the Sun from 2003 to 2020 | Infrared light |
| Cassini | Orbited Saturn from 2004 to 2017 | Visible and infrared light |
| Juno | Orbiting Jupiter since 2016 | Visible light (JunoCam) |
| New Horizons | Flew past Pluto in July 2015 | Visible and infrared light |
| Curiosity rover | On Mars since August 2012 | Visible light |
| Perseverance rover | On Mars since February 2021 | Visible light |

## Which pictures are shown

- **Pictures of space only.** NASA's library also holds pictures of hardware, events, and drawings. The page leaves out pictures taken by a photographer on the ground, pictures from Kennedy Space Center (rockets and spacecraft being prepared), and pictures whose titles show a drawing, chart, test, or event.
- **Webb's pictures come from ESA/Webb.** NASA's library holds mostly pictures of Webb being built, so the Webb choice shows the newest pictures from ESA/Webb instead. Only observations are shown, not artwork or charts.
- **No one else's copyright.** NASA pictures marked with someone else's copyright are left out, and launch photos are shown only when their license allows it.

## Spaceflight times

- Times are in **UTC**, also called world time.
- Launch data refreshes once an hour, so a launch happening today, or in the last hour, can show in either list. If you don't find one in **Planned**, check **Past**, and the other way around.
- A planned launch's date may not be final. The **Exact to** column shows whether the time is set to the second, the hour, the day, or only the month.

## How to run

This project uses [uv](https://docs.astral.sh/uv/) and Python 3.13.

1. Install everything:

```
   uv sync
```

2. Start the dashboard:

```
   uv run streamlit run app.py
```

3. Open it in your browser:

```
   http://localhost:8501
```

No API key is needed.

## Tests

Run the tests:

```
uv run python -m pytest
```

- **Unit and page tests** check every part of the code with saved replies from each source, so they never reach the internet. Coverage must stay at 100%.
- **A browser test** starts the real page in Chrome, opens a picture large, picks Webb, and switches between planned and past launches. It uses a small stand-in server that sends the saved replies. It needs Google Chrome installed.
- **A live source check** calls the real NASA, Launch Library, and ESA/Webb sources and reads each reply the same way the page does, so a change on their side is caught. It is left out of the normal run. GitHub runs it once a day, and you can run it by hand:

```
  uv run python -m pytest -m live --no-cov
```

## How it's built

- **Retries with backoff:** busy-server replies are retried after 1, 2, then 4 seconds.
- **Logging with request IDs:** every call to a source is logged with its own ID, so a failure can be traced.
- **Caching:** each reply is saved for an hour, so the page doesn't call the sources on every click. Launch Library allows only 15 requests an hour without a key.
- **Safe feed reading:** the ESA/Webb feed is read with defusedxml, which refuses the tricks a bad feed could use to tie up the app.
- **Clear errors:** if a source doesn't answer, that tab shows a message and the other tabs keep working.
- **Checks on every change:** GitHub Actions runs Ruff, mypy, pip-audit, and the tests on every pull request.
- **Up-to-date dependencies:** Dependabot opens pull requests for new library and GitHub Actions versions.
- **Pre-commit hooks:** formatting, linting, and type checks run before every commit.

## Project files

| File | What's in it |
|---|---|
| `app.py` | The page: tabs, choices, and the calls to each source |
| `telescopes.py` | The telescopes and cameras, the kinds of objects, and the search words |
| `photos.py` | Turns NASA's replies into picture records, and leaves out pictures that aren't of space |
| `nasa_images.py` | Searches NASA's Image and Video Library |
| `esa_webb.py` | Gets Webb's newest pictures and their credit lines from ESA/Webb |
| `launch_library.py` | Gets planned and past launches from Launch Library 2 |
| `launches.py` | Turns launch replies into records, and keeps only photos with an allowed license |
| `http_client.py` | The calls to every source, with retries and logging |
| `tests/` | The tests and the saved replies they use |
| `.github/workflows/tests.yml` | Runs the checks and tests on GitHub |
| `.github/workflows/live.yml` | Runs the live source check once a day |

## Built with

Python, Streamlit, requests, Beautiful Soup, defusedxml, pytest, Playwright, Ruff, mypy, and uv.

## Data and credits

- **Pictures:** [NASA Image and Video Library](https://images.nasa.gov). NASA doesn't endorse this site. See [NASA's media guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/).
- **Webb pictures:** [ESA/Webb](https://esawebb.org), under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Each picture shows its own credit line. ESA/Webb doesn't endorse this site.
- **Launch data:** [The Space Devs, Launch Library 2](https://thespacedevs.com/llapi). Each launch photo shows its credit and license.

## License

MIT. See [LICENSE](LICENSE). The pictures and launch data belong to their sources, under their own terms above.

## Author

datalogicpro
