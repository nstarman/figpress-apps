# Reading a built page's numbers headlessly

Save as `check_page.py` in the paper repository and run with
`uv run --with playwright python check_page.py build/site globe` (once:
`uv run --with playwright playwright install chromium`). It prints the text of every panel readout
(`.fk-readout`, keyed by the panel's `data-panel` id).

```python
import sys, threading
from playwright.sync_api import sync_playwright
from figpress_apps.serve import make_server

site, app = sys.argv[1], sys.argv[2]
server = make_server(site, port=0)
threading.Thread(target=server.serve_forever, daemon=True).start()
with sync_playwright() as p:
    page = p.chromium.launch().new_page(viewport={"width": 1280, "height": 1000})
    page.goto(f"http://127.0.0.1:{server.server_address[1]}/{app}/")
    page.wait_for_selector(".fk-readout:has-text('%'), .fk-readout:not(:empty)")
    for el in page.locator("[data-panel]").all():
        print(el.get_attribute("data-panel"), "|", el.locator(".fk-readout").inner_text())
server.shutdown()
```
