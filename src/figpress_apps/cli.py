"""The `figpress-apps` command: build and serve webapps (contracts/cli.md)."""

from __future__ import annotations

import argparse
import sys

from figpress_apps.build import BuildError
from figpress_apps.data import DataError


def run_tests(app_dir: str) -> int:
    """Run ``app_dir/*.test.js`` with ``node --test``; imports resolve as in a built page."""
    import json
    import os
    import shutil
    import subprocess
    from pathlib import Path

    from figpress_apps.build import JS_DIR

    app = Path(app_dir).resolve()
    tests = sorted(str(p) for p in app.glob("*.test.js"))
    if not tests:
        print(f"figpress-apps: no *.test.js files in {app}", file=sys.stderr)
        return 1
    node = shutil.which("node")
    if node is None:
        print("figpress-apps: node (≥ 20.6) is needed to run JS tests", file=sys.stderr)
        return 1
    env = {**os.environ, "FIGPRESS_APPS_ROOTS": json.dumps({"figpress-apps/": str(JS_DIR), "app/": str(app)})}
    register = Path(__file__).parent / "node" / "register.mjs"
    return subprocess.run([node, "--import", register.as_uri(), "--test", *tests], env=env).returncode


def main(argv: list[str] | None = None) -> int:
    from figpress_apps import __version__, build
    from figpress_apps.serve import serve

    p = argparse.ArgumentParser(prog="figpress-apps", description="Build and serve figpress-apps webapps.")
    p.add_argument("--version", action="version", version=f"figpress-apps {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="build a webapp into a site and/or a single HTML file")
    b.add_argument("app_dir")
    b.add_argument("--data", action="append", default=[], metavar="DATASET_DIR")
    b.add_argument("--out", metavar="DIR")
    b.add_argument("--single-file", metavar="FILE")
    b.add_argument("--size-warning-mb", type=float, default=50.0)
    t = sub.add_parser("test", help="run an app's *.test.js files with node, resolving figpress-apps/ and app/")
    t.add_argument("app_dir")
    s = sub.add_parser("serve", help="preview a built site locally")
    s.add_argument("dir")
    s.add_argument("--port", type=int, default=8000)
    s.add_argument("--no-open", action="store_true")
    args = p.parse_args(argv)

    if args.cmd == "test":
        return run_tests(args.app_dir)
    if args.cmd == "serve":
        serve(args.dir, port=args.port, open_browser=not args.no_open)
        return 0
    if not args.out and not args.single_file:
        b.error("give --out and/or --single-file")
    try:
        res = build(args.app_dir, data=args.data, out=args.out, single_file=args.single_file, size_warning_mb=args.size_warning_mb)
    except (BuildError, DataError) as e:
        print(f"figpress-apps: {e}", file=sys.stderr)
        return 1
    for w in res.warnings:
        print(f"figpress-apps: warning: {w}", file=sys.stderr)
    for path in (res.out, res.single_file):
        if path:
            print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
