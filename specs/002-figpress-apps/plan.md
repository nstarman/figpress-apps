# Implementation Plan: figkit becomes figpress-apps

**Branch**: `002-figpress-apps` | **Date**: 2026-10-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-figpress-apps/spec.md`

## Summary

A mechanical rename driven by one table, applied by a throwaway script to the live files only, then
read over by hand; the data loader gains compatibility with figkit's keys; a `release.yml` publishes
to PyPI with trusted publishing; the changelog gets one migration note per renamed name; the
constitution is amended (name, PyPI).

## Technical Context

**Language/Version**: Python ≥ 3.11; plain ES modules (browser), Node ≥ 20 for tests

**Primary Dependencies**: numpy; anywidget (optional). Build: hatchling. Release: `uv build`,
`pypa/gh-action-pypi-publish`

**Testing**: pytest, `node --test js-tests/*.test.js`, smoke tests (Playwright) in CI

**Target Platform**: PyPI; static sites; Jupyter/marimo

**Project Type**: library + CLI

**Constraints**: no behaviour change other than names and the old-key compatibility

**Scale/Scope**: ~60 live files

## Rename table

| Old | New |
|---|---|
| distribution `figkit` | `figpress-apps` |
| `import figkit`, `figkit.<attr>` | `import figpress_apps`, `figpress_apps.<attr>` |
| `src/figkit/` | `src/figpress_apps/` |
| command `figkit` | `figpress-apps` |
| module specifier `figkit/<m>.js` | `figpress-apps/<m>.js` |
| `figkit/figkit.js`, `figkit/figkit.css` | `figpress-apps/index.js`, `figpress-apps/index.css` |
| `<meta name="figkit-version">` | `<meta name="figpress-apps-version">` |
| `vendor/figkit-<v>/` | `vendor/figpress-apps-<v>/` |
| `globalThis.FIGKIT_DATA` | `globalThis.FIGPRESS_APPS_DATA` |
| `FIGKIT_ROOTS` (Node test hook) | `FIGPRESS_APPS_ROOTS` |
| manifest `figkit_data`, `figkit` | `figpress_apps_data`, `figpress_apps` (old keys still read) |
| JS `FigkitDataError` | `DataError` (as in Python) |
| `canvas.figkitModel`, `data-figkit-app` | `canvas.appModel`, `data-figpress-app` |
| skills `figkit`, `figkit-upgrade` | `figpress-apps`, `figpress-apps-upgrade` |
| repository `nstarman/figkit` | `nstarman/figpress-apps` (GitHub redirects) |
| gallery `nstarkman.space/figkit/`, Cloudflare `figkit` | `nstarkman.space/figpress-apps/`, `figpress-apps` |
| `.fk-*`, `--fk-*` | unchanged |

## Constitution Check

| Principle | How this plan meets it |
|---|---|
| I. Web-native, no build step | Unchanged; files are only renamed. |
| II. Vendored and pinned | Vendor folder and meta renamed; still vendored at the exact version. Not published to npm. |
| III. One source, two outputs | Bare specifiers keep the rule; the build's checks apply to `figpress-apps/…`. |
| IV. Open data contract | Format stays 1; keys renamed, old keys still read, so published data stays loadable. |
| V. Notebook parity | Widget renamed only. |
| VI. Small, generic, earned | No new code beyond the key compatibility and the release workflow. |
| VII. Verified against Python | All tests, the acceptance numbers and the smoke tests rerun. |
| Technology Constraints | Amended: installed from PyPI (and still from tags). Constitution 2.0.0 → 2.1.0. |
| Releases and Upgrades | `v2026.10.28`, migration notes per renamed name, both skills updated, old tags kept. |

## Project Structure

```text
src/figpress_apps/            (was src/figkit/)  js/index.js, js/index.css (were figkit.js/.css)
skills/figpress-apps/, skills/figpress-apps-upgrade/
.github/workflows/release.yml   new: tag → PyPI (trusted publishing, environment pypi)
CHANGELOG.md                    ## 2026.10.28 with migration notes
```

Historical records left as they are: past changelog sections, `specs/001-figkit-v0-1/`,
`examples/globe/prototype/`.

## Complexity Tracking

None.
