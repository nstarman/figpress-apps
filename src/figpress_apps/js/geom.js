// Pure 3-D geometry: vectors, row-major 3×3 matrices, the paper's sky rotation, trackball
// rotation and orthographic projection. A camera is a Mat3 whose rows are page-right, page-up
// and toward-the-viewer, expressed in the data frame.

export const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
export const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
export const norm = (a) => Math.hypot(a[0], a[1], a[2]);
export const scale = (a, s) => [a[0] * s, a[1] * s, a[2] * s];
export const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
export const unit = (a) => scale(a, 1 / norm(a));

export const mat3 = {
  identity: () => [1, 0, 0, 0, 1, 0, 0, 0, 1],
  row: (A, i) => [A[3 * i], A[3 * i + 1], A[3 * i + 2]],
  mul(A, B) {
    const C = new Array(9);
    for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) {
      C[3 * i + j] = A[3 * i] * B[j] + A[3 * i + 1] * B[3 + j] + A[3 * i + 2] * B[6 + j];
    }
    return C;
  },
  apply: (A, v) => [0, 1, 2].map((i) => A[3 * i] * v[0] + A[3 * i + 1] * v[1] + A[3 * i + 2] * v[2]),
  applyT: (A, v) => [0, 1, 2].map((i) => A[i] * v[0] + A[3 + i] * v[1] + A[6 + i] * v[2]),
  transpose: (A) => [A[0], A[3], A[6], A[1], A[4], A[7], A[2], A[5], A[8]],
  /** Gram–Schmidt on the rows, keeping a right-handed frame. */
  orthonormalize(A) {
    const r0 = unit(mat3.row(A, 0));
    const r1 = unit(add(mat3.row(A, 1), scale(r0, -dot(r0, mat3.row(A, 1)))));
    return [...r0, ...r1, ...cross(r0, r1)];
  },
};

/** The rotation about v × z that takes unit v to +z (the paper's sky convention).
 *  Rows are sky-x, sky-y and v. The antiparallel case is diag(1, −1, −1). */
export function rotationToZ(v) {
  const s = Math.hypot(v[0], v[1]), c = v[2];
  if (s < 1e-12) return c > 0 ? mat3.identity() : [1, 0, 0, 0, -1, 0, 0, 0, -1];
  const kx = v[1] / s, ky = -v[0] / s;
  const K = [0, 0, ky, 0, 0, -kx, -ky, kx, 0];
  const K2 = mat3.mul(K, K);
  return K.map((k, i) => (i % 4 === 0 ? 1 : 0) + s * k + (1 - c) * K2[i]);
}

/** Turn the globe by a drag of (dx, dy) screen pixels on a globe of radius r pixels. */
export function trackball(camera, dx, dy, r) {
  const ay = dx / r, ax = dy / r;
  const cy = Math.cos(ay), sy = Math.sin(ay), cx = Math.cos(ax), sx = Math.sin(ax);
  const Ry = [cy, 0, sy, 0, 1, 0, -sy, 0, cy];
  const Rx = [1, 0, 0, 0, cx, -sx, 0, sx, cx];
  return mat3.orthonormalize(mat3.mul(mat3.mul(Rx, Ry), camera));
}

/** Screen position and depth (> 0 toward the viewer) of data-frame point p. */
export function project(camera, p, { cx, cy, r }) {
  return [cx + r * dot(mat3.row(camera, 0), p), cy - r * dot(mat3.row(camera, 1), p), dot(mat3.row(camera, 2), p)];
}

/** The unit vector on the camera-facing hemisphere under screen point (x, y), clamped to the limb. */
export function unproject(camera, x, y, { cx, cy, r }) {
  let u = (x - cx) / r, v = -(y - cy) / r;
  const rr = u * u + v * v;
  if (rr > 1) { u /= Math.sqrt(rr); v /= Math.sqrt(rr); }
  return mat3.applyT(camera, [u, v, Math.sqrt(Math.max(0, 1 - u * u - v * v))]);
}

/** v or −v, whichever end of the line faces the camera. */
export const facing = (camera, v) => (dot(mat3.row(camera, 2), v) >= 0 ? v : scale(v, -1));
