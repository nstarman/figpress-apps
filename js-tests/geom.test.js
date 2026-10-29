import { test } from "node:test";
import assert from "node:assert/strict";
import { dot, norm, unit, mat3, rotationToZ, trackball, project, unproject, facing } from "figpress-apps/geom.js";
import { expected } from "./helpers.js";

const close = (a, b, tol = 1e-9) => a.forEach((x, i) => assert.ok(Math.abs(x - b[i]) < tol, `${i}: ${x} vs ${b[i]}`));
const orthonormal = (A, tol) => close(mat3.mul(A, mat3.transpose(A)), [1, 0, 0, 0, 1, 0, 0, 0, 1], tol);

test("rotationToZ matches the paper's convention, incl. poles", () => {
  for (const { v, R } of expected().rotations) {
    const M = rotationToZ(v);
    close(M, R, 1e-12);
    close(mat3.apply(M, v), [0, 0, 1], 1e-12);
  }
  close(rotationToZ([0, 0, -1]), [1, 0, 0, 0, -1, 0, 0, 0, -1]);
});

test("trackball stays orthonormal over many steps", () => {
  let C = [1, 0, 0, 0, 1, 0, 0, 0, 1];
  let s = 1;
  const rnd = () => ((s = (s * 16807) % 2147483647) / 2147483647 - 0.5) * 40;
  for (let i = 0; i < 10000; i++) C = trackball(C, rnd(), rnd(), 200);
  orthonormal(C, 1e-12);
});

test("project/unproject round trip; facing", () => {
  const C = trackball([1, 0, 0, 0, 1, 0, 0, 0, 1], 37, -21, 150);
  const geo = { cx: 300, cy: 250, r: 200 };
  const p = unit([0.3, -0.2, 0.9]);
  const front = facing(C, p);
  const [x, y, depth] = project(C, front, geo);
  assert.ok(depth >= 0);
  close(unproject(C, x, y, geo), front, 1e-9);
  assert.ok(Math.abs(norm(unproject(C, 10000, 0, geo)) - 1) < 1e-12); // clamped to the limb
  assert.ok(dot(facing(C, p), mat3.transpose(C).slice(6)) >= -1); // returns a unit vector
  close(facing(C, front.map((c) => -c)), front);
});

test("orthonormalize repairs a skewed matrix", () => {
  orthonormal(mat3.orthonormalize([1, 0.01, 0, 0, 1, 0.02, 0.03, 0, 1]), 1e-12);
});
