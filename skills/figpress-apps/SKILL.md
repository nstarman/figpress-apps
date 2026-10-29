---
name: figpress-apps
description: Build an interactive webapp for a scientific paper with figpress-apps — an interactive counterpart of a figure (draggable views, linked panels, sliders) published as a static site and as one archivable HTML file, also usable in Jupyter/marimo. Use when asked for an interactive figure, explorer or webapp for a paper, when working in a repository's webapps/ folder, or when a repository depends on figpress-apps.
---

# Building a figpress-apps webapp

figpress-apps = a Python package (export data, build, serve, test, notebook widget) carrying a small
browser library of plain ES modules. No build step, no framework, no CDN. Read
[references/conventions.md](references/conventions.md) before writing any JS: its rules are
enforced by `figpress-apps build`.

## 0. Set up

In the paper repository (Python ≥ 3.11):

```bash
uv add "figpress-apps==YYYY.MM.DD"                   # pin a release (PyPI)
uv add --dev "figpress-apps[notebook]==YYYY.MM.DD"   # optional, notebooks
```

## 1. Scaffold

Copy [assets/template/](assets/template/) to `webapps/<name>/`: `index.html`, `widget.js` (the
app), `science.js` (pure science), `science.test.js`, `export.py`. Rename the dataset in
`export.py` and `widget.js` together, and adapt the `meta` keys `widget.js` reads (the template's
`meta.view`). The template projects 3-D points for a viewing direction; for a 2-D app keep its
structure and put your state (e.g. an angle) in `views[id]` — see
[references/components.md](references/components.md) (`skypanel` is the general 2-D panel).

## 2. Export the data — `export.py`

Write the arrays the page needs with `figpress_apps.export(out, name, arrays, meta=…)`
([references/data-contract.md](references/data-contract.md)). Rules:

- Allowed dtypes: float32/64, int8–32, uint8–32, bool. No int64 or strings (put strings in `meta`).
- float64 is kept unless you pass `narrow=[…]`; narrowing is checked against each array's range
  and fails loudly (e.g. MJD times). Never cast silently yourself.
- Precompute in Python whatever does not change with interaction (frames, squashed coordinates,
  textures). Put per-interaction work in `science.js`.
- In a showyourwork paper, run it from a Snakemake rule that depends on the pipeline's outputs.

## 3. Write the science — `science.js`

Pure functions, no DOM: given data and the interactive state (a view direction, a slider value),
return the numbers and arrays to draw plus a readout string. Port only the per-interaction part of
the paper's Python, and check it with `science.test.js` against numbers computed by the paper's
Python (paste them in with their source, or export them):

```bash
uv run figpress-apps test webapps/<name>
```

The JS must reproduce the paper. A figure that disagrees with the paper is worse than none.

## 4. Compose the app — `widget.js`

The app is an anywidget module (`export default { async render({ model, el, signal }) }`) that:
loads data with `loadData` (from the model in notebooks, by name on the web — copy the template's
first lines), initialises model state, builds the layout, mounts components
([references/components.md](references/components.md)) with options, and disposes them on
`signal`. State rules:

- Shared state lives in the model (`camera`, `views`, …); values are **replaced, never mutated**.
- Derived per-interaction data goes through callbacks (`compute`), never into the model.
- Call `model.save_changes()` at the end of an interaction (pointer-up, slider change), not per move.

## 5. Build, view, test

```bash
uv run python webapps/<name>/export.py --out build/data
uv run figpress-apps build webapps/<name> --data build/data/<dataset> --out build/site/<name> --single-file build/<name>.html
uv run figpress-apps serve build/site            # http://127.0.0.1:8000/<name>/ ; the single file just opens
uv run figpress-apps test webapps/<name>
```

The build fails on relative imports, `import.meta.url`, unresolvable or remote imports and
datasets of another data-format version — fix the code, never work around the check. Check both
outputs in a browser: the served page and the single file from disk. To read the panels'
readouts headlessly, use [references/check-page.md](references/check-page.md).

## 6. Notebook (optional)

```python
from figpress_apps.anywidget import Widget
w = Widget(app="webapps/<name>/widget.js", data="build/data/<dataset>"); w
w.views   # state syncs back after each interaction
```

JupyterLab must run in an environment with `anywidget` and `ipywidgets` installed.

## Worked example

[references/worked-example.md](references/worked-example.md) walks through figpress-apps' globe example
(rotatable globe, draggable viewing directions, four linked sky panels reproducing a paper's numbers).
