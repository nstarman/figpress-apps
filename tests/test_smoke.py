"""Browser smoke tests of the globe example (marker `smoke`; needs Playwright browsers)."""

import pytest

pytestmark = pytest.mark.smoke
PAPER = {"orbit1": "48.0", "orbit2": "16.2", "spray": "87.6", "nbody": "87.2"}
ALLOWED = ("http://127.0.0.1", "file:", "data:", "blob:")


def readouts(page):
    return {i: page.locator(f'[data-panel="{i}"] .fk-readout').inner_text() for i in PAPER}


def marker_xy(page, sid):
    # orthographic projection of the marker's camera-facing end (as figpress-apps/geom.js project/facing)
    return page.evaluate("""(sid) => {
      const cv = document.querySelector("canvas[data-r]"), m = cv.appModel, box = cv.getBoundingClientRect();
      const C = m.get("camera"), w = m.get("views")[sid];
      const d = (i) => C[3 * i] * w[0] + C[3 * i + 1] * w[1] + C[3 * i + 2] * w[2];
      const s = d(2) >= 0 ? 1 : -1;
      return [box.left + +cv.dataset.cx + +cv.dataset.r * s * d(0), box.top + +cv.dataset.cy - +cv.dataset.r * s * d(1)];
    }""", sid)


def check_page(page, url):
    foreign = []
    page.on("request", lambda r: None if r.url.startswith(ALLOWED) else foreign.append(r.url))
    page.goto(url)
    page.wait_for_selector('[data-panel="nbody"] .fk-readout:has-text("%")')
    got = readouts(page)
    for i, want in PAPER.items():
        assert want in got[i], (i, got[i])

    # rotate: drag the globe background near its rim
    cv = page.locator("canvas[data-r]")
    box = cv.bounding_box()
    x0, y0 = box["x"] + box["width"] * 0.8, box["y"] + box["height"] * 0.25
    cam0 = page.evaluate("document.querySelector('canvas[data-r]').appModel.get('camera')")
    page.mouse.move(x0, y0); page.mouse.down(); page.mouse.move(x0 + 60, y0 - 5, steps=6); page.mouse.up()
    cam1 = page.evaluate("document.querySelector('canvas[data-r]').appModel.get('camera')")
    assert cam1 != cam0
    rows = [cam1[0:3], cam1[3:6], cam1[6:9]]
    for a in range(3):
        for b in range(3):
            assert abs(sum(x * y for x, y in zip(rows[a], rows[b])) - (a == b)) < 1e-9

    # drag the Orbit 1 marker: only its panel changes
    before = readouts(page)
    x, y = marker_xy(page, "orbit1")
    page.mouse.move(x, y); page.mouse.down(); page.mouse.move(x + 40, y + 30, steps=8); page.mouse.up()
    after = readouts(page)
    assert after["orbit1"] != before["orbit1"]
    assert all(after[i] == before[i] for i in PAPER if i != "orbit1")
    assert not foreign, foreign


def test_served(page, served):
    check_page(page, served)


def test_single_file(page, globe_site):
    # Block every request except file:, data: and blob: (Playwright's offline mode breaks file:// in WebKit).
    page.route("**/*", lambda route: route.continue_() if route.request.url.startswith(("file:", "data:", "blob:"))
               else route.abort())
    check_page(page, globe_site.single_file.as_uri())


# ── performance (SC-002, SC-003) ─────────────────────────────────────────────

def _time_to_readouts(page, url):
    import time

    t0 = time.perf_counter()
    page.goto(url)
    page.wait_for_selector('[data-panel="nbody"] .fk-readout:has-text("%")')
    return time.perf_counter() - t0


def test_load_time(page, served, globe_site):
    served_s = _time_to_readouts(page, served)
    single_s = _time_to_readouts(page, globe_site.single_file.as_uri())
    print(f"time to readouts: served {served_s:.2f} s, single file {single_s:.2f} s")
    assert served_s < 2 and single_s < 2


def test_drag_frame_rate(browser, served, browser_name):
    if browser_name != "chromium":
        pytest.skip("frame rate is measured on Chromium")
    ctx = browser.new_context(viewport={"width": 1280, "height": 1000}, device_scale_factor=2)
    try:
        page = ctx.new_page()
        page.goto(served)
        page.wait_for_selector('[data-panel="nbody"] .fk-readout:has-text("%")')
        # rotate for 2 s, one pointer move per animation frame, driven inside the page (scripted mouse
        # moves are round trips that would cap the rate); frames achieved = the page's frame rate
        fps = page.evaluate("""() => new Promise((done) => {
          const cv = document.querySelector("canvas[data-r]"), b = cv.getBoundingClientRect();
          const x = b.left + 0.8 * b.width, y = b.top + 0.25 * b.height;
          const ev = (type, dx) => cv.dispatchEvent(new PointerEvent(type, { pointerId: 7, clientX: x - dx, clientY: y + dx / 2, bubbles: true }));
          ev("pointerdown", 0);
          let n = 0; const t0 = performance.now();
          const step = () => {
            const t = performance.now() - t0;
            if (t > 2000) { ev("pointerup", n % 60); done(1000 * n / t); return; }
            ev("pointermove", 2 * (n++ % 60)); requestAnimationFrame(step);
          };
          requestAnimationFrame(step);
        })""")
        print(f"rotating at 2x DPR: {fps:.0f} frames/s")
        assert fps >= 30
    finally:
        ctx.close()


# ── layout (narrow screens, dark mode) and the gallery's back link ───────────

def test_phone_layout(browser, served):
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    try:
        page = ctx.new_page()
        page.goto(served)
        page.wait_for_selector('[data-panel="nbody"] .fk-readout:has-text("%")')
        # no sideways scrolling
        assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1")
        globe = page.locator("canvas[data-r]").bounding_box()
        panels = [page.locator(f'[data-panel="{i}"]').bounding_box() for i in PAPER]
        assert globe is not None and all(panels), "globe and panels must be rendered and visible"
        assert globe["width"] > 300  # the globe uses the full width, not a sliver of it
        assert all(p["y"] >= globe["y"] + globe["height"] - 1 for p in panels)  # panels stacked below it
        assert abs(panels[0]["y"] - panels[1]["y"]) < 1  # still 2 x 2 at phone width, not one tall column
        for i in PAPER:  # a readout stays on one line
            box = page.locator(f'[data-panel="{i}"] .fk-readout').bounding_box()
            assert box is not None, i
            assert box["height"] < 24, (i, box["height"])
    finally:
        ctx.close()


def test_gallery_back_link(page, tmp_path_factory):
    import subprocess
    import sys

    from conftest import ROOT

    site = tmp_path_factory.mktemp("gallery") / "site"
    subprocess.run([sys.executable, str(ROOT / "examples" / "gallery.py"), str(site)], check=True)
    page.goto((site / "globe.html").as_uri())
    page.wait_for_selector('[data-panel="nbody"] .fk-readout:has-text("%")')
    page.get_by_role("link", name="← figpress-apps gallery").click()
    page.wait_for_url("**/index.html")
    assert page.locator("h1").inner_text() == "figpress-apps gallery"


def test_pinned_theme(browser, served):
    """A theme the page pins (<html data-theme>, a site's toggle) wins over the system's, both ways,
    and the app's colours change as it is set."""
    for system, pinned, want in (("dark", "light", "#ffffff"), ("light", "dark", "#15181d")):
        page = browser.new_page(color_scheme=system)
        try:
            page.goto(served)
            page.wait_for_selector('[data-panel="nbody"] .fk-readout:has-text("%")')
            bg = lambda: page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--fk-bg').trim()")
            assert bg() == ("#15181d" if system == "dark" else "#ffffff")
            page.evaluate(f"document.documentElement.dataset.theme = '{pinned}'")
            assert bg() == want
        finally:
            page.close()
