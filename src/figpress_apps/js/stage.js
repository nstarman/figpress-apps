// A canvas that fills its element, is sharp on high-DPI screens and is drawn in CSS pixels;
// redraws are coalesced to one per animation frame. Plus a pointer-drag helper.

/** A canvas's 2-D context, or a clear error if the browser cannot provide one. */
export function context2d(canvas, options) {
  const ctx = canvas.getContext("2d", options);
  if (!ctx) throw new Error("figpress-apps: this browser could not provide a 2-D canvas context");
  return ctx;
}

export function createStage(el, { draw, onResize } = {}) {
  const canvas = document.createElement("canvas");
  canvas.style.cssText = "display:block;width:100%;height:100%;touch-action:none";
  el.appendChild(canvas);
  const stage = { canvas, ctx: context2d(canvas), width: 0, height: 0, dpr: 1, requestDraw, dispose };
  let pending = false, disposed = false, mq = null;

  function requestDraw() {
    if (pending || disposed) return;
    pending = true;
    requestAnimationFrame(() => { pending = false; if (!disposed) draw?.(stage); });
  }
  function resize() {
    const box = el.getBoundingClientRect();
    stage.width = box.width; stage.height = box.height; stage.dpr = globalThis.devicePixelRatio || 1;
    canvas.width = Math.max(1, Math.round(box.width * stage.dpr));
    canvas.height = Math.max(1, Math.round(box.height * stage.dpr));
    stage.ctx.setTransform(stage.dpr, 0, 0, stage.dpr, 0, 0);
    onResize?.(stage);
    requestDraw();
  }
  function watchDpr() { // moving to a screen with another pixel density
    mq?.removeEventListener("change", onDpr);
    mq = matchMedia(`(resolution: ${globalThis.devicePixelRatio || 1}dppx)`);
    mq.addEventListener("change", onDpr);
  }
  function onDpr() { resize(); watchDpr(); }
  const ro = new ResizeObserver(resize);
  ro.observe(el);
  watchDpr();
  const scheme = matchMedia("(prefers-color-scheme: dark)"); // theme colours change with it,
  scheme.addEventListener("change", requestDraw);
  const pinned = new MutationObserver(requestDraw); // and with a theme the page pins (data-theme)
  pinned.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  resize();

  function dispose() {
    disposed = true;
    ro.disconnect();
    mq?.removeEventListener("change", onDpr);
    scheme.removeEventListener("change", requestDraw);
    pinned.disconnect();
    canvas.remove();
  }
  return stage;
}

/** A CSS custom property's value on `el` (e.g. a theme colour from index.css), or `fallback`. */
export const cssVar = (el, name, fallback) => getComputedStyle(el).getPropertyValue(name).trim() || fallback;

let probe = null; // one 1×1 context, reused: rgb() runs on every globe redraw
const rgbCache = new Map();

/** Any CSS colour as a frozen [r, g, b] (0–255), resolved by the browser; cached per colour string. */
export function rgb(color) {
  let out = rgbCache.get(color);
  if (out) return out;
  if (!probe) {
    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = 1;
    probe = context2d(canvas, { willReadFrequently: true });
  }
  probe.clearRect(0, 0, 1, 1);
  probe.fillStyle = "#000"; probe.fillStyle = color; probe.fillRect(0, 0, 1, 1);
  out = Object.freeze(Array.from(probe.getImageData(0, 0, 1, 1).data.subarray(0, 3))); // shared: read-only
  if (rgbCache.size > 64) rgbCache.clear();
  rgbCache.set(color, out);
  return out;
}

/**
 * Pointer dragging on `el`, in CSS pixels relative to it. hitTest(x, y) picks what is dragged
 * (null = the background). Returns a dispose function.
 */
export function dragHelper(el, { hitTest, onStart, onMove, onEnd }) {
  let drag = null;
  const at = (e) => { const b = el.getBoundingClientRect(); return [e.clientX - b.left, e.clientY - b.top]; };
  const down = (e) => {
    const [x, y] = at(e);
    drag = { target: hitTest?.(x, y) ?? null, x, y, id: e.pointerId };
    try { el.setPointerCapture?.(e.pointerId); } catch { /* synthetic or already-released pointer */ }
    onStart?.(drag.target, x, y);
  };
  const move = (e) => {
    if (!drag || e.pointerId !== drag.id) return;
    const [x, y] = at(e);
    onMove?.(drag.target, x - drag.x, y - drag.y, x, y);
    drag.x = x; drag.y = y;
  };
  const up = (e) => {
    if (!drag || e.pointerId !== drag.id) return;
    const { target } = drag;
    drag = null;
    onEnd?.(target);
  };
  el.addEventListener("pointerdown", down);
  el.addEventListener("pointermove", move);
  el.addEventListener("pointerup", up);
  el.addEventListener("pointercancel", up);
  return () => {
    el.removeEventListener("pointerdown", down);
    el.removeEventListener("pointermove", move);
    el.removeEventListener("pointerup", up);
    el.removeEventListener("pointercancel", up);
  };
}
