"""A local static server for previewing built sites (127.0.0.1 only, no caching)."""

from __future__ import annotations

import functools
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class _Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map,
                      ".js": "text/javascript", ".mjs": "text/javascript",
                      ".npy": "application/octet-stream", ".json": "application/json"}

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):  # quiet
        pass


def make_server(directory: str | Path, *, port: int = 8000) -> ThreadingHTTPServer:
    """A server for ``directory`` on 127.0.0.1 (port 0 picks a free port); call serve_forever()."""
    handler = functools.partial(_Handler, directory=str(Path(directory).resolve()))
    return ThreadingHTTPServer(("127.0.0.1", port), handler)


def serve(directory: str | Path, *, port: int = 8000, open_browser: bool = True) -> None:
    """Serve ``directory`` until interrupted."""
    server = make_server(directory, port=port)
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"Serving {directory} at {url} (Ctrl-C to stop)")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
