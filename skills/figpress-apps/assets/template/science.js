// The science step: pure functions, no DOM, so `figpress-apps test` can check them against Python.
import { rotationToZ, mat3 } from "figpress-apps/geom.js";

/** Project n×3 points onto the sky for a unit viewing direction → {xy (flat n×2), readout}. */
export function project(xyz, view) {
  const R = rotationToZ(view), ex = mat3.row(R, 0), ey = mat3.row(R, 1);
  const n = xyz.length / 3, xy = new Float32Array(2 * n);
  let r = 0;
  for (let i = 0; i < n; i++) {
    const p = [xyz[3 * i], xyz[3 * i + 1], xyz[3 * i + 2]];
    xy[2 * i] = ex[0] * p[0] + ex[1] * p[1] + ex[2] * p[2];
    xy[2 * i + 1] = ey[0] * p[0] + ey[1] * p[1] + ey[2] * p[2];
    r += Math.hypot(xy[2 * i], xy[2 * i + 1]);
  }
  return { xy, readout: `mean projected radius ${(r / n).toFixed(3)}` };
}
