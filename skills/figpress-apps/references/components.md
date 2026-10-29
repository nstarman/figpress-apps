# Components and the model

Every component: `mount(el, model, opts) → dispose`. It renders into `el`, listens to model keys
and removes its listeners on dispose. Mount several components on one model to link them.

## figpress-apps/globe.js — `mount(el, model, opts)`

| Option | Meaning |
|---|---|
| `texture` | `{data: Uint8Array, shape: [H, W, 4]}` RGBA, rows colatitude 0..π, columns azimuth 0..2π (inclusive) |
| `lines` | `{id: {data, shape: [n, 3]}}` in globe units (radius 1); back half drawn faint |
| `points` | `{id: {data, shape: [m, 3]}}`, optional |
| `colors` | `{id: css colour}` |
| `markerAxes` | `(id, view) → [ex, ey]` tangent axes of id's square (globe frame); default: screen axes |
| `markerSizeDeg` | half-width of a square in degrees (default 5.5) |

Model: reads/writes `camera` (rotate by dragging the background) and `views`
(`{id: [x, y, z]}`, drag a square). Calls `save_changes()` on pointer-up.
Pure kernel: `shade(camera, texture, size, out, base = [255, 255, 255])` — `base` is an `[r, g, b]` array (0–255), e.g. `rgb(cssVar(el, "--fk-bg", "#fff"))`.

## figpress-apps/skypanel.js — `mount(el, model, opts)` (the general 2-D panel)

Named for sky projections, but use it for any 2-D plot driven by model state.

| Option | Meaning |
|---|---|
| `id` | key into `views`; `views[id]` may be any value (a unit vector, an angle, `[θ, φ]`, …). The panel recomputes only when that entry changes (by identity) |
| `title`, `color` | header text and colour |
| `compute` | `(view) → {xy, points?, mask?, readout?}`: `xy` flat n×2 line; `points` flat m×2, drawn as faint 1-px dots in `color`; `mask` Uint8Array n, segments where two neighbours are set are drawn thick in `highlight`; `readout` text in the header |
| `highlight` | colour of masked segments (default `#FF7F7F`) |
| `limits` | fixed frame `{cx, cy, half}` (data units); default: re-frame to the line on every update — fix it when the motion itself is the point (e.g. a rotation) |

The black × marks the origin (0, 0) of the data coordinates (in sky panels, the projected centre).
Pure helper: `autoscale(xy, pad = 0.55) → {cx, cy, half}` (equal aspect, frames the line).

## figpress-apps/model.js — `createModel(initial)`

`get(key)`, `set(key, value)` (fires `change:key` when the value is a different object),
`on("change:key", fn)`, `off(event?, fn?)`, `save_changes()`. Same API as anywidget's model.

## figpress-apps/geom.js (pure)

`dot cross norm unit scale add`; `mat3.{identity,row,mul,apply,applyT,transpose,orthonormalize}`;
`rotationToZ(v)`; `trackball(camera, dx, dy, r)`; `project(camera, p, {cx, cy, r})` →
`[x, y, depth]`; `unproject(camera, x, y, geo)`; `facing(camera, v)`.

## figpress-apps/stage.js

`createStage(el, {draw, onResize})` → `{canvas, ctx, width, height, dpr, requestDraw, dispose}`
(drawing in CSS pixels; one redraw per frame). `dragHelper(el, {hitTest, onStart, onMove, onEnd})`.

## figpress-apps/index.js

Re-exports the above; `run(app, el, {data, base})` hosts an app on a web page; `showError(el, msg)`.
Styles: `figpress-apps/index.css` — `.fk-app`, `.fk-toolbar`, `.fk-panel`, `.fk-plot`, `.fk-grid`, and
the responsive `.fk-split` (side by side, stacked below 760 px) and `.fk-grid-2` (two columns, one
below 320 px). Their breakpoints are container queries on `.fk-app`, so they follow the app's width
(a notebook cell, a phone). Light/dark variables (`--fk-bg`, `--fk-fg`, `--fk-muted`, …) follow the
system theme; canvas code reads them with `cssVar(el, "--fk-fg", fallback)` at draw time, and
`createStage` redraws when the theme changes. Use layout classes, not inline grid styles, so apps
work on phones.

## Adding a component

Only when a real app needs it, inside figpress-apps (a pull request with tests), never by editing a vendored copy.
