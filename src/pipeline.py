"""
NT Population Equation - analysis pipeline
CDU IT Code Fair 2026 | Research (RES003) and Poster (POS006)

Decomposes Northern Territory population change into its three components,
validates them against the published change, and measures how volatile each
component is.

Inputs (both committed, both from the same ABS release)
-------------------------------------------------------
data/raw/310102.xlsx   Components of population change, states and territories
data/raw/310104.xlsx   Estimated resident population, states and territories

See data/raw/SOURCE.md for the release, the attribution and how to update.

Outputs
-------
outputs/nt_components.csv    tidy quarterly series for the NT
outputs/figures.json         every headline figure used in the talk and poster
outputs/components.png       titled chart, 300 dpi
outputs/components.svg       same chart as vector, for print
outputs/components_slide.*   the chart without its title, for a deck or poster
                             that supplies its own heading
outputs/dashboard_data.json  payload for the web dashboard

Run
---
    pip install -r requirements.txt
    python src/pipeline.py

The ABS revises these tables every quarter. Re-running this script against a
newer download reproduces every number in the project. That is the point: the
analysis is a pipeline, not a one-off report.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "outputs"

COMPONENTS_FILE = RAW / "310102.xlsx"
ERP_FILE = RAW / "310104.xlsx"

STATE = "northern territory"

# Column header fragments ABS uses, in table 310102.
SERIES = {
    "natural_increase": ["natural increase"],
    "net_overseas_migration": ["net overseas migration"],
    "net_interstate_migration": ["net interstate migration"],
    "published_change": ["change over previous quarter"],
}

# In 310104 the NT population appears for Male, Female and Persons.
ERP_SERIES = ["estimated resident population", "persons"]

PARTS = ["natural_increase", "net_overseas_migration", "net_interstate_migration"]

# Validated for colour-vision deficiency against a light background.
COLOURS = {
    "natural_increase": "#2a78d6",          # blue
    "net_overseas_migration": "#eb6834",    # orange
    "net_interstate_migration": "#1baf7a",  # aqua
}

LABELS = {
    "natural_increase": "Natural increase",
    "net_overseas_migration": "Net overseas migration",
    "net_interstate_migration": "Net interstate migration",
}


# ---------------------------------------------------------------------------
# Reading the workbooks
#
# ABS changes these layouts between releases. Rather than hard-code column
# positions that will break next quarter, we find the header row and match
# columns by their header text, and say loudly if a series is missing.
# ---------------------------------------------------------------------------

def _norm(value) -> str:
    return re.sub(r"\s+", " ", str(value).replace(";", " ")).strip().lower()


def _header_row(raw: pd.DataFrame, needle: str) -> int | None:
    for i in range(min(25, len(raw))):
        if any(needle in _norm(c) for c in raw.iloc[i].tolist()):
            return i
    return None


def _read_series(path: Path, wanted: dict[str, list[str]]) -> pd.DataFrame:
    """Pull the Northern Territory columns matching each set of fragments."""
    if not path.exists():
        sys.exit(
            f"Missing {path}\n\n"
            "This file is committed to the repository, so it should be here.\n"
            "If it was deleted, restore it with `git checkout -- data/raw`,\n"
            "or see data/raw/SOURCE.md to download the release again."
        )

    book = pd.ExcelFile(path)
    sheets = [s for s in book.sheet_names if s.lower().startswith("data")]
    print(f"{path.name}: sheets {book.sheet_names}, reading {sheets}")

    first_needle = next(iter(wanted.values()))[0]

    for sheet in sheets:
        raw = book.parse(sheet, header=None)
        hrow = _header_row(raw, first_needle)
        if hrow is None:
            continue

        headers = [_norm(c) for c in raw.iloc[hrow].tolist()]
        picked: dict[str, int] = {}
        for key, fragments in wanted.items():
            for col, head in enumerate(headers):
                if STATE in head and all(f in head for f in fragments):
                    picked[key] = col
                    break

        missing = set(wanted) - set(picked)
        if missing:
            print(f"  {sheet}: missing {sorted(missing)}")
            continue

        body = raw.iloc[hrow + 1:]
        dates = pd.to_datetime(body.iloc[:, 0], errors="coerce")
        body = body[dates.notna()]

        frame = pd.DataFrame({"date": pd.to_datetime(body.iloc[:, 0])})
        for key, col in picked.items():
            frame[key] = pd.to_numeric(body.iloc[:, col], errors="coerce")

        frame = frame.sort_values("date").reset_index(drop=True)
        print(f"  {sheet}: matched {sorted(picked)}, {len(frame)} quarters")
        return frame

    sys.exit(
        f"Could not find the Northern Territory series in {path.name}.\n"
        "Open the file, check the sheet name and column headings, and update "
        "SERIES / ERP_SERIES above."
    )


def load() -> pd.DataFrame:
    comp = _read_series(COMPONENTS_FILE, SERIES)
    erp = _read_series(ERP_FILE, {"erp": ERP_SERIES})
    df = comp.merge(erp, on="date", how="left")
    return df.dropna(subset=PARTS).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def compute(df: pd.DataFrame) -> dict:
    latest = df.tail(4)                               # most recent four quarters
    year = {p: float(latest[p].sum()) for p in PARTS}
    total = sum(year.values())

    # Validation: our three components should equal the change ABS publishes.
    published = float(latest["published_change"].sum())
    gap = total - published
    reconciles = abs(gap) < max(5.0, abs(published) * 0.005)

    # Volatility. Coefficient of variation against the mean ABSOLUTE value:
    # interstate migration is mostly negative, so a signed mean would make the
    # measure meaningless. We are asking how much each component moves
    # relative to its own typical size, not which way it points.
    volatility = {}
    for p in PARTS:
        s = df[p]
        mean_abs = float(s.abs().mean())
        volatility[p] = float(s.std() / mean_abs) if mean_abs else float("nan")

    # Robustness: the ABS changed how net overseas migration is measured from
    # the September quarter of 2006, moving from a continuous 12-month rule to
    # the 12-of-16-months rule. Levels either side of that date are not
    # comparable, which would be a fatal objection if our finding depended on
    # comparing them. It does not, but asserting that is not enough: recompute
    # the volatility ranking on the post-2006 window alone and record whether
    # it survives.
    BREAK = pd.Timestamp("2006-09-01")

    def _volatility(frame: pd.DataFrame) -> dict:
        out = {}
        for p in PARTS:
            s = frame[p]
            ma = float(s.abs().mean())
            out[p] = float(s.std() / ma) if ma else float("nan")
        return out

    post = df[df["date"] >= BREAK]
    vol_post = _volatility(post)
    rank_full = sorted(volatility, key=volatility.get, reverse=True)
    rank_post = sorted(vol_post, key=vol_post.get, reverse=True)

    nim = df["net_interstate_migration"]

    # Is the Territory's reliance on overseas migration changing? Compare the
    # share over the last 1, 5 and 10 years.
    dependency = {}
    for years, label in ((1, "1y"), (5, "5y"), (10, "10y")):
        window = df.tail(years * 4)
        sums = {p: float(window[p].sum()) for p in PARTS}
        grand = sum(sums.values())
        dependency[label] = round(sums["net_overseas_migration"] / grand * 100, 1) if grand else None

    # Has the interstate deficit always been there, or is it recent?
    by_decade = {}
    for decade, group in df.groupby(df["date"].dt.year // 10 * 10):
        by_decade[int(decade)] = {
            "quarters": int(len(group)),
            "positive_pct": round(float((group["net_interstate_migration"] > 0).mean() * 100)),
            "mean_per_quarter": round(float(group["net_interstate_migration"].mean())),
        }

    # Everything that added people over the year, before anything left. Only
    # the positive components count: a negative one is an outflow, not a
    # smaller inflow.
    inflows = sum(v for v in (year["natural_increase"],
                              year["net_overseas_migration"],
                              year["net_interstate_migration"]) if v > 0)

    positive = df[nim > 0]["date"]
    last_positive = positive.max() if len(positive) else None
    run = int((df["date"] > last_positive).sum()) if last_positive is not None else None

    erp_now = df["erp"].dropna()
    erp_latest = float(erp_now.iloc[-1]) if len(erp_now) else float("nan")
    erp_year_ago = float(erp_now.iloc[-5]) if len(erp_now) > 5 else float("nan")
    growth_pct = ((erp_latest - erp_year_ago) / erp_year_ago * 100
                  if erp_year_ago == erp_year_ago and erp_year_ago else float("nan"))

    return {
        "reference_period": df["date"].iloc[-1].strftime("%B %Y"),
        "series_start": df["date"].iloc[0].strftime("%B %Y"),
        "quarters_in_series": int(len(df)),

        "natural_increase_12m": round(year["natural_increase"]),
        "net_interstate_migration_12m": round(year["net_interstate_migration"]),
        "net_overseas_migration_12m": round(year["net_overseas_migration"]),
        "total_growth_12m": round(total),
        "nom_share_of_growth_pct": round(year["net_overseas_migration"] / total * 100, 1)
        if total else None,

        # The same reliance measured a second way. Share of growth divides by a
        # net figure that interstate migration has already reduced, which is
        # what makes it reach 90%. Share of inflows divides by everything that
        # came in before any of it left. Both are true; publishing only the
        # larger one invites the obvious objection, so the page carries both.
        "inflows_12m": round(inflows),
        "nom_share_of_inflows_pct": round(
            year["net_overseas_migration"] / inflows * 100, 1) if inflows else None,

        "erp_latest": round(erp_latest) if erp_latest == erp_latest else None,
        "annual_growth_pct": round(growth_pct, 2) if growth_pct == growth_pct else None,

        "quarters_nim_positive": int((nim > 0).sum()),
        "quarters_nim_negative": int((nim < 0).sum()),
        "quarters_nim_positive_pct": round(float((nim > 0).mean() * 100), 1),
        "nim_last_positive": last_positive.strftime("%B %Y") if last_positive is not None else None,
        "nim_consecutive_negative": run,
        "nim_by_decade": by_decade,
        "overseas_dependency": dependency,

        "volatility": {k: round(v, 3) for k, v in volatility.items()},
        "most_volatile": max(volatility, key=volatility.get),

        "robustness_post_2006": {
            "note": "ABS moved net overseas migration to the 12-of-16-months "
                    "rule from the September quarter of 2006. Levels either "
                    "side of that date are not comparable.",
            "quarters": int(len(post)),
            "window_start": post["date"].iloc[0].strftime("%B %Y") if len(post) else None,
            "volatility": {k: round(v, 3) for k, v in vol_post.items()},
            "ranking_full_series": rank_full,
            "ranking_post_2006": rank_post,
            "ranking_unchanged": rank_full == rank_post,
            "nom_mean_abs_pre": round(float(df[df["date"] < BREAK]["net_overseas_migration"].abs().mean()), 1),
            "nom_mean_abs_post": round(float(post["net_overseas_migration"].abs().mean()), 1),
        },

        "reconciliation": {
            "components_sum": round(total),
            "abs_published_change": round(published),
            "difference": round(gap, 1),
            "passes": bool(reconciles),
        },
    }


def report_failure(f: dict) -> None:
    """What a failed run prints instead of the full report.

    A failed reconciliation means the inputs disagree with each other, so every
    figure derived from them is suspect. Printing the usual report would put a
    share, a volatility ranking and a dependency percentage on the screen that
    nobody should quote. This prints only what is needed to find the fault: the
    three components, their sum, and the change the ABS published for the same
    period.
    """
    r = f["reconciliation"]
    print("\n" + "=" * 70)
    print("NT POPULATION EQUATION - RECONCILIATION FAILED")
    print("=" * 70)
    print(f"Series     : {f['series_start']} to {f['reference_period']} "
          f"({f['quarters_in_series']} quarters)")

    print("\nLatest 12 months, as read from the workbooks")
    print(f"  A  Natural increase          {f['natural_increase_12m']:>8,}")
    print(f"  B  Net interstate migration  {f['net_interstate_migration_12m']:>8,}")
    print(f"  C  Net overseas migration    {f['net_overseas_migration_12m']:>8,}")
    print("     " + "-" * 34)
    print(f"  D  Components sum            {r['components_sum']:>8,}")
    print(f"  E  ABS published change      {r['abs_published_change']:>8,}")
    print(f"  F  Difference                {r['difference']:>8}")

    print("\nNo share, no volatility ranking and no dependency figure are")
    print("printed. They would all be derived from inputs that disagree with")
    print("each other, and a number on a screen gets quoted.")
    print("=" * 70)


def report(f: dict) -> None:
    print("\n" + "=" * 70)
    print("NT POPULATION EQUATION")
    print("=" * 70)
    print(f"Series     : {f['series_start']} to {f['reference_period']} "
          f"({f['quarters_in_series']} quarters)")
    print(f"Population : {f['erp_latest']:,}   "
          f"({f['annual_growth_pct']}% over the year)")

    print("\nLatest 12 months")
    print(f"  A  Natural increase          {f['natural_increase_12m']:>8,}")
    print(f"  B  Net interstate migration  {f['net_interstate_migration_12m']:>8,}")
    print(f"  C  Net overseas migration    {f['net_overseas_migration_12m']:>8,}")
    print("     " + "-" * 34)
    print(f"  D  Total growth              {f['total_growth_12m']:>8,}")
    print(f"\n  E  Overseas share of growth  {f['nom_share_of_growth_pct']}%")
    print(f"  F  Share of inflows          {f['nom_share_of_inflows_pct']}%"
          f"   ({f['net_overseas_migration_12m']:,} of {f['inflows_12m']:,} in)")

    r = f["reconciliation"]
    print(f"\nReconciliation [{'PASS' if r['passes'] else 'FAIL'}]")
    print(f"  components sum      {r['components_sum']:>8,}")
    print(f"  ABS published change {r['abs_published_change']:>7,}")
    print(f"  difference          {r['difference']:>8}")
    if not r["passes"]:
        print("  Components do NOT match the published change.")
        print("  Remove the 'this is arithmetic' claim from the script.")

    print(f"\n  H  Interstate migration positive in {f['quarters_nim_positive']} "
          f"of {f['quarters_in_series']} quarters "
          f"({f['quarters_nim_positive_pct']}%)")
    print(f"     last positive {f['nim_last_positive']}, "
          f"negative for {f['nim_consecutive_negative']} quarters since")
    print("     share of quarters positive, by decade:")
    for dec, v in f["nim_by_decade"].items():
        print(f"       {dec}s  {v['positive_pct']:>3}%   mean {v['mean_per_quarter']:>5}/quarter")

    print("\nReliance on overseas migration")
    for label in ("10y", "5y", "1y"):
        print(f"  last {label:<4} {f['overseas_dependency'][label]:>5}% of growth")

    print("\nVolatility (std / mean absolute)")
    for k, v in sorted(f["volatility"].items(), key=lambda kv: -kv[1]):
        print(f"  {LABELS[k]:<28} {v:.3f}")
    rb = f["robustness_post_2006"]
    print(f"\nRobustness, post-2006 window only "
          f"({rb['quarters']} quarters from {rb['window_start']})")
    print("  ABS changed the overseas migration rule from Sept 2006.")
    for k, v in sorted(rb["volatility"].items(), key=lambda kv: -kv[1]):
        print(f"  {LABELS[k]:<28} {v:.3f}")
    print(f"  Mean absolute overseas migration "
          f"{rb['nom_mean_abs_pre']:,}/quarter before, "
          f"{rb['nom_mean_abs_post']:,}/quarter after")
    if rb["ranking_unchanged"]:
        print("  Volatility ranking UNCHANGED by the break. The finding holds.")
    else:
        print("  WARNING: ranking CHANGES on the post-2006 window.")
        print("  The 45-year claim cannot be made. Restrict the series.")

    print(f"\nMost volatile: {LABELS[f['most_volatile']]}")
    if f["most_volatile"] == "net_interstate_migration":
        print("  Growth rests on the two migration components, and the one")
        print("  that swings hardest is the one already running negative.")
        print("  That is the finding.")
    else:
        print("  NOTE: interstate migration is no longer the most volatile")
        print("  component. The presentation argues that it is. Check the")
        print("  release and rewrite the close before presenting.")
    print("=" * 70 + "\n")


# ---------------------------------------------------------------------------
# Chart
# ---------------------------------------------------------------------------

def chart(df: pd.DataFrame, f: dict, *, bare: bool = False,
          size: tuple[float, float] = (11, 6), stem: str = "components") -> None:
    """Draw the three components.

    bare=True omits the title and the source note, for a slide or poster that
    supplies its own heading. That is the variant to drop into Canva.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    smooth = df.set_index("date")[PARTS].rolling(4, min_periods=4).mean().dropna()

    fig, ax = plt.subplots(figsize=size, dpi=300)
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")

    for p in PARTS:
        ax.plot(smooth.index, smooth[p], color=COLOURS[p], linewidth=2, zorder=3)
        ax.annotate(
            LABELS[p],
            xy=(smooth.index[-1], smooth[p].iloc[-1]),
            xytext=(8, 0), textcoords="offset points",
            va="center", fontsize=10, color="#3f3f3f", zorder=4,
        )

    # Zero is the whole story: one series lives below it.
    ax.axhline(0, color="#3f3f3f", linewidth=1.4, zorder=2)
    ax.grid(axis="y", color="#e4e3e0", linewidth=0.8, zorder=1)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#c9c8c4")

    ax.set_ylabel("Persons per quarter", fontsize=11, color="#52514e")
    ax.tick_params(colors="#52514e", labelsize=10)

    if not bare:
        ax.set_title("Northern Territory population change by component",
                     fontsize=15, color="#0b0b0b", pad=16, loc="left")
        ax.text(
            0, -0.17,
            f"Four-quarter rolling average, {f['series_start']} to "
            f"{f['reference_period']}.\n"
            "Source: ABS, National, state and territory population, table 310102.",
            transform=ax.transAxes, fontsize=8.5, color="#6f6e6a", va="top",
        )
        fig.subplots_adjust(left=0.08, right=0.79, top=0.90, bottom=0.21)
    else:
        fig.subplots_adjust(left=0.07, right=0.80, top=0.97, bottom=0.10)

    fig.savefig(OUT / f"{stem}.png", facecolor=fig.get_facecolor())
    fig.savefig(OUT / f"{stem}.svg", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Chart -> {OUT / (stem + '.png')} and .svg")


# ---------------------------------------------------------------------------

def main() -> None:
    OUT.mkdir(exist_ok=True)

    df = load()
    df.to_csv(OUT / "nt_components.csv", index=False)

    figures = compute(df)

    # The validation gate. Nothing downstream is written unless the three
    # components reconcile against the change the ABS publishes for the same
    # period. A department that re-runs this after a revised release should get
    # a refusal, not a plausible-looking number nobody checked.
    #
    # The gate comes before the report on purpose. A failed run prints the
    # three components and the difference, and stops there: the headline
    # figures are never put on the screen at all.
    if not figures["reconciliation"]["passes"]:
        if "--allow-mismatch" not in sys.argv:
            report_failure(figures)
            sys.exit(
                "\nSTOPPED: components do not reconcile against the published "
                "change.\nNo figures, charts or dashboard data were written.\n"
                "Check that 310102 and 310104 come from the same ABS release, "
                "then re-run.\nTo write the outputs anyway, re-run with "
                "--allow-mismatch.\n"
            )
        print("\n--allow-mismatch: writing outputs despite a failed "
              "reconciliation.\nEvery figure below is unverified.\n")

    report(figures)

    (OUT / "figures.json").write_text(json.dumps(figures, indent=2))

    smooth = df.set_index("date")[PARTS].rolling(4, min_periods=4).mean().dropna()
    (OUT / "dashboard_data.json").write_text(json.dumps({
        "figures": figures,
        "series": {
            "dates": [d.strftime("%Y-%m") for d in smooth.index],
            **{k: [round(v, 1) for v in smooth[k]] for k in PARTS},
        },
    }))

    chart(df, figures)
    chart(df, figures, bare=True, size=(12.15, 5.0), stem="components_slide")
    print(f"All outputs in {OUT}")


if __name__ == "__main__":
    main()
