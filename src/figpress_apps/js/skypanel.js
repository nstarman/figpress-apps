// A 2-D panel: points (faint dots), a line, highlighted segments, an origin cross and a readout.
// Built for sky projections but general: `views[id]` may be any value (a direction, an angle, …);
// the app's `compute(view)` turns it into what to draw. Recomputes only when that entry changes.

import { createStage, cssVar } from "figpress-apps/stage.js";

/** Equal-aspect view of an n×2 array of points: centre and half-width, at least `pad` wide. */
export function autoscale(xy, pad = 0.55) {
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  for (let k = 0; k < xy.length; k += 2) {
    x0 = Math.min(x0, xy[k]); x1 = Math.max(x1, xy[k]);
    y0 = Math.min(y0, xy[k + 1]); y1 = Math.max(y1, xy[k + 1]);
  }
  return { cx: (x0 + x1) / 2, cy: (y0 + y1) / 2, half: pad * Math.max(x1 - x0, y1 - y0, 1) };
}

/**
 * opts: id (key into views), title, color, highlight (colour of masked segments),
 * compute(view) → {xy, points?, mask?, readout?} with xy/points flat n×2 arrays,
 * limits: fixed {cx, cy, half} frame (default: autoscale to the line on every update).
 */
export function mount(el, model, { id, title, color = "#555", highlight = "#FF7F7F", compute, limits }) {
  el.classList.add("fk-panel");
  el.dataset.panel = id;
  el.style.borderColor = color;
  const head = document.createElement("div");
  head.className = "fk-panel-head";
  const name = document.createElement("span");
  name.textContent = title ?? id;
  const readout = document.createElement("span");
  readout.className = "fk-readout";
  head.append(name, readout);
  const plot = document.createElement("div");
  plot.className = "fk-plot";
  el.append(head, plot);

  let view = null, result = null;
  const stage = createStage(plot, { draw });

  function draw({ ctx, width, height }) {
    ctx.clearRect(0, 0, width, height);
    if (!result) return;
    const { cx, cy, half } = limits ?? autoscale(result.xy);
    const s = Math.min(width, height) / 2 / half;
    const X = (x) => width / 2 + (x - cx) * s, Y = (y) => height / 2 - (y - cy) * s;
    const { xy, points, mask } = result;
    if (points) {
      ctx.fillStyle = color; ctx.globalAlpha = 0.18;
      for (let k = 0; k < points.length; k += 2) ctx.fillRect(X(points[k]), Y(points[k + 1]), 1, 1);
      ctx.globalAlpha = 1;
    }
    ctx.lineCap = "round";
    if (mask) {
      ctx.strokeStyle = highlight; ctx.lineWidth = 5; ctx.beginPath();
      for (let i = 1; i < mask.length; i++) {
        if (mask[i] && mask[i - 1]) {
          ctx.moveTo(X(xy[2 * i - 2]), Y(xy[2 * i - 1])); ctx.lineTo(X(xy[2 * i]), Y(xy[2 * i + 1]));
        }
      }
      ctx.stroke();
    }
    ctx.strokeStyle = color; ctx.lineWidth = 1.6; ctx.beginPath();
    for (let k = 0; k < xy.length; k += 2) (k ? ctx.lineTo(X(xy[k]), Y(xy[k + 1])) : ctx.moveTo(X(xy[k]), Y(xy[k + 1])));
    ctx.stroke();
    const ox = X(0), oy = Y(0), r = 5;
    ctx.strokeStyle = cssVar(el, "--fk-fg", "#000"); ctx.lineWidth = 2; ctx.beginPath();
    ctx.moveTo(ox - r, oy - r); ctx.lineTo(ox + r, oy + r); ctx.moveTo(ox - r, oy + r); ctx.lineTo(ox + r, oy - r);
    ctx.stroke();
  }

  function update() {
    const v = model.get("views")?.[id];
    if (v === undefined || v === view) return; // a view of 0 is a view
    view = v;
    result = compute(v);
    readout.textContent = result.readout ?? "";
    stage.requestDraw();
  }
  model.on("change:views", update);
  update();
  return () => {
    model.off("change:views", update);
    stage.dispose();
    el.replaceChildren();
  };
}
