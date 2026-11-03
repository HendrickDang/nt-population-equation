"""
Who needs services, and where
Supporting analysis for the dashboard

Why this exists
---------------
The rest of the project answers how the Territory grows. A department that has
to plan a school, a clinic or a housing release needs two more answers: which
age groups are growing, and in which areas. Every one of those plans starts
from the same two counts, so this script produces them, checked, from the ABS.

It does not say where to build anything. It gives the counts that such a
decision starts from: how many people are in each age group a service plans
for, how fast each group is changing, and which areas are adding people or
losing them.

Validation
----------
Both gates must pass before anything is written.

1. Age. The 101 single-year age groups (0 to 100 and over) must sum to the
   Northern Territory estimated resident population in table 310104, at every
   June the two tables share. The tables are produced separately by the ABS,
   so exact agreement shows the right columns and jurisdiction were read.

2. Areas. The Territory's Statistical Areas Level 2 (SA2) must sum to the
   Territory total published in the same workbook, in every year from 2001.

The regional release is published on a different timetable from the national
one, and the national release can revise a June figure after the regional one
has gone out. That difference is reported, not hidden: it is a matter of
release timing, not an error, and the area figures are presented as shares and
changes within their own release for that reason.

Inputs (committed)
------------------
data/raw/3101057.xlsx               ERP by single year of age, Northern
                                    Territory (National, state and territory
                                    population, same release as 310104)
data/raw/310104.xlsx                ERP, states and territories
data/raw/32180DS0003_2001-25.xlsx   ERP by SA2 and above, 2001 to 2025
                                    (Regional population, 2024-25)

Output
------
outputs/services_figures.json

Run
---
    python src/services.py
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "outputs"

AGE_FILE = RAW / "3101057.xlsx"
ERP_FILE = RAW / "310104.xlsx"

STATE = "northern territory"
NT_CODE = 7           # ABS state and territory code for the Northern Territory
YEARS_BACK = 5        # the comparison window for "change"

# Age groups, chosen because each is what a service plans around. Only four
# carry a service label; the other two are shown so the groups add up to the
# whole population and nothing is quietly left out.
BANDS = [
    ("0-4",   "Under 5",      0,   4,   "Childcare and early learning"),
    ("5-17",  "5 to 17",      5,   17,  "Schools"),
    ("18-24", "18 to 24",     18,  24,  None),
    ("25-44", "25 to 44",     25,  44,  "Housing and jobs"),
    ("45-64", "45 to 64",     45,  64,  None),
    ("65+",   "65 and over",  65,  200, "Health and aged care"),
]


def _june(year: int) -> pd.Timestamp:
    return pd.Timestamp(f"{year}-06-01")


# --------------------------------------------------------------------------
# Age
# --------------------------------------------------------------------------

def load_age() -> pd.DataFrame:
    """Persons by single year of age, one row per June, columns 0..100."""
    index = pd.read_excel(AGE_FILE, sheet_name="Index", header=None)
    text = " ".join(str(v).lower() for v in index.to_numpy().ravel())
    if STATE not in text:
        sys.exit(f"{AGE_FILE.name}: the Index sheet does not mention the "
                 "Northern Territory. This is not the table this script reads.")

    frames = []
    for sheet in pd.ExcelFile(AGE_FILE).sheet_names:
        if not sheet.startswith("Data"):
            continue
        header = [str(v) for v in pd.read_excel(AGE_FILE, sheet_name=sheet,
                                                header=None, nrows=1).iloc[0]]
        body = pd.read_excel(AGE_FILE, sheet_name=sheet, header=None, skiprows=10)
        body = body.set_index(0)
        cols = {}
        for i, h in enumerate(header):
            parts = [p.strip() for p in h.split(";")]
            if len(parts) >= 3 and parts[1].lower() == "persons":
                cols[int(parts[2].split()[0])] = body[i]
        if cols:
            frames.append(pd.DataFrame(cols))
    if not frames:
        sys.exit(f"{AGE_FILE.name}: no 'Persons' columns found.")

    age = pd.concat(frames, axis=1).sort_index(axis=1)
    age.index = pd.to_datetime(age.index, errors="coerce")
    age = age[age.index.notna()].apply(pd.to_numeric, errors="coerce")

    expected = list(range(0, 101))
    if list(age.columns) != expected:
        missing = sorted(set(expected) - set(age.columns))
        sys.exit(f"{AGE_FILE.name}: expected ages 0 to 100, missing {missing}.")
    return age


def load_erp() -> pd.Series:
    header = [str(v).lower() for v in pd.read_excel(ERP_FILE, sheet_name="Data1",
                                                   header=None, nrows=1).iloc[0]]
    col = [i for i, h in enumerate(header) if "persons" in h and STATE in h]
    if len(col) != 1:
        sys.exit(f"{ERP_FILE.name}: could not find a single Northern Territory "
                 "persons column.")
    body = pd.read_excel(ERP_FILE, sheet_name="Data1", header=None, skiprows=10)
    s = pd.to_numeric(body[col[0]], errors="coerce")
    s.index = pd.to_datetime(body[0], errors="coerce")
    return s[s.index.notna()]


def age_figures(age: pd.DataFrame, erp: pd.Series) -> tuple[dict, dict]:
    common = age.index.intersection(erp.index)
    diff = (age.loc[common].sum(axis=1) - erp.loc[common]).abs()
    check = {
        "junes_compared": int(len(common)),
        "first": common.min().strftime("%B %Y"),
        "last": common.max().strftime("%B %Y"),
        "largest_difference": float(diff.max()),
        "passes": bool(len(common) > 0 and diff.max() < 0.5),
    }

    now = age.index.max()
    then = _june(now.year - YEARS_BACK)
    if then not in age.index:
        sys.exit(f"{AGE_FILE.name}: no June {then.year} to compare against.")

    def band(lo: int, hi: int, when: pd.Timestamp) -> int:
        return int(round(age.loc[when, [a for a in age.columns if lo <= a <= hi]].sum()))

    total_now, total_then = band(0, 200, now), band(0, 200, then)
    bands = []
    for key, label, lo, hi, service in BANDS:
        a, b = band(lo, hi, then), band(lo, hi, now)
        bands.append({
            "key": key, "label": label, "service": service,
            "then": a, "now": b, "change": b - a,
            "pct": round((b / a - 1) * 100, 1),
            "share_now": round(b / total_now * 100, 1),
        })
    if sum(x["now"] for x in bands) != total_now:
        sys.exit("Age bands do not cover the whole population. Check BANDS.")

    def pair(lo, hi):
        a, b = band(lo, hi, then), band(lo, hi, now)
        return {"then": a, "now": b, "pct": round((b / a - 1) * 100, 1)}

    fig = {
        "reference": now.strftime("%B %Y"),
        "base": then.strftime("%B %Y"),
        "years": YEARS_BACK,
        "total_then": total_then,
        "total_now": total_now,
        "total_pct": round((total_now / total_then - 1) * 100, 1),
        "bands": bands,
        "detail": {
            "primary_5_11": pair(5, 11),
            "secondary_12_17": pair(12, 17),
            "aged_85_plus": pair(85, 200),
        },
    }
    return fig, check


# --------------------------------------------------------------------------
# Areas
# --------------------------------------------------------------------------

def _locate(sheet: pd.DataFrame) -> tuple[int, int, dict]:
    """Find the label row, the year row above it, and the year columns."""
    label_row = None
    for r in range(min(15, len(sheet))):
        cells = [str(v).strip().lower() for v in sheet.iloc[r]]
        if "s/t name" in cells or "s/t code" in cells:
            label_row = r
            break
    if label_row is None:
        sys.exit("Regional workbook: could not find the S/T header row.")
    years = {}
    for r in range(label_row - 1, max(-1, label_row - 4), -1):
        for c, v in enumerate(sheet.iloc[r]):
            if isinstance(v, (int, float)) and not pd.isna(v) and 2000 <= v <= 2100:
                years[int(v)] = c
        if years:
            break
    if not years:
        sys.exit("Regional workbook: could not find the year columns.")
    return label_row, max(years), years


def area_figures(path: Path, erp: pd.Series) -> tuple[dict, dict]:
    sa2 = pd.read_excel(path, sheet_name="Table 1", header=None)
    lr, latest, ycol = _locate(sa2)
    labels = [str(v).strip().lower() for v in sa2.iloc[lr]]

    def col(name: str) -> int:
        if name not in labels:
            sys.exit(f"{path.name}: no '{name}' column in Table 1.")
        return labels.index(name)

    st, gcc, sa3, name = col("s/t code"), col("gccsa name"), col("sa3 name"), col("sa2 name")
    body = sa2.iloc[lr + 1:]
    nt = body[pd.to_numeric(body[st], errors="coerce") == NT_CODE].copy()
    if nt.empty:
        sys.exit(f"{path.name}: no Northern Territory rows in Table 1.")

    state = pd.read_excel(path, sheet_name="Table 5", header=None)
    slr, _, scol = _locate(state)
    slabels = [str(v).strip().lower() for v in state.iloc[slr]]
    sbody = state.iloc[slr + 1:]
    nt_total = sbody[pd.to_numeric(sbody[slabels.index("s/t code")],
                                   errors="coerce") == NT_CODE]
    if len(nt_total) != 1:
        sys.exit(f"{path.name}: expected one Northern Territory row in Table 5.")

    # Gate: the SA2s sum to the published Territory total in every year.
    diffs = {}
    for y, c in ycol.items():
        if y in scol:
            s = pd.to_numeric(nt[c], errors="coerce").sum()
            t = float(pd.to_numeric(nt_total.iloc[0, scol[y]], errors="coerce"))
            diffs[y] = abs(s - t)
    check = {
        "years_compared": len(diffs),
        "first": min(diffs), "last": max(diffs),
        "largest_difference": float(max(diffs.values())),
        "passes": bool(diffs and max(diffs.values()) < 0.5),
        "sa2_count": int(len(nt)),
    }

    base = latest - YEARS_BACK
    for c in (ycol[base], ycol[latest - 1], ycol[latest]):
        nt[c] = pd.to_numeric(nt[c], errors="coerce").astype(float)
    a, p, b = ycol[base], ycol[latest - 1], ycol[latest]
    nt["d5"] = nt[b] - nt[a]
    nt["d1"] = nt[b] - nt[p]

    def row(r) -> dict:
        return {
            "name": str(r[name]), "region": str(r[sa3]),
            "then": int(r[a]), "now": int(r[b]),
            "change": int(r["d5"]),
            "pct": round(r["d5"] / r[a] * 100, 1) if r[a] > 0 else None,
            "change_1y": int(r["d1"]),
            "pct_1y": round(r["d1"] / r[p] * 100, 1) if r[p] > 0 else None,
        }

    growth = float(nt["d5"].sum())
    darwin = float(nt.loc[nt[gcc].astype(str).str.contains("Darwin"), "d5"].sum())
    nt["r1"] = nt["d1"] / nt[p].where(nt[p] > 0)
    big = nt[nt[p] >= 1000]                       # rates on tiny areas mislead
    total_latest = int(nt[b].sum())
    national = erp.get(_june(latest))

    fig = {
        "release": "Regional population, 2024-25",
        "reference": f"June {latest}",
        "base": f"June {base}",
        "years": YEARS_BACK,
        "nt_total": total_latest,
        "growth": int(growth),
        "greater_darwin_share_pct": round(darwin / growth * 100, 0) if growth else None,
        "top": [row(r) for _, r in nt.sort_values("d5", ascending=False).head(6).iterrows()],
        "fastest_1y": row(big.sort_values("r1", ascending=False).iloc[0]),
        "falling": [row(r) for _, r in nt[nt["d5"] < 0].sort_values("d5").head(3).iterrows()],
        "national_release_same_june": int(national) if national == national and national is not None else None,
    }
    if fig["national_release_same_june"] is not None:
        fig["vintage_difference"] = fig["national_release_same_june"] - total_latest
    return fig, check


# --------------------------------------------------------------------------

def report(age: dict, ac: dict, area: dict, rc: dict) -> None:
    print("\n" + "=" * 70)
    print("WHO NEEDS SERVICES, AND WHERE")
    print("=" * 70)
    print(f"\nAge check [{'PASS' if ac['passes'] else 'FAIL'}]  "
          f"{ac['junes_compared']} Junes, {ac['first']} to {ac['last']}, "
          f"largest difference {ac['largest_difference']:.0f}")
    print(f"Area check [{'PASS' if rc['passes'] else 'FAIL'}]  "
          f"{rc['sa2_count']} SA2s, {rc['first']} to {rc['last']}, "
          f"largest difference {rc['largest_difference']:.0f}")
    if not (ac["passes"] and rc["passes"]):
        return

    print(f"\nAge, {age['base']} to {age['reference']} "
          f"(whole Territory {age['total_pct']:+.1f}%)")
    for b in age["bands"]:
        tag = f"  {b['service']}" if b["service"] else ""
        print(f"  {b['label']:<12}{b['now']:>8,}  {b['change']:>+7,}  {b['pct']:>+6.1f}%{tag}")
    d = age["detail"]
    print(f"  primary 5-11 {d['primary_5_11']['pct']:+.1f}%, "
          f"secondary 12-17 {d['secondary_12_17']['pct']:+.1f}%, "
          f"85 and over {d['aged_85_plus']['pct']:+.1f}%")

    print(f"\nAreas, {area['base']} to {area['reference']} "
          f"({area['release']}); Greater Darwin took "
          f"{area['greater_darwin_share_pct']:.0f}% of {area['growth']:,}")
    for r in area["top"]:
        print(f"  {r['name']:<24}{r['change']:>+7,}  {r['pct']:>+6.1f}%")
    f = area["fastest_1y"]
    print(f"  fastest last year: {f['name']} {f['pct_1y']:+.1f}%")
    print("  falling: " + ", ".join(f"{r['name']} {r['change']:+,}" for r in area["falling"]))
    if area.get("vintage_difference") is not None:
        print(f"\n  This regional release puts the Territory at {area['nt_total']:,} at "
              f"{area['reference']}; the later national release says "
              f"{area['national_release_same_june']:,} "
              f"({area['vintage_difference']:+,}). Release timing, not an error.")
    print("=" * 70)


def main() -> None:
    regional = sorted(glob.glob(str(RAW / "32180DS0003_*.xlsx")))
    if not regional:
        sys.exit("No regional population workbook (32180DS0003_*.xlsx) in data/raw.")
    erp = load_erp()
    age, ac = age_figures(load_age(), erp)
    area, rc = area_figures(Path(regional[-1]), erp)
    report(age, ac, area, rc)

    if not (ac["passes"] and rc["passes"]):
        sys.exit("\nSTOPPED: a check failed. services_figures.json was not written.\n")

    OUT.mkdir(exist_ok=True)
    (OUT / "services_figures.json").write_text(json.dumps({
        "age": age, "areas": area,
        "validation": {"age": ac, "areas": rc},
    }, indent=2))
    print(f"Written {OUT / 'services_figures.json'}")


if __name__ == "__main__":
    main()
