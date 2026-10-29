"""figpress_apps.anywidget.Widget (User Story 3)."""

import re

import numpy as np
import pytest

pytest.importorskip("anywidget")

import figpress_apps  # noqa: E402
from figpress_apps.anywidget import Widget  # noqa: E402

from conftest import GLOBE  # noqa: E402


def test_widget_traits(globe_data):
    w = Widget(app=GLOBE / "widget.js", data=globe_data)
    assert not re.search(r"""from\s*["'](figpress-apps|app)/""", w._esm)  # all imports inlined
    assert w.manifest["name"] == "globe" and w.manifest["figpress_apps_data"] == 1
    files = {k: (globe_data / e["file"]).read_bytes()
             for k, e in w.manifest["entries"].items() if e["kind"] == "array"}
    assert set(w.arrays) == set(files) and all(w.arrays[k] == files[k] for k in files)
    assert w.camera == [] and w.views == {}  # the app fills them from the dataset on first render
    assert "--fk-bg" in w._css
    for name in ("camera", "views", "manifest", "arrays", "json"):
        assert w.trait_metadata(name, "sync")


def test_widget_rejects_bad_data(tmp_path):
    with pytest.raises(figpress_apps.DataError):
        Widget(app=GLOBE / "widget.js", data=tmp_path)
    figpress_apps.export(tmp_path, "ok", {"a": np.zeros(2)})
    Widget(app=GLOBE / "widget.js", data=tmp_path / "ok")
