import { test } from "node:test";
import assert from "node:assert/strict";
import { autoscale } from "figpress-apps/skypanel.js";

test("equal aspect, contains the track, centred on its mid-range", () => {
  const xy = new Float32Array([0, 0, 10, 2, 4, -6]);
  const { cx, cy, half } = autoscale(xy);
  assert.equal(cx, 5); assert.equal(cy, -2);
  for (let k = 0; k < xy.length; k += 2) {
    assert.ok(Math.abs(xy[k] - cx) <= half && Math.abs(xy[k + 1] - cy) <= half);
  }
  assert.equal(half, 0.55 * 10);
});

test("a single point gets a unit-size view", () => {
  assert.deepEqual(autoscale(new Float32Array([3, 4])), { cx: 3, cy: 4, half: 0.55 });
});
