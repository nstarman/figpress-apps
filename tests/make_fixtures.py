"""Write fixtures for the JS tests (js-tests/fixtures/), using numpy and figpress_apps.export.

Run before `node --test js-tests/*.test.js`:  uv run python tests/make_fixtures.py
"""

import json
import shutil
import sys
from pathlib import Path

import numpy as np

import figpress_apps

OUT = Path(__file__).resolve().parents[1] / "js-tests" / "fixtures"
DTYPES = ["<f4", "<f8", "|i1", "|u1", "<i2", "<u2", "<i4", "<u4", "|b1"]


def values(dtype, shape):
    n = int(np.prod(shape))
    if dtype == "|b1":
        return (np.arange(n) % 3 == 0).reshape(shape)
    base = np.arange(n) - (n // 2 if dtype[1] in "if" else 0)
    return (base * (0.5 if dtype[1] == "f" else 1)).reshape(shape).astype(np.dtype(dtype))


def rotation_to_z(v):
    """The paper's convention: the rotation about v x z that takes unit v to +z."""
    s, c = np.hypot(v[0], v[1]), v[2]
    if s < 1e-12:
        return np.eye(3) if c > 0 else np.diag([1.0, -1.0, -1.0])
    kx, ky = v[1] / s, -v[0] / s
    K = np.array([[0, 0, ky], [0, 0, -kx], [-ky, kx, 0]])
    return np.eye(3) + s * K + (1 - c) * K @ K


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True)
    expected = {"npy": {}, "rotations": []}

    for dtype in DTYPES:
        for shape in [(3, 2), (0,), (1,), (2, 3, 4)]:
            a = values(dtype, shape)
            name = f"{dtype[1:]}_{'x'.join(map(str, shape))}.npy"
            np.save(OUT / name, a)
            expected["npy"][name] = {"dtype": dtype, "shape": list(shape),
                                     "values": a.astype(float).ravel().tolist()}
    np.save(OUT / "big_endian.npy", np.arange(3, dtype=">f4"))
    np.save(OUT / "fortran.npy", np.asfortranarray(np.arange(6, dtype="<f4").reshape(2, 3)))
    np.save(OUT / "int64.npy", np.arange(3, dtype="<i8"))

    figpress_apps.export(OUT, "ds", {"track": values("<f4", (5, 3)), "flag": values("|b1", (5,))},
                  meta={"title": "fixture"}, json={"style": {"color": "#123456"}})

    rng = np.random.default_rng(1)
    dirs = [np.array([0.0, 0, 1]), np.array([0.0, 0, -1]), np.array([1.0, 0, 0]),
            np.array([0.0, 1, 0])] + [v / np.linalg.norm(v) for v in rng.normal(size=(16, 3))]
    for v in dirs:
        expected["rotations"].append({"v": v.tolist(), "R": rotation_to_z(v).ravel().tolist()})

    # the globe example's dataset, for the acceptance test
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples" / "globe"))
    import export as globe_export

    globe_export.main(OUT)

    (OUT / "expected.json").write_text(json.dumps(expected), encoding="utf-8")
    print(f"wrote fixtures to {OUT}")


if __name__ == "__main__":
    main()
