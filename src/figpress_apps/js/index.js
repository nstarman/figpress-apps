// figpress-apps' public browser API, and `run`, the standalone host for an app module.

export { createModel } from "figpress-apps/model.js";
export { parseNpy, asTyped } from "figpress-apps/npy.js";
export { loadData, DataError } from "figpress-apps/data.js";
export * as geom from "figpress-apps/geom.js";
export { createStage, dragHelper, cssVar, rgb, context2d } from "figpress-apps/stage.js";
export { mount as mountGlobe, shade } from "figpress-apps/globe.js";
export { mount as mountSkyPanel, autoscale } from "figpress-apps/skypanel.js";

import { createModel } from "figpress-apps/model.js";

/** Show a plain error box in `el` (text only) and log details to the console. */
export function showError(el, message, error) {
  if (error) console.error(error);
  const box = document.createElement("div");
  box.className = "fk-error";
  box.textContent = message;
  el.replaceChildren(box);
}

/**
 * Run an app module (an anywidget module: `{initialize?, render}` or a factory returning it) on a
 * web page. `data` is passed to the app through the model as `data_source` (a dataset name or a
 * single-file URL map). Returns a dispose function that aborts the app's signal.
 */
export async function run(app, el, { data, base = "data/", model = createModel() } = {}) {
  const controller = new AbortController();
  model.set("data_source", data ?? null);
  model.set("data_base", base);
  try {
    const def = typeof app === "function" ? await app() : app;
    await def.initialize?.({ model, signal: controller.signal });
    await def.render?.({ model, el, signal: controller.signal });
  } catch (error) {
    showError(el, error?.name === "DataError" ? error.message : `This figure failed to load: ${error?.message ?? error}`, error);
  }
  return () => controller.abort();
}
