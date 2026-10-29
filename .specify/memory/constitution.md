# figpress-apps Constitution

figpress-apps (formerly figkit; a member of the figpress family) is a toolbox for building webapps
that are the interactive counterparts of scientific papers: data, plots and movies that readers can
explore, published next to the static PDF and expected to keep working for a decade or more.

## Core Principles

### I. Web-native, no build step

- The browser library MUST be plain ES modules and CSS that run as written in current evergreen
  browsers. No bundler, transpiler, framework or package manager is required to use, build or
  view a figpress-apps webapp.
- Node.js MAY be used only to run tests (`node --test`), never to produce shipped files.
- Rationale: build toolchains are the most common way interactive pages stop being rebuildable;
  the web platform itself is backward compatible.

### II. Vendored and pinned

- A built webapp MUST NOT load anything from a CDN or other third-party host at runtime.
- figpress-apps' JS ships inside the Python package as package data. Each built site vendors it into
  `vendor/figpress-apps-X.Y.Z/` at the exact installed version, and stamps that version in
  `<meta name="figpress-apps-version">` and in every data manifest.
- A third-party JS library MAY be vendored only if it is plain ESM (or vendored once as a pinned
  ESM file), has an OSI licence kept next to it, and is loaded only by pages that use it.
- Rationale: pages must survive CDN outages, deleted versions and dead projects; journals (AAS)
  require locally included JS.

### III. One source, two outputs

- Every webapp MUST build both as a served site (GitHub Pages, local server) and as a single
  self-contained HTML file that opens from `file://`.
- To make this possible, figpress-apps modules and app modules MUST import other modules only
  through bare `figpress-apps/…` (or app-prefixed) specifiers resolved by an import map. Relative
  imports (`./`, `../`) between modules and `import.meta.url` are forbidden; `figpress-apps build`
  MUST reject them.
- Modules MUST NOT touch the DOM at top level; work happens inside functions.
- Rationale: inlined modules have no base URL, and the same inlining feeds the notebook wrapper.

### IV. Open data contract

- Data passes from Python to the browser as `data/<dataset>/manifest.json` plus one `.npy` file per
  array (and JSON for metadata). Later kinds (Parquet via hyparquet, Zarr via zarrita, media) MAY
  be added to the manifest without changing existing kinds.
- Arrays MUST be little-endian, C-order, of dtype float32/64, int8–32, uint8–32 or bool. int64,
  object and string arrays MUST be rejected with a clear error.
- figpress-apps MUST NOT narrow dtypes silently (e.g. float64 → float32); narrowing happens only on
  explicit request, after a precision check.
- Published data MUST be loadable by readers with `numpy.load` and no figpress-apps installed.
- Rationale: the data behind a figure is part of the scholarly record, and `.npy` is a stable,
  self-describing format.

### V. Notebook parity

- Components MUST talk only through a model with the anywidget API (`get`, `set`,
  `on("change:key")`, `off`, `save_changes`). figpress-apps' standalone model and anywidget's
  model are interchangeable.
- A component exports `mount(el, model, opts) → dispose`. A webapp's app module is itself an
  anywidget module (`render({ model, el, signal })`) that composes components, so the same app
  runs on the web and in Jupyter/marimo.
- Model values are replaced, never mutated in place. Per-interaction derived data stays in app
  callbacks, not in synced model state. Notebooks call `save_changes` at the end of an
  interaction, not per pointer move.
- Rationale: the same code serves exploration during research and publication.

### VI. Small, generic, earned

- figpress-apps contains only generic pieces. Science-specific logic (a paper's classification,
  frames, physics) lives in that paper's app, in a DOM-free `science.js`.
- Code enters figpress-apps only when a real webapp needs it (YAGNI). A helper becomes a component
  only once it is used by an app; speculative options, kinds and abstractions are not added.
- Rationale: a small library stays understandable to a scientist and to the agents extending it.

### VII. Verified against Python

- Every pure module (model, npy, data, geometry, numerical kernels) MUST have `node --test` tests;
  the Python package MUST have pytest tests, including an export → load round trip.
- Every example webapp MUST include an acceptance test that its JS reproduces numbers computed by
  the paper's Python (for the globe example: 48.0 / 16.2 / 87.6 / 87.2 % non-concave).
- Each example MUST have one browser smoke test of both built outputs.
- Rationale: an interactive figure that disagrees with the paper is worse than none.

## Technology Constraints

- Python package `figpress-apps` (import `figpress_apps`), published to PyPI from release tags of
  `nstarman/figpress-apps` with trusted publishing; Python ≥ 3.11;
  runtime dependency on numpy only, plus anywidget as an optional extra.
- Browser targets: the last two major versions of Chrome, Firefox and Safari.
- Licence: MIT. Vendored third-party code keeps its own licence file.
- Agent guidance lives in `AGENTS.md` (with `CLAUDE.md` pointing to it); the skills that teach
  agents to use and upgrade figpress-apps live in `skills/` and are versioned with the code.

## Releases and Upgrades

- Versions are dates: a release is tagged `vYYYY.MM.DD` (Python version `YYYY.MM.DD`); a bug-fix
  release of it is `vYYYY.MM.DD.N` (N = 1, 2, …). The version number does not signal breaking
  changes; migration notes do. Tags `v0.1.0` and `v0.2.0` predate this and stay as they are.
- Every bug fix MUST be backported as far as it applies: to every released version that has the
  bug, each on its `versions/<tag>.x` branch (created from the release tag when first needed) and
  released as that version's next `.N`. Bug-fix releases MUST NOT contain breaking changes or new
  features.
- Every release MUST have a `CHANGELOG.md` section. Every breaking change MUST have a migration
  note giving what changed, how to find affected code (e.g. a grep pattern) and the exact edit.
  A release with an undocumented break MUST NOT be tagged.
- A change to the public API MUST update the `figpress-apps` and `figpress-apps-upgrade` skills in
  the same pull request.
- The example gallery is deployed to figpress-apps' GitHub Pages from each release; a broken example
  blocks the release.

## Governance

- This constitution overrides other practices in this repository. Specs and plans MUST include a
  constitution check; any deviation MUST be justified in the plan's complexity tracking.
- Amendments are made by pull request that states the change and its reason, with a version bump:
  MAJOR for removing or redefining a principle, MINOR for adding or materially expanding one,
  PATCH for wording.
- Reviews MUST check new code against Principles I–VII, especially the import and data rules,
  which `figpress-apps build` and CI enforce mechanically where possible.

**Version**: 2.1.0 | **Ratified**: 2026-10-21 | **Last Amended**: 2026-10-28
