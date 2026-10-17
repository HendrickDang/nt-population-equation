"""
Builds the supporting figures for the A1 poster.

    python src/build_poster_figures.py

Colour use follows the job each chart does: the components chart and the
volatility chart encode identity, so each component keeps the hue it has
everywhere else in the project. The dependency and decade charts encode one
measure, so each uses a single hue, the one belonging to the component the
chart is about.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"

BG = "#fcfcfb"
INK = "#16181c"
INK2 = "#52514e"
INK3 = "#8b857a"
GRID = "#e4e3e0"

NATURAL, OVERSEAS, INTERSTATE = "#2a78d6", "#eb6834", "#1baf7a"
LABELS = {
    "natural_increase": "Natural increase",
    "net_overseas_migration": "Net overseas migration",
    "net_interstate_migration": "Net interstate migration",
}
COLOURS = {
    "natural_increase": NATURAL,
    "net_overseas_migration": OVERSEAS,
    "net_interstate_migration": INTERSTATE,
}


def frame(ax, *, xlabel: str = "") -> None:
    ax.set_facecolor(BG)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#c9c8c4")
    ax.tick_params(colors=INK2, labelsize=13, length=0)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=12.5, color=INK3, labelpad=10)


def hbars(path: str, labels, values, colours, fmt, title: str, xlabel: str) -> None:
    fig, ax = plt.subplots(figsize=(6.6, 3.5), dpi=300)
    fig.patch.set_facecolor(BG)
    y = range(len(labels))
    ax.barh(list(y), values, color=colours, height=0.56, zorder=3)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=13.5, color=INK)
    ax.invert_yaxis()
    ax.grid(axis="x", color=GRID, linewidth=0.9, zorder=1)
    ax.set_axisbelow(True)
    span = max(values) if max(values) else 1
    for i, v in enumerate(values):
        ax.text(v + span * 0.025, i, fmt(v), va="center", fontsize=14,
                color=INK, fontweight="semibold")
    ax.set_xlim(0, span * 1.22)
    ax.set_xticks([])
    frame(ax, xlabel=xlabel)
    ax.set_title(title, fontsize=15, color=INK, loc="left", pad=14,
                 fontweight="semibold")
    fig.tight_layout()
    fig.savefig(OUT / path, facecolor=BG)
    plt.close(fig)
    print(f"  {path}")


def main() -> None:
    f = json.loads((OUT / "figures.json").read_text())
    df = pd.read_csv(OUT / "nt_components.csv", parse_dates=["date"])

    print("Poster figures:")

    # 1. The long series, wide, for the poster's hero panel.
    parts = list(LABELS)
    smooth = df.set_index("date")[parts].rolling(4, min_periods=4).mean().dropna()
    fig, ax = plt.subplots(figsize=(14.0, 4.1), dpi=300)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    for p in parts:
        ax.plot(smooth.index, smooth[p], color=COLOURS[p], linewidth=2.6, zorder=3)
        ax.annotate(LABELS[p], xy=(smooth.index[-1], smooth[p].iloc[-1]),
                    xytext=(11, 0), textcoords="offset points", va="center",
                    fontsize=16, color=INK, zorder=4)
    ax.axhline(0, color=INK2, linewidth=1.8, zorder=2)
    ax.grid(axis="y", color=GRID, linewidth=1.0, zorder=1)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#c9c8c4")
    ax.set_ylabel("Persons per quarter", fontsize=15, color=INK2)
    ax.tick_params(colors=INK2, labelsize=14)
    fig.subplots_adjust(left=0.065, right=0.805, top=0.97, bottom=0.09)
    fig.savefig(OUT / "poster_components.png", facecolor=BG)
    plt.close(fig)
    print("  poster_components.png")

    # 2. Reliance on overseas migration: one measure, one hue.
    dep = f["overseas_dependency"]
    hbars("poster_dependency.png",
          ["Last 10 years", "Last 5 years", "Last 12 months"],
          [dep["10y"], dep["5y"], dep["1y"]],
          [OVERSEAS] * 3,
          lambda v: f"{v}%",
          "Share of growth from overseas migration",
          "The Territory's reliance is rising")

    # 3. Volatility: three components, so each keeps its own hue.
    vol = sorted(f["volatility"].items(), key=lambda kv: kv[1])
    hbars("poster_volatility.png",
          [LABELS[k] for k, _ in vol],
          [v for _, v in vol],
          [COLOURS[k] for k, _ in vol],
          lambda v: f"{v:.2f}",
          "Volatility of each component",
          "Standard deviation over mean absolute value")

    # 4. Interstate migration by decade: one measure, one hue.
    dec = f["nim_by_decade"]
    hbars("poster_decades.png",
          [f"{d}s" for d in dec],
          [v["positive_pct"] for v in dec.values()],
          [INTERSTATE] * len(dec),
          lambda v: f"{v:.0f}%",
          "Quarters with net interstate gain",
          "Share of quarters in each decade")


if __name__ == "__main__":
    main()
