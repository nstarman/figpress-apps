"""Build a webapp into a served site and/or a single self-contained HTML file.

Modules import each other only by bare specifiers: ``figpress-apps/…`` (the vendored library) and
``app/…`` (the app's own files). The served site resolves them with an import map; the single
file and the notebook wrapper rewrite them into nested ``data:`` URLs (research R1).
"""

from __future__ import annotations

import base64
import json
import re
import shutil
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from figpress_apps.data import FORMAT, DataError, read_manifest

JS_DIR = Path(__file__).parent / "js"
WEB_SUFFIXES = {".html", ".js", ".css", ".json", ".png", ".jpg", ".jpeg", ".svg", ".webp", ".mp4", ".webm"}

_STATIC = re.compile(r"""\bimport\s*(?:[\w*{}\s,$]+?\s*from\s*)?(['"])([^'"\n]+)\1""")
_EXPORT_FROM = re.compile(r"""\bexport\s*(?:\*\s*(?:as\s+[\w$]+\s*)?|\{[^}]*\})\s*from\s*(['"])([^'"\n]+)\1""")
_DYNAMIC = re.compile(r"""\bimport\s*\(\s*([^)]*?)\s*\)""")
_META_URL = re.compile(r"\bimport\.meta\.url\b")
_MODULE_SCRIPT = re.compile(r"""(<script\b[^>]*\btype=["']module["'][^>]*>)(.*?)(</script>)""", re.S | re.I)
_ASSET_ATTR = re.compile(r"""\b(href|src)=(["'])figpress-apps/""")
_STYLESHEET = re.compile(r"""<link\b[^>]*\brel=["']stylesheet["'][^>]*>""", re.I)


class BuildError(ValueError):
    """The app or its data cannot be built; the message names the file and line."""


@dataclass
class BuildResult:
    out: Path | None = None
    single_file: Path | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class _Import:
    start: int  # offset of the specifier's text (inside the quotes)
    end: int
    spec: str
    line: int


def _imports(source: str, file: str, offset_line: int = 0) -> list[_Import]:
    """Find every module specifier; reject what the single file and notebooks cannot resolve."""
    line = lambda pos: offset_line + source.count("\n", 0, pos) + 1  # noqa: E731
    if m := _META_URL.search(source):
        raise BuildError(f"{file}:{line(m.start())}: import.meta.url is not allowed (modules may be inlined)")
    found: list[_Import] = []
    for rx in (_STATIC, _EXPORT_FROM):
        found += [_Import(m.start(2), m.end(2), m.group(2), line(m.start())) for m in rx.finditer(source)]
    for m in _DYNAMIC.finditer(source):
        arg = m.group(1)
        lit = re.fullmatch(r"""(['"])([^'"\n]+)\1""", arg)
        if not lit:
            raise BuildError(f"{file}:{line(m.start())}: non-literal dynamic import({arg}); use a string literal")
        found.append(_Import(m.start(1) + 1, m.end(1) - 1, lit.group(2), line(m.start())))
    for imp in found:
        if imp.spec.startswith(("./", "../", "/")):
            raise BuildError(f"{file}:{imp.line}: relative import {imp.spec!r}; use a bare specifier "
                             f"(figpress-apps/… or app/…)")
        if re.match(r"^[a-z][a-z0-9+.-]*:|^//", imp.spec):
            raise BuildError(f"{file}:{imp.line}: third-party URL {imp.spec!r}; vendor it instead "
                             f"(no relative or remote imports)")
    return sorted(found, key=lambda i: i.start)


def _resolve(spec: str, roots: Mapping[str, Path], file: str, line: int) -> Path:
    for prefix, root in roots.items():
        if spec.startswith(prefix):
            path = Path(root) / spec[len(prefix):]
            if path.is_file():
                return path
    raise BuildError(f"{file}:{line}: cannot resolve {spec!r} (known prefixes: {', '.join(roots)})")


def _check_tree(sources: Iterable[tuple[str, str, int]], roots: Mapping[str, Path]) -> None:
    """Check every module reachable from the given (source, file, line offset) entries."""
    seen: set[Path] = set()
    stack = list(sources)
    while stack:
        source, file, off = stack.pop()
        for imp in _imports(source, file, off):
            path = _resolve(imp.spec, roots, file, imp.line)
            if path not in seen:
                seen.add(path)
                stack.append((path.read_text(encoding="utf-8"), path.name, 0))


def _data_url(text: str | bytes, mime: str) -> str:
    raw = text.encode() if isinstance(text, str) else text
    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"


def _rewrite(source: str, file: str, roots: Mapping[str, Path], memo: dict, stack: tuple, off: int = 0) -> str:
    out, last = [], 0
    for imp in _imports(source, file, off):
        path = _resolve(imp.spec, roots, file, imp.line)
        out += [source[last:imp.start], _inline_path(path, roots, memo, stack)]
        last = imp.end
    return "".join(out) + source[last:]


def _inline_path(path: Path, roots: Mapping[str, Path], memo: dict, stack: tuple) -> str:
    if path in stack:
        chain = " → ".join(p.name for p in (*stack, path))
        raise BuildError(f"{path.name}: import cycle {chain}")
    if path not in memo:
        memo[path] = _data_url(_rewrite(path.read_text(encoding="utf-8"), path.name, roots, memo, (*stack, path)),
                               "text/javascript")
    return memo[path]


def inline_modules(entry: str, *, roots: Mapping[str, Path]) -> str:
    """Return the entry module's source with every import rewritten to nested ``data:`` URLs.

    ``entry`` is a bare specifier (e.g. ``"app/widget.js"``); ``roots`` maps prefixes to folders,
    e.g. ``{"figpress-apps/": apps_js_dir, "app/": app_dir}``. Identical modules become identical URLs,
    so each module is instantiated once.
    """
    path = _resolve(entry, roots, entry, 0)
    return _rewrite(path.read_text(encoding="utf-8"), path.name, roots, {}, (path,))


def _insert_head(html: str, snippet: str) -> str:
    m = re.search(r"<head\b[^>]*>", html, re.I)
    if m:
        return html[:m.end()] + "\n" + snippet + html[m.end():]
    return snippet + "\n" + html


def _version_meta() -> str:
    from figpress_apps import __version__

    return f'<meta name="figpress-apps-version" content="{__version__}">'


def _check_data(data: Iterable[str | Path]) -> list[Path]:
    paths = [Path(d) for d in data]
    for d in paths:
        try:
            read_manifest(d)
        except DataError as e:
            raise BuildError(f"{e} (this figpress-apps reads figpress_apps_data {FORMAT})") from None
    return paths


def build(
    app_dir: str | Path,
    *,
    data: Iterable[str | Path] = (),
    out: str | Path | None = None,
    single_file: str | Path | None = None,
    size_warning_mb: float = 50.0,
) -> BuildResult:
    """Build ``app_dir`` (an ``index.html`` plus app modules) into a served site and/or one file."""
    from figpress_apps import __version__

    if out is None and single_file is None:
        raise BuildError("nothing to build: give out and/or single_file")
    app = Path(app_dir)
    index = app / "index.html"
    if not index.is_file():
        raise BuildError(f"{index} not found")
    roots = {"figpress-apps/": JS_DIR, "app/": app}
    html = index.read_text(encoding="utf-8")
    scripts = [(m.group(2), "index.html", html.count("\n", 0, m.start(2))) for m in _MODULE_SCRIPT.finditer(html)]
    app_js = [(p.read_text(encoding="utf-8"), p.name, 0) for p in sorted(app.glob("*.js")) if not p.name.endswith(".test.js")]
    lib_js = [(p.read_text(encoding="utf-8"), f"figpress-apps/{p.name}", 0) for p in sorted(JS_DIR.glob("*.js"))]
    _check_tree([*scripts, *app_js, *lib_js], roots)
    datasets = _check_data(data)
    result = BuildResult()

    if out is not None:
        site = Path(out)
        if site.exists():
            shutil.rmtree(site)
        site.mkdir(parents=True)
        for f in app.iterdir():
            if f.is_file() and f.suffix in WEB_SUFFIXES and not f.name.endswith(".test.js"):
                shutil.copy2(f, site / f.name)
        vendor = f"vendor/figpress-apps-{__version__}"
        shutil.copytree(JS_DIR, site / vendor)
        imap = json.dumps({"imports": {"figpress-apps/": f"./{vendor}/", "app/": "./"}})
        page = _ASSET_ATTR.sub(lambda m: f"{m.group(1)}={m.group(2)}./{vendor}/", html)
        page = _insert_head(page, f'{_version_meta()}\n<script type="importmap">{imap}</script>')
        (site / "index.html").write_text(page, encoding="utf-8")
        for d in datasets:
            shutil.copytree(d, site / "data" / d.name)
        result.out = site

    if single_file is not None:
        memo: dict = {}
        page = _MODULE_SCRIPT.sub(
            lambda m: m.group(1) + _rewrite(m.group(2), "index.html", roots, memo, (),
                                            html.count("\n", 0, m.start(2))) + m.group(3),
            html,
        )

        def inline_css(m: re.Match) -> str:
            href = re.search(r"""\bhref=["']([^"']+)["']""", m.group(0)).group(1)
            path = JS_DIR / href[len("figpress-apps/"):] if href.startswith("figpress-apps/") else app / href
            if not path.is_file():
                raise BuildError(f"index.html: stylesheet {href!r} not found")
            css = path.read_text(encoding="utf-8")
            return f"<style>\n{css}</style>"

        page = _STYLESHEET.sub(inline_css, page)
        registry = {
            d.name: {"name": d.name, "urls": {f.name: _data_url(f.read_bytes(), "application/octet-stream")
                                               for f in sorted(d.iterdir()) if f.is_file()}}
            for d in datasets
        }
        page = _insert_head(page, f"{_version_meta()}\n<script>globalThis.FIGPRESS_APPS_DATA = {json.dumps(registry)};</script>")
        target = Path(single_file)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page, encoding="utf-8")
        size_mb = target.stat().st_size / 1e6
        if size_mb > size_warning_mb:
            result.warnings.append(f"{target} is {size_mb:.1f} MB (above {size_warning_mb:g} MB); "
                                   f"consider the served build or smaller data")
        result.single_file = target
    return result
