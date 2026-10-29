"""Make examples/globe/source.npz from the paper's built globe explorer page.

The convexities single-galaxy paper's pipeline (src/scripts/data_streams_globe.py with
GLOBE_EXPLORER=1) writes a self-contained page, globe_explorer.html, with every array embedded as
base64. This script reads that page with numpy alone, so figpress-apps never depends on the paper's
environment. Run once:

    python examples/globe/make_source.py PATH/TO/globe_explorer.html
"""

import base64
import json
import re
import sys
from pathlib import Path

import numpy as np

IDS = {"Orbit 1": "orbit1", "Orbit 2": "orbit2", "Particle spray": "spray", "$N$-body": "nbody"}
MAX_POINTS = 3000


def main(page: str) -> None:
    text = Path(page).read_text(encoding="utf-8")
    data = json.loads(re.search(r"const DATA = (\{.*?\});\n", text, re.S).group(1))
    f32 = lambda b64: np.frombuffer(base64.b64decode(b64), dtype="<f4").reshape(-1, 3)  # noqa: E731
    tex = data["texture"]
    out = {
        "texture": np.frombuffer(base64.b64decode(tex["rgba"]), np.uint8).reshape(tex["h"], tex["w"], 4),
        "camera": np.array(data["camera"], dtype="<f8").reshape(3, 3),
        "r_globe": np.float64(data["rGlobe"]),
        "radial_power": np.float64(data["radialPower"]),
        "cap_deg": np.float64(data["capDeg"]),
        "ids": np.array(list(IDS.values())),
        "names": np.array([n.replace("$N$", "N") for n in IDS]),
    }
    for s in data["streams"]:
        i = IDS[s["name"]]
        points = f32(s["points"])
        step = max(1, int(np.ceil(len(points) / MAX_POINTS)))
        out |= {
            f"{i}_pos": f32(s["pos"]), f"{i}_d1": f32(s["d1"]), f"{i}_d2": f32(s["d2"]),
            f"{i}_points": points[::step],
            f"{i}_T": np.array(s["T"], dtype="<f8").reshape(3, 3),
            f"{i}_view": np.array(s["view"], dtype="<f8"),
            f"{i}_color": np.array(s["color"]),
            f"{i}_panel_rot_deg": np.float64(s["panelRotDeg"]),
        }
    np.savez_compressed(Path(__file__).with_name("source.npz"), **out)
    print({k: v.shape for k, v in out.items() if hasattr(v, "shape") and v.ndim})


if __name__ == "__main__":
    main(sys.argv[1])
