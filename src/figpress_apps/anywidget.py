"""Run a figpress-apps app in Jupyter or marimo (extra: ``figpress-apps[notebook]``).

The app module is the same file the web page runs; its imports are inlined into nested ``data:``
URLs (anywidget loads modules without an import map). The dataset travels as synced traits:
``manifest``, ``arrays`` (entry name → the ``.npy`` file's bytes) and ``json``.
"""

from __future__ import annotations

import json as _json
from pathlib import Path

import anywidget
import traitlets

from figpress_apps.build import JS_DIR, inline_modules
from figpress_apps.data import load


class Widget(anywidget.AnyWidget):
    """A figpress-apps app as a notebook widget; ``camera`` and ``views`` sync back to Python."""

    camera = traitlets.List(traitlets.Float()).tag(sync=True)
    views = traitlets.Dict().tag(sync=True)
    manifest = traitlets.Dict().tag(sync=True)
    arrays = traitlets.Dict().tag(sync=True)
    json = traitlets.Dict().tag(sync=True)

    def __init__(self, app: str | Path, data: str | Path, **kwargs):
        app, data = Path(app), Path(data)
        ds = load(data)  # verifies the dataset (format version, checksums)
        entries = ds.manifest["entries"]
        # anywidget turns these attributes into synced traits during __init__
        self._esm = inline_modules(f"app/{app.name}", roots={"figpress-apps/": JS_DIR, "app/": app.parent})
        self._css = (JS_DIR / "index.css").read_text(encoding="utf-8")
        super().__init__(
            manifest=ds.manifest,
            arrays={k: (data / e["file"]).read_bytes() for k, e in entries.items() if e["kind"] == "array"},
            json={k: _json.loads((data / e["file"]).read_text(encoding="utf-8")) for k, e in entries.items() if e["kind"] == "json"},
            **kwargs,
        )
