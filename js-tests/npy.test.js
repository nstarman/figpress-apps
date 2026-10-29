import { test } from "node:test";
import assert from "node:assert/strict";
import { parseNpy, asTyped } from "figpress-apps/npy.js";
import { read, expected } from "./helpers.js";

const CLASS = { "<f4": Float32Array, "<f8": Float64Array, "|i1": Int8Array, "|u1": Uint8Array,
  "<i2": Int16Array, "<u2": Uint16Array, "<i4": Int32Array, "<u4": Uint32Array, "|b1": Uint8Array };

test("parses every allowed dtype and shape", () => {
  for (const [name, e] of Object.entries(expected().npy)) {
    const buf = read(name);
    const a = parseNpy(buf);
    assert.equal(a.dtype, e.dtype, name);
    assert.deepEqual(a.shape, e.shape, name);
    assert.ok(a.data instanceof CLASS[e.dtype], name);
    assert.deepEqual(Array.from(a.data, Number), e.values, name);
    assert.equal(a.data.buffer, buf, `${name}: zero-copy view`);
  }
});

test("asTyped converts DataViews, copying only when unaligned", () => {
  const buf = new Float32Array([1, 2, 3]).buffer;
  const aligned = asTyped(new DataView(buf), "<f4");
  assert.deepEqual(Array.from(aligned), [1, 2, 3]);
  assert.equal(aligned.buffer, buf);
  const shifted = new Uint8Array(13);
  shifted.set(new Uint8Array(buf), 1);
  const un = asTyped(new DataView(shifted.buffer, 1, 12), "<f4");
  assert.deepEqual(Array.from(un), [1, 2, 3]);
  assert.deepEqual(Array.from(asTyped(buf, "<f4")), [1, 2, 3]);
});

test("rejects big-endian, Fortran order and unsupported dtypes", () => {
  assert.throws(() => parseNpy(read("big_endian.npy")), /big-endian|dtype/);
  assert.throws(() => parseNpy(read("fortran.npy")), /Fortran/);
  assert.throws(() => parseNpy(read("int64.npy")), /dtype/);
  assert.throws(() => parseNpy(new ArrayBuffer(16)), /not a \.npy/);
});
