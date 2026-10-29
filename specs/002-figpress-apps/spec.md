# Feature Specification: figkit becomes figpress-apps

**Feature Branch**: `002-figpress-apps`

**Created**: 2026-10-28

**Status**: Draft

**Input**: User description: "Rename figkit to figpress-apps, a member of the figpress family
(figpress, figpress-plotly, figpress-apps): repository, package, imports, command, skills,
migration note; publish it on PyPI like the rest of the family."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install and use figpress-apps (Priority: P1)

A paper's author installs `figpress-apps` from PyPI and builds, serves, tests and embeds webapps
exactly as with figkit, under the new name: the Python package, the command, the browser modules
and the notebook widget are all called figpress-apps.

**Why this priority**: it is the rename itself; everything else follows from it.

**Independent Test**: in a clean environment, `pip install figpress-apps`, then export the globe
example's data, build it (served site and single file), run its tests and open both outputs; the
acceptance numbers (48.0 / 16.2 / 87.6 / 87.2 %) are reproduced.

**Acceptance Scenarios**:

1. **Given** a clean environment, **When** the author installs `figpress-apps` from PyPI, **Then**
   `import figpress_apps`, the `figpress-apps` command (`build`, `serve`, `test`) and
   `figpress_apps.anywidget.Widget` work.
2. **Given** a webapp whose modules import `figpress-apps/<module>.js`, **When** it is built,
   **Then** the served site and the single file work, vendor `vendor/figpress-apps-<version>/` and
   carry `<meta name="figpress-apps-version">`.
3. **Given** an app that still imports `figkit/<module>.js`, **When** it is built, **Then** the build
   fails with a message naming the new specifier, as it does for any unresolvable import.

---

### User Story 2 - Move an existing figkit webapp (Priority: P1)

The maintainer of a webapp built with figkit (CP1's two apps, syw-site) moves it to figpress-apps by
following the changelog's migration note, or the upgrade skill, which applies it.

**Why this priority**: figkit has real users; a rename without a migration path breaks them.

**Independent Test**: apply the migration note to the globe example as it was at figkit 0.2.0;
it builds and passes its tests.

**Acceptance Scenarios**:

1. **Given** the changelog, **When** the maintainer reads the release's section, **Then** every
   renamed thing has a migration note with **What changed**, **Find** (a grep pattern) and **Edit**.
2. **Given** a dataset written by figkit (`figkit_data` manifest), **When** figpress-apps loads it in
   Python or in the browser, **Then** it loads unchanged; nothing has to be re-exported.
3. **Given** an app's own CSS using figkit's `.fk-*` classes and `--fk-*` variables, **When** it moves
   to figpress-apps, **Then** that CSS keeps working unchanged.

---

### User Story 3 - Find it under its new name (Priority: P2)

Someone who follows an old link to figkit's repository, gallery or skill lands on figpress-apps.

**Why this priority**: links in papers, notes and pins should keep working.

**Independent Test**: open `github.com/nstarman/figkit` and a pip pin to
`git+https://github.com/nstarman/figkit@v0.2.0`; both resolve.

**Acceptance Scenarios**:

1. **Given** the repository is renamed, **When** someone opens or clones the old address, **Then**
   GitHub redirects to `nstarman/figpress-apps`.
2. **Given** a paper pinned to figkit `v0.1.0` or `v0.2.0`, **When** it installs, **Then** it gets
   that figkit release unchanged (tags and `versions/*` branches are kept).

### Edge Cases

- A fix needed by figkit 0.1/0.2 is still backported on `versions/v0.1.x` / `versions/v0.2.x` and
  released as figkit `0.1.N` / `0.2.N` (git tags); figpress-apps releases are dated.
- Old and new data keys in one manifest: the new key wins; the loader does not fail.
- A notebook that imported `figkit.anywidget` must change its import (migration note); there is no
  `figkit` alias package.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The distribution MUST be `figpress-apps` (import `figpress_apps`), its command
  `figpress-apps`, and its notebook widget `figpress_apps.anywidget.Widget`.
- **FR-002**: Browser modules MUST be imported as `figpress-apps/<module>.js`; the entry module and
  stylesheet are `figpress-apps/index.js` and `figpress-apps/index.css` (formerly `figkit/figkit.js`
  and `figkit/figkit.css`).
- **FR-003**: Built sites MUST vendor `vendor/figpress-apps-<version>/` and carry
  `<meta name="figpress-apps-version">`; single-file builds register datasets on
  `globalThis.FIGPRESS_APPS_DATA`.
- **FR-004**: New datasets MUST be written with the manifest keys `figpress_apps_data` (format 1)
  and `figpress_apps` (the writer's version); loaders MUST also accept datasets written with
  figkit's `figkit_data` / `figkit` keys.
- **FR-005**: The `.fk-*` CSS classes and `--fk-*` custom properties MUST stay as they are.
- **FR-006**: The skills MUST be `figpress-apps` and `figpress-apps-upgrade`; the upgrade skill MUST
  apply this release's migration notes to a figkit webapp.
- **FR-007**: The release MUST be `v2026.10.28`, published to PyPI as `figpress-apps` from a tag
  with trusted publishing (environment `pypi`), and as a GitHub release with the changelog notes.
- **FR-008**: The changelog's section for the release MUST give a migration note for every renamed
  public name (FR-001–FR-003, FR-006).
- **FR-009**: Historical records MUST keep their wording: changelog sections of past releases,
  `specs/001-figkit-v0-1/`, and the globe example's `prototype/`.

### Key Entities

- **Rename table**: old name → new name for every public name (package, import, command, module
  specifiers, entry module, stylesheet, page meta, vendor folder, single-file registry, data keys,
  skills, repository, gallery URL).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `pip install figpress-apps` gives a working package from the first release on.
- **SC-002**: Every test passes after the rename: pytest, `node --test`, the globe acceptance numbers
  and the browser smoke tests.
- **SC-003**: No live file (outside the historical records of FR-009) still names figkit, except the
  migration notes and the data loader's compatibility with old keys.
- **SC-004**: CP1's two webapps move with the migration note alone.

## Assumptions

- PyPI's pending publisher for `figpress-apps` is registered (repository `nstarman/figpress-apps`,
  workflow `release.yml`, environment `pypi`); the GitHub repository is renamed before the tag.
- No npm package: the browser modules ship inside the Python package and are vendored into every
  build (Principle II); `@nstarkman` is the maintainer's own scope, so there is no name to claim.
- The Cloudflare preview project and the gallery's Pages URL follow the new name; the old
  Cloudflare project is left to the maintainer.
- Downstream moves (syw-site, CP1, the skills registry, the figpress family list) are done after the
  release, outside this repository.
