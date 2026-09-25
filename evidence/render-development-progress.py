"""Render the published milestone graph from the verified historical replay.

Requires Matplotlib. Run from the repository root:
    python evidence/render-development-progress.py
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


ROOT = Path(__file__).resolve().parent.parent
report = json.loads((ROOT / "evidence/development-progress-2026-09-25.json").read_text(encoding="utf-8"))
if not report["complete"] or report["endpoint_verdicts_match_reference"] != {"new": True, "old": True}:
    raise RuntimeError("Render only a complete, verified replay")
new = [s for s in report["snapshots"] if s["engine"] == "new"]
old = [s for s in report["snapshots"] if s["engine"] == "old"]
first_current = next(s for s in new if s["counts"] == new[-1]["counts"])
selected = [old[-1], new[0], first_current]
passes = [s["counts"]["pass"] for s in selected]
timeouts = [s["passes_by_external_timeout"] for s in selected]
completed = [p - t for p, t in zip(passes, timeouts)]

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 12,
    "text.color": "#283238", "axes.labelcolor": "#283238",
    "xtick.color": "#283238", "ytick.color": "#586269",
    "svg.fonttype": "none", "svg.hashsalt": "cyclops-progress-2026-09-25",
})
fig, ax = plt.subplots(figsize=(8.4, 5.7), facecolor="#faf9f6")
ax.set_facecolor("#faf9f6")
fig.subplots_adjust(left=.09, right=.98, top=.78, bottom=.26)
fig.text(.09, .94, "Same 21 checks, three milestones", fontsize=19, weight="semibold")
fig.text(.09, .885, "Retrospective results on the same 21 selected checks.", fontsize=12)
ax.set_axisbelow(True)
ax.yaxis.grid(True, color="#d6d9d8", linewidth=.8)
ax.bar(range(3), completed, width=.49, color="#215e73")
ax.bar(range(3), timeouts, bottom=completed, width=.49,
       color="#ebca8e", edgecolor="#7b5a24", hatch="///", linewidth=.6)
for index, score in enumerate(passes):
    ax.text(index, score + .7, f"{score} / 21", ha="center", va="bottom", fontsize=17, weight="semibold")
ax.set_ylim(0, 23)
ax.set_yticks([0, 7, 14, 21])
ax.set_ylabel("Checks passing", fontsize=12)
ax.set_xticks(range(3), [
    "Earlier engine\nAug 30",
    "First rewrite\nSep 14",
    "Next rewrite\nSep 15",
])
ax.tick_params(axis="both", length=0, pad=10)
for spine in ax.spines.values():
    spine.set_visible(False)
fig.legend(handles=[Patch(facecolor="#215e73", label="Pass without external timeout"),
                    Patch(facecolor="#ebca8e", edgecolor="#7b5a24", hatch="///", label="Accepted timeout")],
           loc="lower left", bbox_to_anchor=(.075, .11), ncol=2, frameon=False, fontsize=10.5)
fig.text(.09, .065, "All dates: 2026. This measures case outcomes, not development speed.", fontsize=10.5)
fig.text(.09, .025, "Later rewrite snapshots retain 18/21. Source: historical replay, Sep 25.", fontsize=10.5)
description = (
    "The earlier engine's August 30 revision passes 10 of 21 checks. The first rewrite "
    "revision on September 14 passes 17, including one external timeout accepted under "
    "an unbounded-search rule. The September 15 rewrite passes 18, including two such "
    "timeouts. Commit intervals from the seed prompt are approximately 10 and 35 hours; "
    "they do not measure active labor. Later sampled rewrite revisions retain 18 passes."
)
assets = ROOT / "assets"
assets.mkdir(exist_ok=True)
fig.savefig(assets / "development-progress.svg", metadata={
    "Title": "Cyclops Storm: same 21 checks, three milestones", "Description": description, "Date": None})
fig.savefig(assets / "development-progress.png", dpi=180, metadata={"Description": description})
plt.close(fig)
print("Wrote assets/development-progress.svg and assets/development-progress.png")
