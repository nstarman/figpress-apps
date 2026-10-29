// Load a figpress-apps dataset (manifest.json + .npy files) into typed arrays — the same result from a
// served folder, from the data: URLs of a single-file build, or from a notebook model.

import { parseNpy } from "figpress-apps/npy.js";

export const FORMAT = 1; // figpress_apps_data major this library reads

export class DataError extends Error {
  constructor(message) { super(message); this.name = "DataError"; }
}

// Datasets written before the rename (figkit ≤ 0.2) carry these keys; they still load.
const OLD_KEYS = { figkit_data: "figpress_apps_data", figkit: "figpress_apps" };
function upgradeKeys(manifest) {
  const m = { ...manifest };
  for (const [old, now] of Object.entries(OLD_KEYS)) {
    if (old in m) { if (!(now in m)) m[now] = m[old]; delete m[old]; }
  }
  return m;
}

function check(manifest, where) {
  if (manifest.figpress_apps_data !== FORMAT) {
    throw new DataError(`${where}: dataset has figpress_apps_data ${manifest.figpress_apps_data}, `
      + `this figpress-apps reads figpress_apps_data ${FORMAT}; re-export it with the matching figpress-apps version`);
  }
}

const result = (m) => ({ name: m.name, meta: m.meta ?? {}, arrays: {}, json: {} });

/**
 * source: a dataset name (fetched from `${base}${name}/`), {name, urls: {file: url}} from a
 * single-file build, or a notebook model holding `manifest`, `arrays` (entry → .npy bytes) and `json`.
 */
export async function loadData(source, { fetch = globalThis.fetch, base = "data/" } = {}) {
  if (source && typeof source.get === "function") return fromModel(source);
  // a single-file build registers its datasets as data: URLs on globalThis.FIGPRESS_APPS_DATA
  if (typeof source === "string" && globalThis.FIGPRESS_APPS_DATA?.[source]) source = globalThis.FIGPRESS_APPS_DATA[source];
  const [name, urlOf] = typeof source === "string"
    ? [source, (f) => `${base}${source}/${f}`]
    : [source.name, (f) => source.urls[f]];
  const get = async (file, kind) => {
    const url = urlOf(file);
    let res;
    try { res = url && await fetch(url); } catch { res = null; }
    if (!res?.ok) throw new DataError(`could not load ${name}/${file}; run the export for dataset "${name}" and rebuild`);
    return kind === "json" ? res.json() : res.arrayBuffer();
  };
  const manifest = upgradeKeys(await get("manifest.json", "json"));
  check(manifest, `${name}/manifest.json`);
  const out = result(manifest);
  await Promise.all(Object.entries(manifest.entries).map(async ([key, e]) => {
    if (e.kind === "json") out.json[key] = await get(e.file, "json");
    else out.arrays[key] = parseNpy(await get(e.file, "binary"));
  }));
  return out;
}

function fromModel(model) {
  const raw = model.get("manifest");
  if (!raw) throw new DataError("the widget has no dataset (manifest is missing)");
  const manifest = upgradeKeys(raw);
  check(manifest, "widget manifest");
  const out = result(manifest), arrays = model.get("arrays") ?? {}, json = model.get("json") ?? {};
  for (const [key, e] of Object.entries(manifest.entries)) {
    if (e.kind === "json") { out.json[key] = json[key]; continue; }
    const raw = arrays[key];
    if (!raw) throw new DataError(`the widget is missing array ${key}`);
    // notebooks deliver DataViews, possibly unaligned: copy the bytes once, then view them
    const bytes = raw instanceof DataView ? new Uint8Array(raw.buffer, raw.byteOffset, raw.byteLength)
      : new Uint8Array(raw.buffer ?? raw);
    out.arrays[key] = parseNpy(bytes.slice().buffer);
  }
  return out;
}
