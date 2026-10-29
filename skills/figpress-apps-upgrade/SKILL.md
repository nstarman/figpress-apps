---
name: figpress-apps-upgrade
description: Upgrade a figpress-apps webapp (or a paper repository's webapps) to a newer figpress-apps version, or move a figkit webapp to figpress-apps, applying the changelog's migration notes in order, rebuilding and re-checking the app's numbers. Use when asked to upgrade, bump or update figpress-apps or figkit, when a webapp was built against an older version, or when a build or page fails after a version change.
---

# Upgrading a figpress-apps webapp

figpress-apps webapps are pinned to one figpress-apps version: a PyPI release (`figpress-apps==YYYY.MM.DD`)
or a git tag of `nstarman/figpress-apps`. Versions are dates, `vYYYY.MM.DD`, with bug-fix releases
`vYYYY.MM.DD.N`; a bug-fix release of the pinned version never needs migration notes. Before
2026.10.28 the package was **figkit** (tags `v0.1.0`, `v0.2.0`): see "Coming from figkit" below. Every built page
records it, and every breaking change in figpress-apps ships a **migration note** saying exactly how to
update an app. This skill applies those notes; it never guesses.

## 1. Find the current and target versions

- **Built against**: the page's `<meta name="figpress-apps-version" content="…">` (in a built
  `index.html` or single-file page), or `"figpress_apps"` in a dataset's `data/<name>/manifest.json`.
  A figkit build has `figkit-version` and `"figkit"` instead.
- **Pinned**: `figpress-apps==YYYY.MM.DD` or `figpress-apps @ git+https://github.com/nstarman/figpress-apps@vYYYY.MM.DD`
  in the repo's `pyproject.toml` (or `environment.yml` / requirements file); for a figkit app,
  `figkit @ git+https://github.com/nstarman/figkit@v0.X.Y`.
- **Target**: what the user asked for; otherwise the latest release
  (`gh release list -R nstarman/figpress-apps --limit 1`, or PyPI).

If the versions are equal, report that and stop. If the sources disagree (e.g. a stale build next
to a newer pin), the **pin** is what the code runs against: upgrade from the pinned version and
rebuild everything.

**Record a baseline before changing anything**: run the app's tests
(`uv run figpress-apps test webapps/<name>`, if it has `*.test.js`) and record what the built page shows
(the panel readouts — see [references/check-page.md](references/check-page.md) for a headless
recipe). These are the numbers that must be unchanged afterwards.

## 2. Read the migration notes

Change the pin to the target (keep its form: `==YYYY.MM.DD` from PyPI, or `git+https://…@vX`) and
install it; check that the resolver reports the intended version. Then read the installed
changelog, which includes every earlier release:

```bash
uv add "figpress-apps==TARGET"        # or edit the pin and `uv sync`
uv run python -c "import figpress_apps, pathlib; print((pathlib.Path(figpress_apps.__file__).parent / 'CHANGELOG.md').read_text())"
```

Take every section **after** the current version up to and including the target, oldest first.
List each breaking change and its migration note: **What changed**, **Find**, **Edit**.

**Stop** if a section describes a breaking change (under "Changed" or "Removed", or anything that
renames or removes an API, option, model key, file or command) without a migration note. Report
the gap to the user; do not improvise an edit.

## 3. Apply the notes, oldest first

For each note:

1. Run its **Find** as written (e.g. `grep -rn "compute:" webapps/`); the note's scope wins. Also
   search the obvious syntax variants the pattern may miss (shorthand `{ compute }`,
   `compute :`, `opts.compute =`).
2. Read each hit in context and make the **Edit** only where it matches what the note describes
   (e.g. a skypanel options object, not an unrelated `compute:` key). Change nothing else.
3. Re-run **Find** and confirm that no relevant hits remain.

## 4. Rebuild and check

For each webapp:

```bash
uv run python webapps/<name>/export.py --out build/data          # re-export: the manifest records the version
uv run figpress-apps build webapps/<name> --data build/data/<dataset> --out build/site/<name> --single-file build/<name>.html
uv run figpress-apps test webapps/<name>                                 # the app's science tests, if any
```

The build must succeed (it rejects relative imports, `import.meta.url` and datasets of another
data-format version). Then compare with the baseline: the tests pass and the page's readouts are
unchanged ([references/check-page.md](references/check-page.md)).

Build output normally lives in an ignored `build/`. If the repository tracks built output, the
rebuild replaces `vendor/figpress-apps-<old>/` with `vendor/figpress-apps-<new>/`: commit that together with the
source edits and say so in the report.

## Coming from figkit

figkit was renamed figpress-apps in 2026.10.28. To move a figkit app (pinned to `v0.1.0` or
`v0.2.0`): replace the pin `figkit @ git+…@v0.X.Y` with `figpress-apps==TARGET`, then apply every
migration note from the figkit version's section onward, **including 2026.10.28's renames** (the
command, the import, `figkit/…` module specifiers, `figkit/figkit.js` and `figkit/figkit.css`).
Datasets written by figkit load unchanged; re-exporting writes the new manifest keys. The app's
`.fk-*` classes and `--fk-*` variables stay as they are.

## 5. Report

Tell the user: old → new version, each migration note applied (with the files touched), the
build and test results, and anything that could not be done.
