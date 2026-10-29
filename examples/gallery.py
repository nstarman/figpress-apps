"""Build the gallery: every example (served + single file) and an index page.

    uv run python examples/gallery.py site

Used by gallery.yml (GitHub Pages, on release) and by the pull-request previews in tests.yml.
"""

import importlib.util
import shutil
import sys
from pathlib import Path

import figpress_apps

HERE = Path(__file__).parent

EXAMPLES = [
    ("globe", "Stream convexities in a common principal-axis frame",
     "A rotatable globe of viewing directions with four linked sky panels that re-project stellar "
     "streams and recompute the paper's non-concavity criterion live.",
     "Starkman et al. (2026)", "https://ui.adsabs.harvard.edu/abs/2026arXiv260940057S/abstract"),
]

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>figpress-apps gallery</title>
<style>
  body {{ margin: 0; font: 15px/1.5 system-ui, sans-serif; color: #222; background: #fff; }}
  main {{ max-width: 760px; margin: 0 auto; padding: 24px 16px; }}
  a {{ color: #3b6ea8; }}
  @media (prefers-color-scheme: dark) {{ body {{ color: #e3e6ea; background: #15181d; }} a {{ color: #8ab4e8; }} }}
  .ex {{ border-top: 1px solid #8884; padding: 12px 0; }} .meta {{ color: #888; font-size: 13px; }}
</style></head>
<body><main>
<h1>figpress-apps gallery</h1>
<p>Interactive counterparts of paper figures, built with
<a href="https://github.com/nstarman/figpress-apps">figpress-apps</a> {version}.</p>
{items}
</main></body></html>
"""
ITEM = """<div class="ex"><h2><a href="{slug}/">{title}</a></h2><p>{text}</p>
<p class="meta">Data: <a href="{url}">{cite}</a> · <a href="{slug}.html">single file</a> (opens offline)</p></div>"""


# Added to each example page by the gallery only: the examples stay standalone pages that papers reuse.
BACK = ('<nav style="max-width:1200px;margin:0 auto;padding:12px 16px 0;font:14px/1.4 system-ui,sans-serif">'
        '<a href="{href}" style="color:var(--fk-accent,#3b6ea8);text-decoration:none">← figpress-apps gallery</a></nav>')


def add_back_link(page: Path, href: str) -> None:
    html = page.read_text(encoding="utf-8")
    i = html.index(">", html.index("<body")) + 1
    page.write_text(html[:i] + "\n" + BACK.format(href=href) + html[i:], encoding="utf-8")


def build_example(slug: str, site: Path, data_dir: Path) -> None:
    spec = importlib.util.spec_from_file_location(f"{slug}_export", HERE / slug / "export.py")
    export = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(export)
    dataset = export.main(data_dir)
    res = figpress_apps.build(HERE / slug, data=[dataset], out=site / slug, single_file=site / f"{slug}.html")
    add_back_link(res.out / "index.html", "../")
    add_back_link(res.single_file, "index.html")  # explicit: file:// does not open a folder's index


def main(site: Path) -> None:
    shutil.rmtree(site, ignore_errors=True)
    site.mkdir(parents=True)
    for slug, *_ in EXAMPLES:
        build_example(slug, site, site.parent / f"{site.name}-data")
    items = "\n".join(ITEM.format(slug=s, title=t, text=x, cite=c, url=u) for s, t, x, c, u in EXAMPLES)
    (site / "index.html").write_text(PAGE.format(version=figpress_apps.__version__, items=items), encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
