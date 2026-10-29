"""Export the globe example's dataset: examples/globe/source.npz → <out>/globe/.

    uv run python examples/globe/export.py --out build/data
"""

import argparse
from pathlib import Path

import numpy as np

import figpress_apps

HERE = Path(__file__).parent
PAPER = "https://ui.adsabs.harvard.edu/abs/2026arXiv260940057S/abstract"


def squash(p: np.ndarray, r_globe: float, power: float) -> np.ndarray:
    """Radii r → R (r/R)^power, in units of the globe radius R; directions unchanged."""
    r = np.maximum(np.linalg.norm(p, axis=-1, keepdims=True), 1e-9)
    return p / r * (r / r_globe) ** power


def main(out: Path) -> Path:
    s = np.load(HERE / "source.npz")
    ids = [str(i) for i in s["ids"]]
    R, power = float(s["r_globe"]), float(s["radial_power"])
    arrays = {"texture": s["texture"]}
    descriptions = {"texture": "RGBA convexity regions; rows colatitude 0..pi, columns azimuth "
                               "0..2pi inclusive, in the globe frame"}
    for i in ids:
        T = s[f"{i}_T"]  # globe frame → simulation frame
        pos, pts = s[f"{i}_pos"], s[f"{i}_points"]
        arrays |= {
            f"{i}_pos": pos, f"{i}_d1": s[f"{i}_d1"], f"{i}_d2": s[f"{i}_d2"], f"{i}_points": pts,
            f"{i}_t": T,
            # globe-ready: back to the globe frame (T is orthogonal), radially squashed
            f"{i}_globe_line": squash(pos @ T, R, power).astype("<f4"),
            f"{i}_globe_points": squash(pts[::2] @ T, R, power).astype("<f4"),
        }
        descriptions |= {
            f"{i}_pos": "track, simulation frame", f"{i}_d1": "d(track)/dγ",
            f"{i}_d2": "curvature direction along the track", f"{i}_points": "particles, simulation frame",
            f"{i}_t": "matrix taking the globe frame to the simulation frame",
            f"{i}_globe_line": "track in the globe frame, radially squashed, globe radius = 1",
            f"{i}_globe_points": "particles in the globe frame, radially squashed",
        }
    meta = {
        "title": "Stream convexities in a common principal-axis frame",
        "paper": PAPER,
        "streams": [
            {"id": i, "name": str(n), "color": str(s[f"{i}_color"]), "view": s[f"{i}_view"].tolist(),
             "panel_rot_deg": float(s[f"{i}_panel_rot_deg"])}
            for i, n in zip(ids, s["names"])
        ],
        "camera": s["camera"].ravel().tolist(),
        "cap_deg": float(s["cap_deg"]),
    }
    units = {f"{i}_{k}": "kpc" for i in ids for k in ("pos", "points")}
    return figpress_apps.export(out, "globe", arrays, meta=meta, units=units, descriptions=descriptions,
                         licence="MIT", overwrite=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=Path("build/data"))
    print(main(ap.parse_args().out))
