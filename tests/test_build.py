"""figpress_apps.build (served output) and the CLI (contracts/python-api.md, contracts/cli.md)."""

import json
import shutil
import subprocess
import sys

import numpy as np
import pytest

import figpress_apps
from figpress_apps import BuildError

JS = __import__("pathlib").Path(figpress_apps.__file__).parent / "js"
V = figpress_apps.__version__


def make_app(tmp_path, widget='import { createModel } from "figpress-apps/model.js";\nexport default { render() {} };\n'):
    app = tmp_path / "app"
    app.mkdir()
    (app / "index.html").write_text(
        '<!doctype html><html><head><title>t</title>'
        '<link rel="stylesheet" href="figpress-apps/index.css"></head><body><div id="el"></div>'
        '<script type="module">import { run } from "figpress-apps/index.js"; import app from "app/widget.js";'
        ' run(app, document.getElementById("el"));</script></body></html>', encoding="utf-8")
    (app / "widget.js").write_text(widget, encoding="utf-8")
    (app / "notes.md").write_text("not copied", encoding="utf-8")
    (app / "widget.test.js").write_text("not copied", encoding="utf-8")
    return app


def test_served_layout(tmp_path):
    data = figpress_apps.export(tmp_path / "d", "ds", {"a": np.zeros(2)})
    res = figpress_apps.build(make_app(tmp_path), data=[data], out=tmp_path / "site")
    site = res.out
    html = (site / "index.html").read_text(encoding="utf-8")
    assert f'<meta name="figpress-apps-version" content="{V}">' in html
    imap = json.loads(html.split('<script type="importmap">')[1].split("</script>")[0])
    assert imap == {"imports": {"figpress-apps/": f"./vendor/figpress-apps-{V}/", "app/": "./"}}
    assert html.index("importmap") < html.index('<script type="module">')
    assert f'href="./vendor/figpress-apps-{V}/index.css"' in html
    for f in JS.iterdir():
        assert (site / f"vendor/figpress-apps-{V}" / f.name).read_bytes() == f.read_bytes()
    assert (site / "data/ds/a.npy").exists() and (site / "widget.js").exists()
    assert not (site / "notes.md").exists() and not (site / "widget.test.js").exists()


@pytest.mark.parametrize(
    ("widget", "msg"),
    [('import { x } from "./science.js";\n', r"widget\.js:1: relative import"),
     ('\nconst u = new URL("a", import.meta.url);\n', r"widget\.js:2: import\.meta\.url"),
     ('const m = "figpress-apps/model.js";\nawait import(m);\n', r"widget\.js:2: non-literal"),
     ('import { x } from "figpress-apps/nope.js";\n', r"widget\.js:1: cannot resolve"),
     ('import x from "https://cdn.example.com/x.js";\n', r"widget\.js:1: .*third-party|relative"),
     ('import x from "lodash";\n', r"widget\.js:1: cannot resolve")],
)
def test_import_checks(tmp_path, widget, msg):
    with pytest.raises(BuildError, match=msg):
        figpress_apps.build(make_app(tmp_path, widget), out=tmp_path / "site")


def test_rejects_other_data_format(tmp_path):
    data = figpress_apps.export(tmp_path / "d", "ds", {"a": np.zeros(2)})
    m = json.loads((data / "manifest.json").read_text(encoding="utf-8"))
    (data / "manifest.json").write_text(json.dumps({**m, "figpress_apps_data": 2}), encoding="utf-8")
    with pytest.raises(BuildError, match="figpress_apps_data 2"):
        figpress_apps.build(make_app(tmp_path), data=[data], out=tmp_path / "site")


def test_js_passes_its_own_checks(tmp_path):
    figpress_apps.build(make_app(tmp_path), out=tmp_path / "site")  # vendored modules are checked too


def test_cli(tmp_path):
    app = make_app(tmp_path)
    run = lambda *a: subprocess.run([sys.executable, "-m", "figpress_apps.cli", *a], capture_output=True, text=True)  # noqa: E731
    assert run("build", str(app), "--out", str(tmp_path / "s")).returncode == 0
    assert run("build", str(app)).returncode == 2
    (app / "widget.js").write_text('import "./x.js";\n', encoding="utf-8")
    r = run("build", str(app), "--out", str(tmp_path / "s2"))
    assert r.returncode == 1 and "widget.js:1" in r.stderr
    assert run("--version").stdout.strip().endswith(V)


# ── single file and inline_modules (User Story 2) ────────────────────────────

def test_inline_modules(tmp_path):
    app = make_app(tmp_path, 'import { a } from "app/a.js";\nexport default { render() { return a; } };\n')
    (app / "a.js").write_text('import { createModel } from "figpress-apps/model.js";\nexport const a = createModel;\n', encoding="utf-8")
    src = figpress_apps.inline_modules("app/widget.js", roots={"figpress-apps/": JS, "app/": app})
    assert '"figpress-apps/' not in src and '"app/' not in src and "importmap" not in src
    assert src.count("data:text/javascript;base64,") == 1  # a.js, with model.js nested inside it


def test_inline_cycle(tmp_path):
    app = make_app(tmp_path, 'import "app/a.js";\nexport default {};\n')
    (app / "a.js").write_text('import "app/widget.js";\n', encoding="utf-8")
    with pytest.raises(BuildError, match="cycle"):
        figpress_apps.inline_modules("app/widget.js", roots={"figpress-apps/": JS, "app/": app})


def test_single_file(tmp_path):
    data = figpress_apps.export(tmp_path / "d", "ds", {"a": np.zeros(2)})
    res = figpress_apps.build(make_app(tmp_path), data=[data], single_file=tmp_path / "x.html",
                       size_warning_mb=1e-6)
    html = res.single_file.read_text(encoding="utf-8")
    assert f'<meta name="figpress-apps-version" content="{V}">' in html
    assert "importmap" not in html and '"figpress-apps/' not in html and '"app/' not in html
    assert "globalThis.FIGPRESS_APPS_DATA" in html and "--fk-bg" in html  # data and index.css inlined
    assert res.warnings and "MB" in res.warnings[0]


def test_test_command(tmp_path):
    app = make_app(tmp_path)
    (app / "widget.test.js").unlink()  # placeholder text, not a test
    (app / "science.js").write_text('import { dot } from "figpress-apps/geom.js";\nexport const f = () => dot([1, 2, 3], [1, 1, 1]);\n', encoding="utf-8")
    (app / "science.test.js").write_text(
        'import { test } from "node:test";\nimport assert from "node:assert/strict";\n'
        'import { f } from "app/science.js";\ntest("f", () => assert.equal(f(), 6));\n', encoding="utf-8")
    run = lambda: subprocess.run([sys.executable, "-m", "figpress_apps.cli", "test", str(app)], capture_output=True, text=True)  # noqa: E731
    assert run().returncode == 0
    (app / "science.test.js").write_text((app / "science.test.js").read_text(encoding="utf-8").replace("6)", "7)"))
    assert run().returncode != 0


def test_text_io_is_utf8():
    """Every text read/write in the package names UTF-8: the shipped JS, CSS and generated READMEs
    contain non-ASCII characters, which a platform default (e.g. cp1252 on Windows) would break.
    Checked on the syntax tree, so a call split over several lines is judged correctly."""
    import ast

    bad = []
    for p in JS.parent.rglob("*.py"):
        for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr in ("read_text", "write_text")):
                enc = next((k.value for k in node.keywords if k.arg == "encoding"), None)
                if not (isinstance(enc, ast.Constant) and str(enc.value).lower().replace("_", "-") == "utf-8"):
                    bad.append(f"{p.name}:{node.lineno}")
    assert not bad, bad
