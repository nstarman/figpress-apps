# Data contract (data format 1)

```
data/<dataset>/
  manifest.json      figpress_apps_data, figpress-apps, name, meta, licence?, doi?, entries
  <entry>.npy        one per array — plain NumPy files: readers use np.load, no figpress-apps needed
  <entry>.json       one per json entry
  README.md          generated: what each file is and how to load it
```

## Python

```python
figpress_apps.export(out_dir, name, arrays, *, meta=None, json=None, units=None, descriptions=None,
              narrow=False, rtol=1e-6, licence=None, doi=None, overwrite=False) -> Path
figpress_apps.load(path) -> Dataset          # .name .meta .arrays .json .manifest; verifies checksums
```

- Names: dataset `[a-z][a-z0-9_-]*`, entries `[a-z][a-z0-9_]*`.
- dtypes stored: `<f4 <f8 |i1 |u1 <i2 <u2 <i4 <u4 |b1`, little-endian, C-order (converted
  automatically). Rejected: int64/uint64, float16, complex, object, string, structured, datetime.
- `narrow=[names]` (or `True`) turns float64 into float32 only if
  `max|x32 − x| ≤ rtol · range(x)`; otherwise `DataError` naming the entry and error.
- `meta` is any JSON object: put names, colours, initial views, citation URLs there.

## JavaScript

```js
import { loadData } from "figpress-apps/data.js";
const data = await loadData("points");      // or a notebook model, or {name, urls}
data.meta;                                   // the manifest's meta
data.arrays.xyz;                             // { data: Float64Array, shape: [400, 3], dtype: "<f8" }
data.json.style;                             // json entries
```

The same call works on the served site (fetches `data/<name>/…`), in the single file (inlined
copies) and in a notebook (synced bytes). Arrays are flat typed arrays in C order: element
`[i, j]` of an `[n, m]` array is `data[i * m + j]`.

## Loading a dataset inside `figpress-apps test`

`loadData` takes a `fetch`; in Node, read the exported files from disk:

```js
import { readFile } from "node:fs/promises";
import { loadData } from "figpress-apps/data.js";

const fileFetch = async (url) => {
  const buf = await readFile(new URL(url, `file://${process.cwd()}/`));
  return { ok: true, json: async () => JSON.parse(buf), arrayBuffer: async () => buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength) };
};
const data = await loadData("points", { fetch: fileFetch, base: "build/data/" }); // run after export.py
```
