# Tasks: figkit becomes figpress-apps

**Input**: [spec.md](spec.md), [plan.md](plan.md)

## Phase 1: Setup

- [x] T001 `git mv` the package to `src/figpress_apps/`, the entry module and stylesheet to
      `js/index.js` / `js/index.css`, and the skills to `skills/figpress-apps*`

## Phase 2: Foundational

- [x] T002 Apply the plan's rename table to the live files (script, then read every diff)
- [x] T003 pyproject (name, command, version path), package.json (test resolver), `uv lock`

## Phase 3: User Story 1 — install and use (P1)

- [x] T004 [US1] pytest, `node --test`, globe acceptance; fix what the rename broke
- [x] T005 [US1] Build the globe example (site + single file) and check vendor folder and meta
- [x] T006 [US1] `.github/workflows/release.yml` (tag → PyPI, environment `pypi`); tests.yml's
      tag check uses `figpress_apps.__version__`

## Phase 4: User Story 2 — move an existing webapp (P1)

- [x] T007 [US2] Loaders accept figkit's `figkit_data`/`figkit` keys (Python and JS), with tests
- [x] T008 [US2] CHANGELOG `## 2026.10.28` with a migration note per renamed name; both skills
      updated; the upgrade skill knows the figkit → figpress-apps move

## Phase 5: User Story 3 — find it under its new name (P2)

- [x] T009 [US3] README, AGENTS.md, gallery and preview URLs; constitution amended (2.1.0)

## Phase 6: Polish

- [x] T010 Grep: no live file names figkit except migration notes and the loader's old-key support
- [x] T011 Set `__version__ = "2026.10.28"`; show the maintainer before renaming the repository
