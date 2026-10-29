# Worked example: the globe explorer (figpress-apps `examples/globe/`)

An interactive version of a paper's globe figure: four stellar streams in a halo's principal-axis
frame, a rotatable globe of viewing directions, and four linked sky panels that re-project each
stream and recompute, per point, the paper's non-concavity criterion while a marker is dragged.

| File | Role |
|---|---|
| `make_source.py`, `source.npz`, `SOURCE.md` | one-off extraction of the paper's arrays, with attribution |
| `export.py` | `source.npz` → dataset `globe`: per stream track, derivatives, particles, frame matrix `T`, globe-ready squashed lines; texture; `meta` with names, colours, paper views, camera |
| `science.js` | `streamFromData`, `classify(stream, view)` (project + classify → `{xy, points, mask, fraction, readout}`), `markerAxes` |
| `widget.js` | the app: loads data, initialises `camera`/`views` from `meta`, toolbar with reset buttons, mounts `globe` + four `skypanel`s with `compute: (v) => classify(stream, v)` |
| `index.html` | title, citation, `run(app, el)` |

Patterns to copy:

- **Frames**: data stay in each stream's own simulation frame; `T` maps the shared globe frame to it.
  `science.js` maps the view with `T` and builds the sky basis with `rotationToZ`.
- **Precompute in Python**: the radial squash of globe lines happens in `export.py`, once.
- **Acceptance numbers**: the JS reproduces the paper's fractions (48.0 / 16.2 / 87.6 / 87.2 %) at
  the paper's views; figpress-apps' tests check this in Node and in browsers.
- **Antipodes**: a view and its antipode give the same fraction (mirrored sky); the globe draws the
  camera-facing end and keeps a dragged view on its own end.
