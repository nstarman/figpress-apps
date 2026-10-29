// The globe example reproduces the paper's non-concave fractions at the paper's views.
import { test } from "node:test";
import assert from "node:assert/strict";
import { loadData } from "figpress-apps/data.js";
import { streamFromData, classify } from "../examples/globe/science.js";
import { fixtureFetch } from "./helpers.js";

const PAPER = { orbit1: 48.0, orbit2: 16.2, spray: 87.6, nbody: 87.2 };

test("non-concave fractions match the paper", async () => {
  const data = await loadData("globe", { fetch: fixtureFetch, base: "fixtures/" });
  const got = {};
  for (const s of data.meta.streams) {
    const r = classify(streamFromData(data, s.id), s.view);
    got[s.id] = Math.round(1000 * r.fraction) / 10;
    assert.equal(r.xy.length, 2 * data.arrays[`${s.id}_pos`].shape[0]);
    assert.ok(r.readout.includes(got[s.id].toFixed(1)));
  }
  console.log(Object.entries(got).map(([k, v]) => `${k} ${v.toFixed(1)}`).join(" "));
  for (const [id, want] of Object.entries(PAPER)) assert.ok(Math.abs(got[id] - want) < 0.1 + 1e-9, `${id}: ${got[id]} vs ${want}`);
});

test("the antipodal view gives the same fraction (mirrored sky)", async () => {
  const data = await loadData("globe", { fetch: fixtureFetch, base: "fixtures/" });
  for (const s of data.meta.streams) {
    const st = streamFromData(data, s.id);
    const a = classify(st, s.view).fraction, b = classify(st, s.view.map((c) => -c)).fraction;
    assert.ok(Math.abs(a - b) < 1e-12, s.id);
  }
});
