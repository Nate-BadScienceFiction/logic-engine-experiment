"""Render assets/test-timeline.png/.svg: passing tests over time, and cross-check scores.

Top panel: evidence/test-timeline-2026-09-25.csv, dated passing-test counts for the earlier
engine, reconstructed from the test log's git history, pytest summaries in commit messages,
and log lines that carry their own timestamps (see evidence/README.md). The rewrite's new
suite is noted rather than plotted, because the two suites aren't comparable.
Bottom panel: evidence/development-progress-2026-09-25.json, the 21 cross-checks replayed
on saved versions of both engines.

Requires Matplotlib. Run from the repository root:
    python evidence/render-test-timeline.py
"""
import csv
import json
from datetime import date, datetime, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parent.parent
SERIES = ROOT / "evidence" / "test-timeline-2026-09-25.csv"
REPLAY = ROOT / "evidence" / "development-progress-2026-09-25.json"

INK, MUTED, GRID, PAPER = "#283238", "#586269", "#e3e5e3", "#faf9f6"
OLD, NEW = "#1d6fa3", "#c0612b"

# ---- data -------------------------------------------------------------------
rows = []
with SERIES.open(encoding="utf-8") as fh:
    for row in csv.DictReader(fh):
        if row["source"].startswith("rewrite"):
            continue
        rows.append((row["timestamp"], date.fromisoformat(row["date"]), int(row["passed"])))


def last_per_day(points):
    """Chronological by timestamp; the last observation of each day wins."""
    out = {}
    for _, d, p in sorted(points):
        out[d] = p
    return sorted(out.items())


old = last_per_day(rows)

replay = json.loads(REPLAY.read_text(encoding="utf-8"))
checks = {"old": [], "new": []}
for snap in replay["snapshots"]:
    d = datetime.fromisoformat(snap["committer_date"]).date()
    checks[snap["engine"]].append((d, snap["counts"]["pass"]))
for key in checks:
    checks[key].sort()

# ---- figure -----------------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11,
    "text.color": INK, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "svg.fonttype": "none", "svg.hashsalt": "cyclops-test-timeline",
})
fig, (top, bottom) = plt.subplots(
    2, 1, figsize=(10, 7.4), sharex=True, facecolor=PAPER,
    gridspec_kw={"height_ratios": [3, 1.35], "hspace": 0.28})
fig.subplots_adjust(left=.085, right=.97, top=.82, bottom=.16)
for ax in (top, bottom):
    ax.set_facecolor(PAPER)
    ax.yaxis.grid(True, color=GRID, lw=1)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", length=0, pad=6)
    for spine in ax.spines.values():
        spine.set_visible(False)

# Top: the earlier engine's passing tests, drawn as steps (a count holds until the next observation).
top.step([d for d, _ in old], [p for _, p in old], where="post", color=OLD, lw=2)
peak = max(old, key=lambda pt: pt[1])
split = next(pt for pt in old if pt[0] >= date(2026, 2, 21))
for (d, p), txt, dy, ha in [
    (old[0], f"{old[0][1]:,}", 260, "center"),
    (split, f"{split[1]:,}", 260, "right"),
    (peak, f"{peak[1]:,}", 200, "center"),
    (old[-1], f"{old[-1][1]:,}", 200, "center"),
]:
    top.plot([d], [p], "o", ms=5.5, color=OLD, zorder=5)
    top.text(d, p + dy, txt, ha=ha, va="bottom", fontsize=9.5, color=INK)
top.text(date(2026, 9, 18), 900, "rewrite:\na new suite,\n540 → 1,144\n(not comparable)",
         ha="center", va="bottom", fontsize=8.8, color=MUTED)
top.set_ylim(0, 7300)
top.set_yticks([0, 2000, 4000, 6000])
top.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v):,}"))
top.set_ylabel("Passing tests", fontsize=10.5)

MILESTONES = [
    (date(2025, 10, 12), "tabling added\n(depth limits stayed)"),
    (date(2026, 2, 22), "moves to its\nown repository"),
    (date(2026, 6, 14), "AI audits; dead\ncode deleted"),
    (date(2026, 9, 13), "rewrite\nbegins"),
]
for d, label in MILESTONES:
    for ax in (top, bottom):
        ax.axvline(d, color=GRID, lw=1, zorder=0)
    top.text(d, 7380, label, ha="center", va="bottom", fontsize=9, color=MUTED)

# Bottom: the 21 cross-checks, replayed on saved versions (commit dates).
for key, color in (("old", OLD), ("new", NEW)):
    pts = checks[key]
    bottom.plot([d for d, _ in pts], [p for _, p in pts], "o-", color=color, lw=2, ms=5.5)
bottom.text(checks["old"][0][0], checks["old"][0][1] + 3.2, f"{checks['old'][0][1]}", ha="center", fontsize=9.5, color=INK)
bottom.text(checks["old"][-1][0], checks["old"][-1][1] + 3.2, f"{checks['old'][-1][1]}", ha="center", fontsize=9.5, color=INK)
bottom.text(checks["new"][0][0] - timedelta(days=4), checks["new"][0][1] - 1.2, f"{checks['new'][0][1]}",
            ha="right", va="center", fontsize=9.5, color=INK)
bottom.text(checks["new"][-1][0], 21.6, f"{checks['new'][-1][1]}", ha="left", fontsize=9.5, color=INK)
bottom.set_ylim(0, 24)
bottom.set_yticks([0, 7, 14, 21])
bottom.set_ylabel("Cross-checks\npassed (of 21)", fontsize=10.5)
bottom.set_xlim(date(2025, 8, 15), date(2026, 10, 12))
bottom.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[9, 11, 1, 3, 5, 7]))
bottom.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))

fig.text(.085, .945, "Passing tests, and scores on 21 cross-checks", fontsize=17, weight="bold")
fig.text(.085, .89, "Top: passing tests in the earlier engine's suite, Sep 2025 to Aug 2026.\n"
         "Bottom: 21 cross-checks (12 refereed by SWI-Prolog) replayed on saved versions of the earlier engine (blue) and the rewrite (orange).",
         fontsize=9.6, color=MUTED)
fig.text(.085, .018,
         "Steps show the last logged count per day, so most mid-refactor dips are hidden (the worst logged: 149 passing, Sep 9, 2025). Runner settings\n"
         "changed several times, so small zigzags aren't meaningful. The cross-checks were written in Sep 2026; versions before May 2026 couldn't\n"
         "be replayed; two of the rewrite's passes are test-runner timeouts. Data and method: evidence/README.md.",
         fontsize=8.2, color=MUTED)

out = ROOT / "assets"
out.mkdir(exist_ok=True)
fig.savefig(out / "test-timeline.png", dpi=160, facecolor=PAPER)
fig.savefig(out / "test-timeline.svg", facecolor=PAPER, metadata={"Date": None})
print("wrote assets/test-timeline.png and .svg")
