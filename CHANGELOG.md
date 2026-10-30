# Changelog

Releases are dated: `YYYY.MM.DD`, and `YYYY.MM.DD.N` for a bug-fix release of it (0.1.0 and 0.2.0
predate this). The version does not say whether a release breaks things; the migration notes do.

Every release has a section. Every breaking change has a migration note with three parts, so the
`figpress-apps-upgrade` skill can apply it:

- **What changed**: one sentence.
- **Find**: how to locate affected code, e.g. `grep -rn "compute:" webapps/`.
- **Edit**: the exact change to make.

A release with a breaking change that has no migration note is not tagged.

## 2026.10.29 — 2026-10-29

- Apps follow a theme the page pins with `<html data-theme="light|dark">` (a site's toggle), not only
  the system's: the colours (`index.css`) and the canvases' redraw. With no `data-theme`, as before.

## 2026.10.28 — 2026-10-28

figkit is now **figpress-apps**, a member of the [figpress](https://nstarkman.space/figpress/) family,
published on PyPI. Nothing else changes: same modules, same behaviour, same data format. Each rename
below has its migration note; the `figpress-apps-upgrade` skill applies them in order.

### Changed — migration

- **What changed**: the Python distribution, its import and its command: `figkit` →
  `figpress-apps` (PyPI), `import figkit` → `import figpress_apps`, the command `figkit` →
  `figpress-apps`, the widget `figkit.anywidget.Widget` → `figpress_apps.anywidget.Widget`.
  **Find**: `grep -rnE "figkit( @|\\.|$| build| serve| test)|import figkit|from figkit" .`
  **Edit**: pin `figpress-apps==2026.10.28` instead of `figkit @ git+…`; replace `import figkit` with
  `import figpress_apps` and `figkit.` with `figpress_apps.`; run `figpress-apps build|serve|test`.
- **What changed**: browser module specifiers: `figkit/<module>.js` → `figpress-apps/<module>.js`,
  and the entry module and stylesheet `figkit/figkit.js` → `figpress-apps/index.js`,
  `figkit/figkit.css` → `figpress-apps/index.css`.
  **Find**: `grep -rn "figkit/" webapps/`
  **Edit**: replace `figkit/figkit.js` with `figpress-apps/index.js`, `figkit/figkit.css` with
  `figpress-apps/index.css`, then every remaining `figkit/` with `figpress-apps/`.
- **What changed**: built pages: `<meta name="figkit-version">` → `<meta name="figpress-apps-version">`,
  `vendor/figkit-<v>/` → `vendor/figpress-apps-<v>/`, `globalThis.FIGKIT_DATA` →
  `globalThis.FIGPRESS_APPS_DATA`, the app element's `data-figkit-app` → `data-figpress-app`.
  **Find**: `grep -rnE "figkit-version|vendor/figkit-|FIGKIT_DATA|figkitApp|data-figkit-app" .`
  **Edit**: rebuild (`figpress-apps build`); in app code, replace `dataset.figkitApp` with
  `dataset.figpressApp`. Commit the new `vendor/` folder if built output is tracked.
- **What changed**: datasets are written with `figpress_apps_data` / `figpress_apps` instead of
  `figkit_data` / `figkit`. Datasets written by figkit still load.
  **Find**: `grep -rn "figkit_data" .` (code that reads manifests itself)
  **Edit**: none for datasets; in code that reads a manifest directly, read `figpress_apps_data`
  (falling back to `figkit_data` for old data). JS `FigkitDataError` is now `DataError`.
- **What changed**: the skills `figkit` and `figkit-upgrade` are `figpress-apps` and
  `figpress-apps-upgrade`; the repository is `nstarman/figpress-apps` (GitHub redirects the old
  address) and the gallery `https://nstarkman.space/figpress-apps/`.
  **Find**: `grep -rn "nstarman/figkit\|skills/figkit\|nstarkman.space/figkit" .`
  **Edit**: use the new names and addresses.

Unchanged: the `.fk-*` CSS classes and `--fk-*` custom properties, the data format (1), and the
figkit releases `v0.1.0` / `v0.2.0` (still installable from their tags; fixes for them stay
`0.1.N` / `0.2.N`).

### Added

- Releases are published to PyPI from their tag (`release.yml`, trusted publishing).

### Changed

- Versioning: releases are dated (`vYYYY.MM.DD`, bug fixes `vYYYY.MM.DD.N`), and every bug fix is
  backported to every released version that has it (constitution 2.0.0, AGENTS.md "Releasing").
  No code changes; pins to `v0.1.0`/`v0.2.0` keep working, and the next release sorts after them.

## 0.2.0 — 2026-10-21

No breaking changes: no migration needed from 0.1.

### Added

- Responsive layout classes in `figkit.css`, driven by container queries (the app's own width,
  so they also adapt in narrow notebook cells): `.fk-split` (two columns, stacked below 760 px)
  and `.fk-grid-2` (a 2 × 2-style grid, one column below 320 px).
- `cssVar(el, name, fallback)`, `rgb(color)` (a frozen `[r, g, b]`) and `context2d(canvas)` (a clear error
  instead of a null context) in `figkit/stage.js`, re-exported by `figkit.js`.
- `shade(camera, texture, size, out, base)`: optional background `[r, g, b]` (0–255) to composite over.

### Fixed

- Dark mode: the globe's disc, axes and labels and the panels' origin mark follow the theme
  instead of staying white or near-black; canvases redraw when the system theme changes.
- Panel headers wrap on narrow screens: titles may wrap, readouts stay on one line.
- The globe example stacks the globe above its panels on phones.
- Gallery: each example page links back to the gallery (served and single file).
- All text files are read and written as UTF-8 (`figkit build`, `export`, the notebook widget):
  non-ASCII characters in figkit's JS, CSS and generated READMEs broke on non-UTF-8 locales
  (e.g. Windows cp1252). A test guards it.

### Development

- Pull requests get a live gallery preview on Cloudflare Pages and a single **CI Pass** gate.
- The `versions/vX.Y.x` release process (AGENTS.md).

## 0.1.0 — 2026-10-21

First release. Specified in `specs/001-figkit-v0-1/`.

### Added

- Data contract: `figkit.export` / `figkit.load` — a manifest plus plain `.npy` files, dtype rules,
  checked opt-in float64 → float32 narrowing (data format 1).
- Browser library: `model`, `npy`, `data`, `geom`, `stage`, `globe`, `skypanel` and `figkit.css`.
- `figkit build` (served site with vendored library and import map; single self-contained HTML that
  opens from `file://`), `figkit serve`, `figkit test`.
- `figkit.anywidget.Widget` (extra `notebook`): the same app in JupyterLab and marimo.
- The globe example (`examples/globe/`) and its gallery page.
- Skills: `figkit` (building a webapp) and `figkit-upgrade` (moving one to a newer tag).
