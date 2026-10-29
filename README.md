# figpress-apps

*Formerly **figkit** (renamed in 2026.10.28; the [changelog](CHANGELOG.md) says how to move an app).
Part of the [figpress](https://nstarkman.space/figpress/) family.*

A toolbox for webapps that are the interactive counterparts of scientific papers: data, plots and
movies that readers can explore next to the static PDF, built to keep working for years.

- **Python** exports a paper's arrays as plain `.npy` files with a manifest (readers can `np.load`
  them without figpress-apps), builds sites, serves previews and runs the app's JS tests.
- **Browser** code is plain ES modules and CSS — no build step, no framework, no CDN. Each site
  vendors the exact figpress-apps version it was built with.
- **Two outputs** from one source: a site for GitHub Pages, and a single HTML file that opens from
  disk, offline, for archives.
- **Same app in notebooks** (Jupyter, marimo) through anywidget, with state synced back to Python.

Gallery: <https://nstarkman.space/figpress-apps/> (published from releases).

## Install

Pin a release from [PyPI](https://pypi.org/project/figpress-apps/):

```bash
uv add "figpress-apps==2026.10.28"
uv add "figpress-apps[notebook]==2026.10.28"   # notebooks
```

figkit's releases (`v0.1.0`, `v0.2.0`) stay installable from their git tags.

## Use

```python
import figpress_apps
figpress_apps.export("build/data", "points", {"xyz": xyz}, meta={"title": "…"})
```

```bash
uv run figpress-apps build webapps/points --data build/data/points --out build/site/points --single-file build/points.html
uv run figpress-apps serve build/site
uv run figpress-apps test webapps/points
```

```python
from figpress_apps.anywidget import Widget
Widget(app="webapps/points/widget.js", data="build/data/points")
```

An app is an `index.html`, a `widget.js` (an anywidget module composing figpress-apps components) and a
DOM-free `science.js`. See [`examples/globe/`](examples/globe/) and the agent skills in
[`skills/`](skills/): `figpress-apps` (building a webapp) and `figpress-apps-upgrade` (moving one to a newer tag).

## Development

```bash
uv sync --all-extras
uv run pytest                                   # Python
uv run python tests/make_fixtures.py && node --test js-tests/*.test.js   # JS
uv run playwright install chromium webkit && uv run pytest -m smoke --browser chromium --browser webkit
```

Design and requirements: [`specs/001-figkit-v0-1/`](specs/001-figkit-v0-1/) (written as figkit). Rules:
[`.specify/memory/constitution.md`](.specify/memory/constitution.md).

License: MIT. The globe example's data: see [`examples/globe/SOURCE.md`](examples/globe/SOURCE.md).
