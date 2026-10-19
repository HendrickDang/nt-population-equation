"""
Interstate migration: arrivals and departures, not just the net
CDU IT Code Fair 2026 | supporting analysis

Why this exists
---------------
Table 310102 reports net interstate migration: one number per quarter, the
balance of two much larger flows. A net loss of 1,589 people tells a planner
that the Territory shrank on that measure. It does not tell them whether fewer
people arrived, more people left, or both, and those three situations call for
different responses.

This script separates the flows. It also puts the net figure in proportion:
the Territory exchanges roughly one in nine of its residents with other states
every year, so the published net number is the small residue of a very large
two-way movement.

Validation
----------
Arrivals minus departures must equal the net interstate migration already in
table 310102, in every quarter. The three tables are produced separately by
the ABS, so agreement is evidence that the right columns and jurisdiction were
read. The check covers the full series and is a gate: nothing is written if it
fails.

Inputs (all committed, all from the same ABS release)
-----------------------------------------------------
data/raw/3101016A.xlsx   Interstate migration arrivals, states and territories
data/raw/3101016B.xlsx   Interstate migration departures
outputs/nt_components.csv  written by pipeline.py, supplies the published net

Outputs
-------
outputs/interstate_figures.json   headline figures
outputs/interstate_flows.csv      arrivals, departures, net and churn by quarter
outputs/interstate_flows.png/.svg the two flows plotted together

Run
---
    python src/pipeline.py          # must run first
    python src/interstate_flows.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "outputs"

ARRIVALS_FILE = RAW / "3101016A.xlsx"
DEPARTURES_FILE = RAW / "3101016B.xlsx"
COMPONENTS = OUT / "nt_components.csv"

ARRIVALS_COL = ["interstate arrivals", "northern territory"]
DEPARTURES_COL = ["interstate departures", "northern territory"]

HEADER_ROW, SERIES_ID_ROW, FIRST_DATA_ROW = 0, 9, 10

ARRIVE, DEPART = "#1baf7a", "#eb6834"
BG, INK, INK2, INK3, GRID = "#fcfcfb", "#16181c", "#52514e", "#6f6e6a", "#e4e3e0"


def _series(path: Path, fragments: list[str], name: str) -> tuple[pd.Series, str]:
    if not path.exists():
        sys.exit(
            f"Missing {path}\n\n"
            "This file is committed to the repository, so it should be here.\n"
            "If it was deleted, restore it with `git checkout -- data/raw`,\n"
            "or see data/raw/SOURCE.md to download the release again."
        )

    book = pd.read_excel(path, sheet_name="Data1", header=None)
    # Plain strings: a NaN in the header row survives .astype(str) as a float
    # under the newer pandas string dtype.
    header = [str(v).lower() for v in book.iloc[HEADER_ROW]]
    hits = [i for i, text in enumerate(header)
            if all(f in text for f in fragments)]
    if len(hits) != 1:
        sys.exit(
            f"\nExpected exactly one column in {path.name} matching\n"
            f"  {fragments}\nbut found {len(hits)}.\n\n"
            "The ABS has changed this workbook's layout. Open it, find the "
            "Northern Territory column, and update the fragments at the top "
            "of src/interstate_flows.py."
        )
    col = hits[0]
    series_id = str(book.iloc[SERIES_ID_ROW, col])

    body = book.iloc[FIRST_DATA_ROW:, [0, col]].copy()
    body.columns = ["date", name]
    body["date"] = pd.to_datetime(body["date"], errors="coerce")
    body[name] = pd.to_numeric(body[name], errors="coerce")
    body = body.dropna()

    print(f"  {path.name}: {name} from column {col}, series {series_id}, "
          f"{len(body)} quarters")
    return body.set_index("date")[name], series_id


def load() -> tuple[pd.DataFrame, dict]:
    if not COMPONENTS.exists():
        sys.exit(
            f"Missing {COMPONENTS}\n\n"
            "Run `python src/pipeline.py` first. This script validates its "
            "figures against the net interstate migration that pipeline "
            "writes."
        )

    print("Reading:")
    arrivals, arr_id = _series(ARRIVALS_FILE, ARRIVALS_COL, "arrivals")
    departures, dep_id = _series(DEPARTURES_FILE, DEPARTURES_COL, "departures")

    comp = pd.read_csv(COMPONENTS, parse_dates=["date"]).set_index("date")
    published = comp["net_interstate_migration"].rename("net_published")
    erp = comp["erp"].rename("erp")

    df = pd.concat([arrivals, departures, published, erp], axis=1).dropna(
        subset=["arrivals", "departures", "net_published"])
    df["net_computed"] = df["arrivals"] - df["departures"]
    df["churn"] = df["arrivals"] + df["departures"]
    df.index.name = "date"

    print(f"\n  Matched {len(df)} quarters, "
          f"{df.index[0]:%b %Y} to {df.index[-1]:%b %Y}")
    return df.reset_index(), {"arrivals_series_id": arr_id,
                              "departures_series_id": dep_id}


def compute(df: pd.DataFrame, ids: dict) -> dict:
    # Validation: our two gross flows must reproduce the published net.
    gap = (df["net_computed"] - df["net_published"]).abs()
    worst = float(gap.max())
    passes = worst < 0.5                      # both series are whole persons

    year = df.tail(4)
    arrivals = float(year["arrivals"].sum())
    departures = float(year["departures"].sum())
    churn = arrivals + departures
    erp = float(df["erp"].dropna().iloc[-1]) if df["erp"].notna().any() else float("nan")

    # Is the deficit widening because fewer people arrive, or because more
    # leave? Compare the latest year against the preceding decade's average.
    decade = df.iloc[-44:-4]                  # ten years ending a year ago
    arr_avg = float(decade["arrivals"].sum() / 10)
    dep_avg = float(decade["departures"].sum() / 10)

    return {
        "window_start": df["date"].iloc[0].strftime("%B %Y"),
        "window_end": df["date"].iloc[-1].strftime("%B %Y"),
        "quarters": int(len(df)),

        "arrivals_12m": round(arrivals),
        "departures_12m": round(departures),
        "net_12m": round(arrivals - departures),
        "churn_12m": round(churn),
        "churn_share_of_population_pct":
            round(churn / erp * 100, 1) if erp == erp else None,
        "population": round(erp) if erp == erp else None,

        "prior_decade_mean_arrivals": round(arr_avg),
        "prior_decade_mean_departures": round(dep_avg),
        "arrivals_vs_prior_decade_pct": round((arrivals / arr_avg - 1) * 100, 1),
        "departures_vs_prior_decade_pct": round((departures / dep_avg - 1) * 100, 1),

        "validation": {
            "description": "Arrivals minus departures, from tables 16A and 16B, "
                           "against the net interstate migration published in "
                           "table 310102.",
            "quarters_checked": int(len(df)),
            "largest_difference": round(worst, 3),
            "passes": bool(passes),
        },

        **ids,
    }


def report(f: dict) -> None:
    print("\n" + "=" * 70)
    print("NT INTERSTATE MIGRATION: ARRIVALS AND DEPARTURES")
    print("=" * 70)
    print(f"Series : {f['window_start']} to {f['window_end']} "
          f"({f['quarters']} quarters)")

    print(f"\nYear to {f['window_end']}")
    print(f"  arrivals     {f['arrivals_12m']:>8,}")
    print(f"  departures   {f['departures_12m']:>8,}")
    print("  " + "-" * 22)
    print(f"  net          {f['net_12m']:>8,}")
    print(f"\n  gross churn  {f['churn_12m']:>8,}   "
          f"{f['churn_share_of_population_pct']}% of a population of "
          f"{f['population']:,}")

    v = f["validation"]
    print(f"\nValidation [{'PASS' if v['passes'] else 'FAIL'}]")
    print("  arrivals - departures vs the published net interstate migration")
    print(f"  {v['quarters_checked']} quarters checked, "
          f"largest difference {v['largest_difference']:g}")

    print("\nAgainst the prior decade's annual average")
    print(f"  arrivals   {f['prior_decade_mean_arrivals']:>7,}/year  ->  "
          f"{f['arrivals_12m']:>7,}   {f['arrivals_vs_prior_decade_pct']:+.1f}%")
    print(f"  departures {f['prior_decade_mean_departures']:>7,}/year  ->  "
          f"{f['departures_12m']:>7,}   {f['departures_vs_prior_decade_pct']:+.1f}%")

    a, d = f["arrivals_vs_prior_decade_pct"], f["departures_vs_prior_decade_pct"]
    if a < 0 and d < 0:
        print("  Both flows have shrunk: fewer people moving either way.")
    elif a < 0 <= d:
        print("  Fewer arriving, more leaving.")
    elif d < 0 <= a:
        print("  More arriving, fewer leaving.")
    else:
        print("  Both flows have grown.")
    print("=" * 70 + "\n")


def chart(df: pd.DataFrame, f: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    smooth = df.set_index("date")[["arrivals", "departures"]].rolling(
        4, min_periods=4).mean().dropna()

    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    ax.fill_between(smooth.index, smooth["arrivals"], smooth["departures"],
                    where=smooth["departures"] >= smooth["arrivals"],
                    color=DEPART, alpha=0.11, zorder=2)
    ax.fill_between(smooth.index, smooth["arrivals"], smooth["departures"],
                    where=smooth["arrivals"] > smooth["departures"],
                    color=ARRIVE, alpha=0.11, zorder=2)

    for name, colour, label in (("arrivals", ARRIVE, "Arrivals"),
                                ("departures", DEPART, "Departures")):
        ax.plot(smooth.index, smooth[name], color=colour, linewidth=2, zorder=3)
        ax.annotate(label, xy=(smooth.index[-1], smooth[name].iloc[-1]),
                    xytext=(8, 0), textcoords="offset points", va="center",
                    fontsize=10, color=INK2, zorder=4)

    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=1)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#c9c8c4")

    ax.set_ylabel("Persons per quarter", fontsize=11, color=INK2)
    ax.tick_params(colors=INK2, labelsize=10)
    ax.set_title("Northern Territory interstate migration, both directions",
                 fontsize=15, color=INK, pad=16, loc="left")
    ax.text(
        0, -0.17,
        f"Four-quarter rolling average, {f['window_start']} to "
        f"{f['window_end']}. The shaded gap is the net.\n"
        "Source: ABS tables 3101016A and 3101016B.",
        transform=ax.transAxes, fontsize=8.5, color=INK3, va="top",
    )
    fig.subplots_adjust(left=0.08, right=0.84, top=0.90, bottom=0.21)

    fig.savefig(OUT / "interstate_flows.png", facecolor=BG)
    fig.savefig(OUT / "interstate_flows.svg", facecolor=BG)
    plt.close(fig)
    print(f"Chart -> {OUT / 'interstate_flows.png'} and .svg")


def main() -> None:
    OUT.mkdir(exist_ok=True)

    df, ids = load()
    figures = compute(df, ids)
    report(figures)

    if not figures["validation"]["passes"]:
        if "--allow-mismatch" not in sys.argv:
            sys.exit(
                "\nSTOPPED: arrivals minus departures does not match the "
                "published net interstate migration.\nNo figures or charts "
                "were written.\nCheck that all three tables come from the same "
                "ABS release, then re-run.\nTo write the outputs anyway, "
                "re-run with --allow-mismatch.\n"
            )
        print("\n--allow-mismatch: writing outputs despite a failed check.\n")

    (OUT / "interstate_figures.json").write_text(json.dumps(figures, indent=2))
    df.to_csv(OUT / "interstate_flows.csv", index=False)
    chart(df, figures)
    print(f"All outputs in {OUT}")


if __name__ == "__main__":
    main()
