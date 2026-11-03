"""
Check the ABS for a new release and download it if there is one.

What this does
--------------
The ABS publishes National, state and territory population quarterly, always at
the same `latest-release` address, with the workbooks under a dated path such
as `.../mar-2026/310102.xlsx`. This script reads that page, works out which
release is current, and downloads the four workbooks only when the release has
changed since the last run.

It is deliberately cautious. Files are downloaded to a temporary directory and
each one is opened and checked for the Northern Territory column it is supposed
to contain before anything in data/raw is touched. A truncated download, an
error page served as HTML, or a layout change all fail here rather than
reaching the analysis.

Nothing is analysed or published by this script. It only replaces the inputs.
The pipeline's own validation gate still decides whether the new figures are
fit to report, and that gate is what makes an unattended run safe.

Exit codes
----------
0   a new release was downloaded, or no new release was available
1   something went wrong: network, layout change, or a bad file

Run
---
    python src/fetch_abs.py            # download only if the release changed
    python src/fetch_abs.py --force    # download even if it looks unchanged
    python src/fetch_abs.py --check    # report only, download nothing
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
MARKER = RAW / "RELEASE"
REGIONAL_MARKER = RAW / "RELEASE_REGIONAL"

LANDING = ("https://www.abs.gov.au/statistics/people/population/"
           "national-state-and-territory-population/latest-release")
REGIONAL_LANDING = ("https://www.abs.gov.au/statistics/people/population/"
                    "regional-population/latest-release")
BASE = "https://www.abs.gov.au"

# The workbooks this project reads, and the Northern Territory column each one
# must contain. The check is what stops a layout change reaching the analysis.
WANTED = {
    "310102.xlsx": "net overseas migration",
    "310104.xlsx": "estimated resident population",
    "3101016A.xlsx": "interstate arrivals",
    "3101016B.xlsx": "interstate departures",
}

# Population by single year of age, Northern Territory. Same release and same
# folder as the four above, so it is required in the same way. Its columns are
# named by age, not by state, so it gets its own check: see verify_age().
AGE = "3101057.xlsx"

# A browser user agent: the ABS serves a block page to the default urllib one.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

LINK = re.compile(
    r'href="(/statistics/people/population/national-state-and-territory-population'
    r'/([a-z]{3}-\d{4})/([^"/]+\.xlsx))"',
    re.I,
)

# Regional population is a separate annual release with its own page, and the
# workbook name carries its year range (32180DS0003_2001-25.xlsx).
REGIONAL_LINK = re.compile(
    r'href="(/statistics/people/population/regional-population'
    r'/(\d{4}-\d{2})/(32180DS0003_\d{4}-\d{2}\.xlsx))"',
    re.I,
)


def get(url: str, timeout: int = 90) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def discover() -> tuple[str, dict[str, str]]:
    """Return (release label, {filename: absolute url}) from the landing page."""
    try:
        page = get(LANDING).decode("utf-8", "replace")
    except urllib.error.URLError as e:
        sys.exit(f"Could not reach the ABS landing page: {e}")

    found: dict[str, str] = {}
    releases: set[str] = set()
    for href, release, name in LINK.findall(page):
        if name in WANTED or name == AGE:
            found[name] = BASE + href
            releases.add(release.lower())

    missing = (set(WANTED) | {AGE}) - set(found)
    if missing:
        sys.exit(
            "\nThe ABS page no longer links the workbooks this project reads.\n"
            f"Missing: {', '.join(sorted(missing))}\n\n"
            "The page layout has probably changed. Open the landing page, find "
            "the new links, and update WANTED or LINK in src/fetch_abs.py."
        )
    if len(releases) != 1:
        sys.exit(
            f"\nThe workbooks point at more than one release: {sorted(releases)}.\n"
            "Mixing releases would break reconciliation, so nothing was downloaded."
        )
    return releases.pop(), found


def verify(path: Path, fragment: str) -> None:
    """Open the workbook and confirm it holds the NT column we expect."""
    import pandas as pd

    if path.stat().st_size < 20_000:
        sys.exit(f"{path.name} is only {path.stat().st_size} bytes. "
                 "That is an error page, not a workbook.")
    try:
        head = pd.read_excel(path, sheet_name="Data1", header=None, nrows=1)
    except Exception as e:
        sys.exit(f"{path.name} did not open as an ABS workbook: {e}")

    header = " | ".join(str(v).lower() for v in head.iloc[0])
    if fragment not in header or "northern territory" not in header:
        sys.exit(
            f"\n{path.name} opened, but its first row does not contain a "
            f"Northern Territory '{fragment}' column.\n"
            "The ABS has changed this workbook. Nothing in data/raw was touched."
        )


def verify_age(path: Path) -> None:
    """The age table names its columns by age, so check the Index sheet for
    the Territory and the first row for persons columns instead."""
    import pandas as pd

    if path.stat().st_size < 20_000:
        sys.exit(f"{path.name} is only {path.stat().st_size} bytes. "
                 "That is an error page, not a workbook.")
    try:
        index = pd.read_excel(path, sheet_name="Index", header=None)
        head = pd.read_excel(path, sheet_name="Data1", header=None, nrows=1)
    except Exception as e:
        sys.exit(f"{path.name} did not open as an ABS workbook: {e}")
    text = " ".join(str(v).lower() for v in index.to_numpy().ravel())
    header = " | ".join(str(v).lower() for v in head.iloc[0])
    if "northern territory" not in text or "persons" not in header:
        sys.exit(f"\n{path.name} is not the Northern Territory age table it "
                 "used to be. Nothing in data/raw was touched.")


def regional(force: bool, check_only: bool) -> str:
    """Check the regional release. Never fatal: it is published once a year
    on its own timetable, and a problem here must not stop the quarterly
    national update. Returns a one-line status."""
    import pandas as pd

    try:
        page = get(REGIONAL_LANDING).decode("utf-8", "replace")
    except urllib.error.URLError as e:
        return f"regional: could not reach the page ({e}); left as it is"
    links = REGIONAL_LINK.findall(page)
    if not links:
        return "regional: workbook link not found on the page; left as it is"
    href, release, name = links[0]
    current = REGIONAL_MARKER.read_text().strip() if REGIONAL_MARKER.exists() else "(none)"
    print(f"Regional latest    : {release}")
    print(f"Regional in data/raw: {current}")
    if check_only or (release == current and not force):
        return "regional: up to date" if release == current else "regional: new release available"

    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / name
        try:
            dest.write_bytes(get(BASE + href))
            t1 = pd.read_excel(dest, sheet_name="Table 1", header=None)
        except Exception as e:
            return f"regional: download or open failed ({e}); left as it is"
        if dest.stat().st_size < 100_000 or not t1.astype(str).apply(
                lambda c: c.str.contains("Northern Territory")).any().any():
            return "regional: workbook did not look right; left as it is"
        for old in RAW.glob("32180DS0003_*.xlsx"):
            old.unlink()
        shutil.copy2(dest, RAW / name)
        REGIONAL_MARKER.write_text(release + "\n")
    return f"regional: updated to {release} ({name})"


def main() -> None:
    force = "--force" in sys.argv
    check_only = "--check" in sys.argv

    release, urls = discover()
    current = MARKER.read_text().strip() if MARKER.exists() else "(none recorded)"
    print(f"ABS latest release : {release}")
    print(f"Release in data/raw: {current}")

    if check_only:
        print("new release available" if release != current else "up to date")
        print(regional(force, check_only))
        return

    if release == current and not force:
        print("\nNo new release. Nothing downloaded, nothing changed.")
        print(regional(force, check_only))
        return

    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp)
        print()
        for name, url in sorted(urls.items()):
            dest = staging / name
            print(f"  downloading {name} ...", end=" ", flush=True)
            try:
                dest.write_bytes(get(url))
            except urllib.error.URLError as e:
                sys.exit(f"failed: {e}")
            print(f"{dest.stat().st_size // 1024} KB", end=" ")
            if name == AGE:
                verify_age(dest)
            else:
                verify(dest, WANTED[name])
            print("verified")

        # Every file is present and readable, so the swap is safe.
        for name in urls:
            shutil.copy2(staging / name, RAW / name)
        MARKER.write_text(release + "\n")

    print(f"\nUpdated data/raw to the {release} release.")
    print(regional(force, check_only))
    print("Now run: python src/pipeline.py && python src/interstate_flows.py "
          "&& python src/services.py && python src/build_dashboard.py")
    print("The pipeline's reconciliation gate decides whether these figures "
          "are fit to publish.")


if __name__ == "__main__":
    main()
