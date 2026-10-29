"""The data contract: a dataset folder of `.npy` files plus `manifest.json`.

See specs/001-figkit-v0-1/contracts/data-format.md. Readers need only numpy to use the files.
"""

from __future__ import annotations

import hashlib
import json as _json
import re
import shutil
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

FORMAT = 1  #: data-format major version, `figpress_apps_data` in every manifest
ALLOWED = ("<f4", "<f8", "|i1", "|u1", "<i2", "<u2", "<i4", "<u4", "|b1")
_ENTRY = re.compile(r"[a-z][a-z0-9_]*\Z")
_DATASET = re.compile(r"[a-z][a-z0-9_-]*\Z")
_TOP_KEYS = {"figpress_apps_data", "figpress_apps", "name", "meta", "licence", "doi", "entries"}
# Datasets written before the rename (figkit ≤ 0.2) carry these keys; they still load.
_OLD_KEYS = {"figkit_data": "figpress_apps_data", "figkit": "figpress_apps"}
_ARRAY_KEYS = {"kind", "file", "dtype", "shape", "source_dtype", "sha256", "unit", "description"}
_JSON_KEYS = {"kind", "file", "sha256", "description"}


class DataError(ValueError):
    """A dataset could not be written or read under the data contract."""


@dataclass
class Dataset:
    """A loaded dataset folder."""

    name: str
    meta: dict
    arrays: dict[str, np.ndarray] = field(default_factory=dict)
    json: dict[str, Any] = field(default_factory=dict)
    manifest: dict = field(default_factory=dict)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _little_endian(a: np.ndarray) -> np.ndarray:
    if a.dtype.byteorder == ">" or (a.dtype.byteorder == "=" and np.little_endian is False):
        a = a.astype(a.dtype.newbyteorder("<"))
    return np.ascontiguousarray(a)


def _narrow(name: str, x: np.ndarray, rtol: float) -> np.ndarray:
    """float64 → float32, only if the rounding error is small against the data's range."""
    with np.errstate(over="ignore"):
        x32 = x.astype("<f4")
    if not np.array_equal(np.isnan(x), np.isnan(x32)) or not np.array_equal(
        np.isposinf(x), np.isposinf(x32)) or not np.array_equal(np.isneginf(x), np.isneginf(x32)):
        raise DataError(f"cannot narrow {name!r} to float32: values overflow or change finiteness")
    finite = np.isfinite(x)
    if finite.any():
        err = float(np.max(np.abs(x32[finite].astype("f8") - x[finite])))
        scale = max(float(np.ptp(x[finite])), float(np.finfo(np.float32).tiny))
        if err > rtol * scale:
            raise DataError(
                f"cannot narrow {name!r} to float32: max error {err:.3g} exceeds threshold "
                f"{rtol * scale:.3g} (rtol {rtol:g} x range {scale:.3g}); keep it float64 or "
                f"subtract an offset first"
            )
    return x32


def _readme(manifest: dict) -> str:
    lines = [f"# Dataset `{manifest['name']}`", "",
             f"Written by figpress-apps {manifest['figpress_apps']} (data format {manifest['figpress_apps_data']})."]
    if manifest.get("licence"):
        lines.append(f"Licence: {manifest['licence']}.")
    if manifest.get("doi"):
        lines.append(f"DOI: {manifest['doi']}.")
    lines += ["", "| File | dtype | shape | unit | description |", "|---|---|---|---|---|"]
    for e in manifest["entries"].values():
        shape = "×".join(map(str, e.get("shape", []))) or "–"
        lines.append(f"| `{e['file']}` | {e.get('dtype', 'json')} | {shape} | "
                     f"{e.get('unit', '')} | {e.get('description', '')} |")
    first = next((e["file"] for e in manifest["entries"].values() if e["kind"] == "array"), "x.npy")
    lines += ["", "Each `.npy` file is a standard NumPy array; no figpress-apps needed:", "",
              "```python", "import numpy as np", f'x = np.load("{first}")', "```", ""]
    return "\n".join(lines)


def export(
    out_dir: str | Path,
    name: str,
    arrays: Mapping[str, Any],
    *,
    meta: Mapping[str, Any] | None = None,
    json: Mapping[str, Any] | None = None,
    units: Mapping[str, str] | None = None,
    descriptions: Mapping[str, str] | None = None,
    narrow: Iterable[str] | bool = False,
    rtol: float = 1e-6,
    licence: str | None = None,
    doi: str | None = None,
    overwrite: bool = False,
) -> Path:
    """Write ``arrays`` (and optional JSON entries) as the dataset ``out_dir / name``."""
    from figpress_apps import __version__

    if not _DATASET.match(name or ""):
        raise DataError(f"dataset name {name!r} must match [a-z][a-z0-9_-]*")
    json = dict(json or {})
    for key in [*arrays, *json]:
        if not _ENTRY.match(key):
            raise DataError(f"entry name {key!r} must match [a-z][a-z0-9_]*")
    if clash := set(arrays) & set(json):
        raise DataError(f"entry name {sorted(clash)[0]!r} used for both an array and a json entry")
    narrow_set = set(arrays) if narrow is True else set(narrow or ())
    if unknown := narrow_set - set(arrays):
        raise DataError(f"cannot narrow unknown entries {sorted(unknown)}")
    units, descriptions = dict(units or {}), dict(descriptions or {})

    prepared = {}
    for key, value in arrays.items():
        a = np.asarray(value)
        source = str(a.dtype)
        a = _little_endian(a)
        if key in narrow_set and a.dtype.str == "<f8":
            a = _narrow(key, a, rtol)
        if a.dtype.str not in ALLOWED:
            raise DataError(f"entry {key!r} has dtype {source}; allowed: float32/64, "
                            f"int8-32, uint8-32, bool (put strings in meta)")
        prepared[key] = (a, source)

    path = Path(out_dir) / name
    if path.exists():
        if not overwrite:
            raise DataError(f"{path} exists; pass overwrite=True to replace it")
        shutil.rmtree(path)
    path.mkdir(parents=True)

    entries: dict[str, dict] = {}
    for key, (a, source) in prepared.items():
        file = path / f"{key}.npy"
        np.save(file, a, allow_pickle=False)
        entries[key] = {"kind": "array", "file": file.name, "dtype": a.dtype.str,
                        "shape": list(a.shape), "source_dtype": source, "sha256": _sha256(file)}
        if key in units:
            entries[key]["unit"] = units[key]
        if key in descriptions:
            entries[key]["description"] = descriptions[key]
    for key, value in json.items():
        file = path / f"{key}.json"
        file.write_text(_json.dumps(value, indent=1), encoding="utf-8")
        entries[key] = {"kind": "json", "file": file.name, "sha256": _sha256(file)}
        if key in descriptions:
            entries[key]["description"] = descriptions[key]

    manifest = {"figpress_apps_data": FORMAT, "figpress_apps": __version__, "name": name, "meta": dict(meta or {})}
    if licence:
        manifest["licence"] = licence
    if doi:
        manifest["doi"] = doi
    manifest["entries"] = entries
    (path / "manifest.json").write_text(_json.dumps(manifest, indent=1), encoding="utf-8")
    (path / "README.md").write_text(_readme(manifest), encoding="utf-8")
    return path


def read_manifest(path: str | Path) -> dict:
    """Read and validate ``path/manifest.json`` (keys and data-format version only)."""
    path = Path(path)
    try:
        m = _json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise DataError(f"{path / 'manifest.json'} not found") from None
    for old, new in _OLD_KEYS.items():
        if old in m:
            value = m.pop(old)
            m.setdefault(new, value)
    if extra := set(m) - _TOP_KEYS:
        raise DataError(f"{path}: unknown manifest keys {sorted(extra)}")
    if m.get("figpress_apps_data") != FORMAT:
        raise DataError(f"{path}: dataset has figpress_apps_data {m.get('figpress_apps_data')}, "
                        f"this figpress-apps reads figpress_apps_data {FORMAT}")
    for key, e in m.get("entries", {}).items():
        allowed = _ARRAY_KEYS if e.get("kind") == "array" else _JSON_KEYS
        if e.get("kind") not in ("array", "json") or (extra := set(e) - allowed):
            raise DataError(f"{path}: entry {key!r} is malformed")
    return m


def load(path: str | Path) -> Dataset:
    """Load and verify a dataset folder written by :func:`export`."""
    path = Path(path)
    m = read_manifest(path)
    ds = Dataset(name=m["name"], meta=m.get("meta", {}), manifest=m)
    for key, e in m["entries"].items():
        file = path / e["file"]
        if not file.exists():
            raise DataError(f"{file} not found")
        if _sha256(file) != e["sha256"]:
            raise DataError(f"{file}: sha256 does not match the manifest")
        if e["kind"] == "json":
            ds.json[key] = _json.loads(file.read_text(encoding="utf-8"))
            continue
        a = np.load(file, allow_pickle=False)
        if a.dtype.str != e["dtype"] or list(a.shape) != e["shape"]:
            raise DataError(f"{file}: header {a.dtype.str} {list(a.shape)} does not match "
                            f"the manifest {e['dtype']} {e['shape']}")
        ds.arrays[key] = a
    return ds
