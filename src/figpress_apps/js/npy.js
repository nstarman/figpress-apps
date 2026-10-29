// Read NumPy .npy files (format 1.0/2.0/3.0) into typed-array views.
// Only little-endian, C-order arrays of figpress-apps' allowed dtypes (see the data contract).

const TYPES = {
  "<f4": Float32Array, "<f8": Float64Array,
  "|i1": Int8Array, "<i1": Int8Array, "|u1": Uint8Array, "<u1": Uint8Array,
  "<i2": Int16Array, "<u2": Uint16Array, "<i4": Int32Array, "<u4": Uint32Array,
  "|b1": Uint8Array,
};

/** Parse a .npy buffer → {data: TypedArray (a view, no copy), shape, dtype}. */
export function parseNpy(buffer) {
  const bytes = new Uint8Array(buffer);
  if (bytes.length < 10 || bytes[0] !== 0x93 || String.fromCharCode(...bytes.subarray(1, 6)) !== "NUMPY") {
    throw new Error("not a .npy file");
  }
  const major = bytes[6];
  const view = new DataView(buffer);
  const [headerLen, start] = major === 1 ? [view.getUint16(8, true), 10] : [view.getUint32(8, true), 12];
  const header = new TextDecoder(major === 3 ? "utf-8" : "latin1").decode(bytes.subarray(start, start + headerLen));
  const field = (key) => header.match(new RegExp(`'${key}':\\s*([^,}]+)`))?.[1]?.trim();
  const dtype = field("descr")?.replace(/'/g, "");
  if (/True/.test(field("fortran_order") ?? "")) throw new Error("Fortran-order .npy arrays are not supported");
  const Type = TYPES[dtype];
  if (!Type) throw new Error(`unsupported .npy dtype ${dtype} (big-endian or not allowed by the data contract)`);
  const shape = (header.match(/'shape':\s*\(([^)]*)\)/)?.[1] ?? "").split(",").map((x) => x.trim()).filter(Boolean).map(Number);
  const length = shape.reduce((a, b) => a * b, 1);
  return { data: new Type(buffer, start + headerLen, length), shape, dtype };
}

/** View binary data (an ArrayBuffer or a DataView, as notebooks deliver it) as a typed array. */
export function asTyped(source, dtype) {
  const Type = TYPES[dtype];
  if (!Type) throw new Error(`unsupported dtype ${dtype}`);
  const [buffer, offset, length] = source instanceof ArrayBuffer
    ? [source, 0, source.byteLength] : [source.buffer, source.byteOffset, source.byteLength];
  if (offset % Type.BYTES_PER_ELEMENT === 0) return new Type(buffer, offset, length / Type.BYTES_PER_ELEMENT);
  return new Type(buffer.slice(offset, offset + length)); // unaligned: copy once
}
