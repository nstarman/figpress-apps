import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GLOBE = ROOT / "examples" / "globe"


@pytest.fixture(scope="session")
def globe_data(tmp_path_factory):
    sys.path.insert(0, str(GLOBE))
    import export

    return export.main(tmp_path_factory.mktemp("data"))


@pytest.fixture(scope="session")
def globe_site(tmp_path_factory, globe_data):
    import figpress_apps

    out = tmp_path_factory.mktemp("site")
    return figpress_apps.build(GLOBE, data=[globe_data], out=out / "globe", single_file=out / "globe.html")


@pytest.fixture(scope="session")
def served(globe_site):
    from figpress_apps.serve import make_server

    server = make_server(globe_site.out.parent, port=0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}/globe/"
    server.shutdown()


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "viewport": {"width": 1280, "height": 1000}}
