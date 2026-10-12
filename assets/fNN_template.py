# figures/fNN_slug.py — figure script template (paper-figures skill, §4).
# Rename to e.g. f03_plane.py: one file = one figure. Replace this comment and
# the docstring; the docstring IS the caption draft (one line per panel).
"""Figure N. One-line statement of what the figure shows.

(a) What panel (a) shows, how it is computed, what each colour means.
(b) What panel (b) shows. Values come from results/estimates.json;
nothing is typed by hand. Chart form (§5): <question the figure answers>.
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
import style as S  # noqa: E402  (only S.* below — no rcParams, no hex, no bbox_inches)

RESULTS = Path(__file__).parent.parent / "results"


def load():
    """Read from results_dir only — never hardcode a number."""
    return json.loads((RESULTS / "estimates.json").read_text(encoding="utf-8"))


def main():
    d = load()
    S.apply_from_config()  # or S.apply("trb", "final")
    fig, axes = plt.subplots(1, 2, figsize=(S.FULL, 2.6))  # width fixed, height chosen

    # --- panel (a): dot plot with CI whiskers (example form) -----------------
    ax = axes[0]
    groups = [row["group"] for row in d["rows"]]
    est = [row["est"] for row in d["rows"]]
    lo = [row["lo"] for row in d["rows"]]
    hi = [row["hi"] for row in d["rows"]]
    y = range(len(groups))
    ax.hlines(y, lo, hi, color=S.C["obs"], linewidth=1.0)
    ax.plot(est, y, S.MARKERS["obs"], color=S.C["obs"], markersize=3.5,
            linestyle="none")
    ax.set_yticks(list(y), groups)
    ax.set_xlabel("Estimate (95% CI)")  # units in the label, sentence case
    S.light_grid(ax, axis="x")
    S.panel_title(ax, "a", "Estimates by group")

    # --- panel (b) ------------------------------------------------------------
    ax = axes[1]
    ax.plot(d["x"], d["obs"], color=S.C["obs"], linestyle=S.LINESTYLES["obs"],
            label="Observed")
    ax.plot(d["x"], d["adj"], color=S.C["adj"], linestyle=S.LINESTYLES["adj"],
            label="Adjusted")
    ax.set_xlabel("Year")
    ax.set_ylabel("Crashes (thousands)")
    ax.legend()  # only when direct labeling is impossible
    S.panel_title(ax, "b", "Observed and adjusted series")

    S.finish(fig)
    S.save(fig, Path(__file__).stem)  # mode="exact"


if __name__ == "__main__":
    main()
