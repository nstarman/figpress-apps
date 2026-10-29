"""Export this webapp's dataset. Replace the example arrays with the paper's.

    uv run python webapps/NAME/export.py --out build/data
"""

import argparse
from pathlib import Path

import numpy as np

import figpress_apps

DATASET = "points"  # the name the app loads (widget.js)


def main(out: Path) -> Path:
    t = np.linspace(0, 6 * np.pi, 400)
    xyz = np.stack([np.cos(t), np.sin(t), t / (6 * np.pi) - 0.5], axis=1)  # a helix, as float64
    return figpress_apps.export(
        out, DATASET,
        {"xyz": xyz},                          # float64 stays float64 unless you pass narrow=[...]
        meta={"title": "Example points", "view": [0.0, 0.0, 1.0]},
        units={"xyz": "kpc"}, descriptions={"xyz": "example 3-D points"},
        licence="MIT", overwrite=True,
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("build/data"))
    print(main(ap.parse_args().out))
