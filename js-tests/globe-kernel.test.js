import { test } from "node:test";
import assert from "node:assert/strict";
import { shade } from "figpress-apps/globe.js";
import { trackball, mat3 } from "figpress-apps/geom.js";

const H = 19, W = 37;
const tex = { shape: [H, W, 4], data: new Uint8Array(H * W * 4).map((_, i) => (i * 37) % 251) };
const camera = trackball(mat3.identity(), 40, -25, 100);

test("outside the disc is untouched; the centre samples the toward direction", () => {
  const size = 41, out = new Uint8ClampedArray(size * size * 4).fill(7);
  shade(camera, tex, size, out);
  assert.deepEqual(Array.from(out.subarray(0, 4)), [7, 7, 7, 7]); // corner
  const c = (Math.floor(size / 2) * size + Math.floor(size / 2)) * 4;
  const d = mat3.row(camera, 2);
  const i = Math.round(Math.acos(d[2]) / Math.PI * (H - 1));
  const j = Math.round(((Math.atan2(d[1], d[0]) + 2 * Math.PI) % (2 * Math.PI)) / (2 * Math.PI) * (W - 1));
  const t = 4 * (i * W + j), a = tex.data[t + 3] / 255;
  for (let k = 0; k < 3; k++) assert.ok(Math.abs(out[c + k] - ((1 - a) * 255 + a * tex.data[t + k])) <= 2, `channel ${k}`);
  assert.equal(out[c + 3], 255);
});

test("every pixel inside the disc is shaded, none outside", () => {
  const size = 40, out = new Uint8ClampedArray(size * size * 4);
  shade(camera, tex, size, out);
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const u = (x + 0.5 - 20) / 20, v = (y + 0.5 - 20) / 20;
    assert.equal(out[4 * (y * size + x) + 3], u * u + v * v <= 1 ? 255 : 0, `${x},${y}`);
  }
});
