"""
Darwin house prices against Northern Territory wages
CDU IT Code Fair 2026 | supporting analysis, not part of the presentation

Why this exists
---------------
The presentation argues that Territory population growth rests on its two
migration components, and that the interstate component is the least stable of
the three. It does not argue why people leave. Taylor and Dyrting (2025) found
that residential property prices are the strongest macroeconomic predictor of
Northern Territory net interstate migration, and the presentation cites them
for that.

This script measures the price and wage series ourselves, so the claim is in
the repository rather than only in a citation. One correlation between two
series does not establish causation and nothing here attempts to. It is a
descriptive comparison, held in reserve for a question, deliberately kept out
of the slide and the script.

Inputs (both committed)
-----------------------
data/raw/643202.xlsx    Median price of established house transfers, Darwin
data/raw/634502b.xlsx   Wage price index, Northern Territory

See data/raw/SOURCE.md for releases and attribution.

Outputs
-------
outputs/housing_figures.json   headline figures
outputs/housing_wages.csv      the aligned quarterly series
outputs/housing_gap.png/.svg   indexed comparison chart

Run
---
    python src/housing.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "outputs"

PRICE_FILE = RAW / "643202.xlsx"
WAGE_FILE = RAW / "634502b.xlsx"

# Matched on header text, not column position, so an ABS layout change fails
# loudly rather than silently returning the wrong jurisdiction.
PRICE_COL = ["median price of established house transfers", "darwin"]
WAGE_COL = ["quarterly index", "northern territory", "all industries"]
WAGE_YOY_COL = ["percentage change from corresponding quarter of previous year",
                "northern territory", "all industries"]

HEADER_ROW = 0
SERIES_ID_ROW = 9
FIRST_DATA_ROW = 10

PRICE = "#eb6834"
WAGE = "#2a78d6"
BG, INK, INK2, INK3, GRID = "#fcfcfb", "#16181c", "#52514e", "#6f6e6a", "#e4e3e0"


def _column(book: pd.DataFrame, fragments: list[str], path: Path) -> int:
    """Find the one column whose header contains every fragment."""
    # Built as plain strings: a NaN in the header row survives .astype(str)
    # as a float under the newer pandas string dtype.
    header = [str(v).lower() for v in book.iloc[HEADER_ROW]]
    hits = [i for i, text in enumerate(header)
            if all(f in text for f in fragments)]
    if len(hits) != 1:
        sys.exit(
            f"\nExpected exactly one column in {path.name} matching\n"
            f"  {fragments}\nbut found {len(hits)}.\n\n"
            "The ABS has changed this workbook's layout. Open it, find the "
            "column that holds this series, and update the fragments at the "
            "top of src/housing.py."
        )
    return hits[0]


def _series(path: Path, fragments: list[str], name: str) -> tuple[pd.Series, str]:
    if not path.exists():
        sys.exit(
            f"Missing {path}\n\n"
            "This file is committed to the repository, so it should be here.\n"
            "If it was deleted, restore it with `git checkout -- data/raw`,\n"
            "or see data/raw/SOURCE.md to download the release again."
        )

    book = pd.read_excel(path, sheet_name="Data1", header=None)
    col = _column(book, fragments, path)
    series_id = str(book.iloc[SERIES_ID_ROW, col])

    body = book.iloc[FIRST_DATA_ROW:, [0, col]].copy()
    body.columns = ["date", name]
    body["date"] = pd.to_datetime(body["date"], errors="coerce")
    body[name] = pd.to_numeric(body[name], errors="coerce")
    body = body.dropna().reset_index(drop=True)

    print(f"  {path.name}: {name} from column {col}, "
          f"series {series_id}, {len(body)} quarters "
          f"({body['date'].iloc[0]:%b %Y} to {body['date'].iloc[-1]:%b %Y})")
    return body.set_index("date")[name], series_id


def load() -> tuple[pd.DataFrame, dict]:
    print("Reading:")
    price, price_id = _series(PRICE_FILE, PRICE_COL, "median_house_price_000")
    wage, wage_id = _series(WAGE_FILE, WAGE_COL, "wage_price_index")
    wage_yoy, _ = _series(WAGE_FILE, WAGE_YOY_COL, "abs_wpi_yoy_pct")

    df = pd.concat([price, wage, wage_yoy], axis=1, join="inner").dropna(
        subset=["median_house_price_000", "wage_price_index"])
    df.index.name = "date"
    print(f"\n  Common window: {len(df)} quarters, "
          f"{df.index[0]:%b %Y} to {df.index[-1]:%b %Y}")
    return df.reset_index(), {"price_series_id": price_id, "wage_series_id": wage_id}


def compute(df: pd.DataFrame, ids: dict) -> dict:
    base_price = float(df["median_house_price_000"].iloc[0])
    base_wage = float(df["wage_price_index"].iloc[0])
    last_price = float(df["median_house_price_000"].iloc[-1])
    last_wage = float(df["wage_price_index"].iloc[-1])

    price_growth = (last_price / base_price - 1) * 100
    wage_growth = (last_wage / base_wage - 1) * 100

    # Both rebased to 100 at the first common quarter, so the divergence is
    # visible without either series' units mattering.
    df["price_index"] = df["median_house_price_000"] / base_price * 100
    df["wage_index"] = df["wage_price_index"] / base_wage * 100
    df["price_to_wage"] = df["price_index"] / df["wage_index"] * 100

    # Validation. We recompute the year-on-year wage change from the index and
    # compare it against the figure the ABS publishes in its own column of the
    # same workbook. The two are produced differently, so agreement is evidence
    # that the right column, jurisdiction and period were read. Same principle
    # as the reconciliation in pipeline.py.
    ours = df["wage_price_index"].pct_change(4) * 100
    theirs = df["abs_wpi_yoy_pct"]
    both = pd.concat([ours, theirs], axis=1).dropna()
    worst = float((both.iloc[:, 0] - both.iloc[:, 1]).abs().max())
    checks = int(len(both))
    passes = worst < 0.15          # ABS publishes this column to one decimal

    years = (df["date"].iloc[-1] - df["date"].iloc[0]).days / 365.25

    return {
        "window_start": df["date"].iloc[0].strftime("%B %Y"),
        "window_end": df["date"].iloc[-1].strftime("%B %Y"),
        "quarters": int(len(df)),
        "years": round(years, 1),

        "darwin_median_house_price_start": round(base_price * 1000),
        "darwin_median_house_price_end": round(last_price * 1000),
        "darwin_price_growth_pct": round(price_growth, 1),

        "nt_wage_index_start": round(base_wage, 1),
        "nt_wage_index_end": round(last_wage, 1),
        "nt_wage_growth_pct": round(wage_growth, 1),

        "gap_percentage_points": round(price_growth - wage_growth, 1),
        "price_to_wage_ratio_end": round(float(df["price_to_wage"].iloc[-1]), 1),
        "price_to_wage_peak": round(float(df["price_to_wage"].max()), 1),
        "price_to_wage_peak_quarter":
            df.loc[df["price_to_wage"].idxmax(), "date"].strftime("%B %Y"),

        "validation": {
            "description": "Year-on-year wage growth recomputed from the index "
                           "and compared against the ABS published column in "
                           "the same workbook.",
            "quarters_checked": checks,
            "largest_difference_pp": round(worst, 3),
            "tolerance_pp": 0.15,
            "passes": bool(passes),
        },

        **ids,
    }


def report(f: dict) -> None:
    print("\n" + "=" * 70)
    print("DARWIN HOUSE PRICES AGAINST NT WAGES")
    print("=" * 70)
    print(f"Window : {f['window_start']} to {f['window_end']} "
          f"({f['quarters']} quarters, {f['years']} years)")

    print(f"\n  Darwin median established house price")
    print(f"    {f['darwin_median_house_price_start']:>9,}  ->  "
          f"{f['darwin_median_house_price_end']:>9,}    "
          f"{f['darwin_price_growth_pct']:+.1f}%")
    print(f"  NT wage price index")
    print(f"    {f['nt_wage_index_start']:>9}  ->  {f['nt_wage_index_end']:>9}    "
          f"{f['nt_wage_growth_pct']:+.1f}%")
    print(f"\n  Gap: {f['gap_percentage_points']:.0f} percentage points")

    v = f["validation"]
    print(f"\nValidation [{'PASS' if v['passes'] else 'FAIL'}]")
    print(f"  recomputed year-on-year wage growth vs the ABS published column")
    print(f"  {v['quarters_checked']} quarters checked, "
          f"largest difference {v['largest_difference_pp']} pp "
          f"(tolerance {v['tolerance_pp']})")

    print(f"\n  Price-to-wage ratio, {f['window_start']} = 100")
    print(f"    now  {f['price_to_wage_ratio_end']}")
    print(f"    peak {f['price_to_wage_peak']} in {f['price_to_wage_peak_quarter']}")
    print("=" * 70)
    print("\nThis is descriptive. It compares two series over the same period.")
    print("It does not establish that house prices cause people to leave.")
    print("Taylor and Dyrting (2025) tested that properly; we cite them.\n")


def chart(df: pd.DataFrame, f: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    ax.plot(df["date"], df["price_index"], color=PRICE, linewidth=2, zorder=3)
    ax.plot(df["date"], df["wage_index"], color=WAGE, linewidth=2, zorder=3)

    for label, col, colour in (("Darwin median house price", "price_index", PRICE),
                               ("NT wages", "wage_index", WAGE)):
        ax.annotate(label, xy=(df["date"].iloc[-1], df[col].iloc[-1]),
                    xytext=(8, 0), textcoords="offset points", va="center",
                    fontsize=10, color=INK2, zorder=4)

    ax.axhline(100, color=INK2, linewidth=1.2, zorder=2)
    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=1)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#c9c8c4")

    ax.set_ylabel(f"Index, {f['window_start']} = 100", fontsize=11, color=INK2)
    ax.tick_params(colors=INK2, labelsize=10)
    ax.set_title("Darwin house prices and Northern Territory wages",
                 fontsize=15, color=INK, pad=16, loc="left")
    ax.text(
        0, -0.17,
        f"Both rebased to 100 at {f['window_start']}. Established house "
        f"transfers, unstratified median.\n"
        "Source: ABS tables 643202 and 634502b.",
        transform=ax.transAxes, fontsize=8.5, color=INK3, va="top",
    )
    fig.subplots_adjust(left=0.08, right=0.78, top=0.90, bottom=0.21)

    fig.savefig(OUT / "housing_gap.png", facecolor=BG)
    fig.savefig(OUT / "housing_gap.svg", facecolor=BG)
    plt.close(fig)
    print(f"Chart -> {OUT / 'housing_gap.png'} and .svg")


def main() -> None:
    OUT.mkdir(exist_ok=True)

    df, ids = load()
    figures = compute(df, ids)
    report(figures)

    if not figures["validation"]["passes"]:
        if "--allow-mismatch" not in sys.argv:
            sys.exit(
                "\nSTOPPED: recomputed wage growth does not match the figure "
                "the ABS publishes.\nNo figures or charts were written.\n"
                "Check that the wage columns are being read correctly, then "
                "re-run.\nTo write the outputs anyway, re-run with "
                "--allow-mismatch.\n"
            )
        print("\n--allow-mismatch: writing outputs despite a failed check.\n")

    (OUT / "housing_figures.json").write_text(json.dumps(figures, indent=2))
    df.to_csv(OUT / "housing_wages.csv", index=False)
    chart(df, figures)
    print(f"All outputs in {OUT}")


if __name__ == "__main__":
    main()
