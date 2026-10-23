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

LANDING = ("https://www.abs.gov.au/statistics/people/population/"
           "national-state-and-territory-population/latest-release")
BASE = "https://www.abs.gov.au"

# The workbooks this project reads, and the Northern Territory column each one
# must contain. The check is what stops a layout change reaching the analysis.
WANTED = {
    "310102.xlsx": "net overseas migration",
    "310104.xlsx": "estimated resident population",
    "3101016A.xlsx": "interstate arrivals",
    "3101016B.xlsx": "interstate departures",
}

# A browser user agent: the ABS serves a block page to the default urllib one.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

LINK = re.compile(
    r'href="(/statistics/people/population/national-state-and-territory-population'
    r'/([a-z]{3}-\d{4})/([^"/]+\.xlsx))"',
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
        if name in WANTED:
            found[name] = BASE + href
            releases.add(release.lower())

    missing = set(WANTED) - set(found)
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


def main() -> None:
    force = "--force" in sys.argv
    check_only = "--check" in sys.argv

    release, urls = discover()
    current = MARKER.read_text().strip() if MARKER.exists() else "(none recorded)"
    print(f"ABS latest release : {release}")
    print(f"Release in data/raw: {current}")

    if check_only:
        print("new release available" if release != current else "up to date")
        return

    if release == current and not force:
        print("\nNo new release. Nothing downloaded, nothing changed.")
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
            verify(dest, WANTED[name])
            print("verified")

        # Every file is present and readable, so the swap is safe.
        for name in urls:
            shutil.copy2(staging / name, RAW / name)
        MARKER.write_text(release + "\n")

    print(f"\nUpdated data/raw to the {release} release.")
    print("Now run: python src/pipeline.py && python src/build_dashboard.py")
    print("The pipeline's reconciliation gate decides whether these figures "
          "are fit to publish.")


if __name__ == "__main__":
    main()
