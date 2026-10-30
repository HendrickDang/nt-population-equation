"""
Builds outputs/dashboard.html from the pipeline's outputs.

The page is self-contained: the quarterly series is embedded, so it opens
from a file, a web host, or an artifact link with nothing to fetch. Re-run
this after the pipeline whenever a new ABS release is loaded.

    python src/build_dashboard.py
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
RELEASE_FILE = ROOT / "data" / "raw" / "RELEASE"

MONTHS = {"jan": "January", "feb": "February", "mar": "March", "apr": "April",
          "may": "May", "jun": "June", "jul": "July", "aug": "August",
          "sep": "September", "oct": "October", "nov": "November",
          "dec": "December"}


def release_label() -> str:
    """"mar-2026" as the ABS writes it in the download path -> "March 2026"."""
    try:
        raw = RELEASE_FILE.read_text().strip().lower()
        month, year = raw.split("-")
        return f"{MONTHS[month[:3]]} {year}"
    except Exception:
        # The marker is written by src/fetch_abs.py. A missing or unexpected
        # value should not stop the page being built, so say what is known.
        return "release not recorded"

REPO = "https://github.com/HendrickDang/nt-population-equation"

TEMPLATE = """<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Territory Population Equation</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
<script>
/* Runs before the first paint, so a reader who chose a theme last time does
   not see the other one flash first. Storage can throw in a private window or
   with site data blocked, in which case the page just follows the system
   setting, which is what it did before this control existed. */
(function () {
  try {
    var t = localStorage.getItem("theme");
    if (t === "dark" || t === "light") {
      document.documentElement.setAttribute("data-theme", t);
    }
  } catch (e) {}
})();
</script>
<style>
/* Phone first. One column, big numbers, every figure captioned in plain words.
   The three series hues are the project's validated set and carry all the data;
   everything else is ink and surface. */
:root {
  --bg: #fbfaf8;
  --surface: #ffffff;
  --surface-2: #f4f2ee;
  --line: #e4e0d8;
  --ink: #171613;
  --ink-2: #55504a;
  --ink-3: #87817a;
  --accent: #a8552a;
  --s-natural: #2a78d6;
  --s-overseas: #eb6834;
  --s-interstate: #1baf7a;
  --radius: 14px;
  --cited-bg: #f6f3ec;
  --cited-line: #ddd3c0;
  --cited-ink: #7a5d2e;
  --body: "Inter", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #121110; --surface: #1a1916; --surface-2: #232019; --line: #322e27;
    --ink: #f4f1ea; --ink-2: #bdb6ab; --ink-3: #8b857c; --accent: #e09a6d;
    --s-natural: #4a90ea; --s-overseas: #e26a35; --s-interstate: #19ad76;
    --cited-bg: #221e17; --cited-line: #3d3527; --cited-ink: #c9a66b;
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #121110; --surface: #1a1916; --surface-2: #232019; --line: #322e27;
  --ink: #f4f1ea; --ink-2: #bdb6ab; --ink-3: #8b857c; --accent: #e09a6d;
  --s-natural: #4a90ea; --s-overseas: #e26a35; --s-interstate: #19ad76;
  --cited-bg: #221e17; --cited-line: #3d3527; --cited-ink: #c9a66b;
  color-scheme: dark;
}

/* ---- theme control ------------------------------------------------------
   The button shows the theme it switches TO, so the moon means "go dark".
   Which icon is visible follows exactly the same cascade as the colours
   above: system preference unless data-theme overrides it. */
.topbar { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.themer {
  flex: none; width: 38px; height: 38px; margin-top: -7px;
  display: grid; place-items: center; cursor: pointer;
  background: var(--surface); color: var(--ink-2);
  border: 1px solid var(--line); border-radius: 50%;
  transition: color .15s, border-color .15s;
}
.themer:hover { color: var(--ink); border-color: var(--ink-3); }
.themer:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.themer svg { width: 18px; height: 18px; display: block; }
.themer .sun { display: none; }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) .themer .moon { display: none; }
  :root:not([data-theme="light"]) .themer .sun  { display: block; }
}
:root[data-theme="dark"]  .themer .moon { display: none; }
:root[data-theme="dark"]  .themer .sun  { display: block; }
:root[data-theme="light"] .themer .moon { display: block; }
:root[data-theme="light"] .themer .sun  { display: none; }
@media print { .themer { display: none; } }

* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0; background: var(--bg); color: var(--ink);
  font-family: var(--body); font-size: 16px; line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}
.wrap {
  max-width: 1120px; margin: 0 auto;
  padding: 28px max(16px, env(safe-area-inset-left, 0px)) 64px;
}

/* ---- header ------------------------------------------------------------ */
.eyebrow {
  font-size: 11px; letter-spacing: .14em; text-transform: uppercase;
  color: var(--accent); font-weight: 600; margin-bottom: 10px;
}
h1 {
  font-size: clamp(27px, 7vw, 40px); line-height: 1.12; font-weight: 700;
  letter-spacing: -.022em; margin: 0 0 10px; text-wrap: balance;
}
.standfirst { color: var(--ink-2); margin: 0; max-width: 58ch; font-size: 15.5px; }

/* ---- hero -------------------------------------------------------------- */
.hero {
  margin: 26px 0 22px; padding: 24px 20px;
  background: var(--surface); border: 1px solid var(--line);
  border-radius: var(--radius);
}
.hero-fig {
  font-size: clamp(56px, 17vw, 86px); line-height: .92; font-weight: 700;
  letter-spacing: -.045em; color: var(--s-overseas); margin-bottom: 10px;
}
.hero-say { font-size: 17px; font-weight: 500; color: var(--ink); max-width: 36ch; }
.hero-sub { font-size: 14px; color: var(--ink-2); margin-top: 9px; max-width: 48ch; }
@media (min-width: 740px) {
  /* Side by side once there is room, so the figure is not marooned beside an
     empty half of the card. */
  .hero { display: grid; grid-template-columns: auto 1fr; gap: 6px 36px;
          align-items: center; padding: 30px 28px; }
  .hero-fig { margin: 0; grid-row: span 2; }
  .hero-say { font-size: 19px; align-self: end; }
  .hero-sub { margin-top: 0; align-self: start; }
}

/* ---- stat tiles -------------------------------------------------------- */
.tiles {
  display: grid; gap: 10px; margin-bottom: 12px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
/* ---- live status strip ------------------------------------------------- */
.live {
  display: flex; align-items: flex-start; gap: 10px;
  margin-bottom: 36px; padding: 11px 14px;
  background: var(--surface); border: 1px solid var(--line);
  border-radius: var(--radius);
  font-size: 12.5px; color: var(--ink-2); line-height: 1.45;
}
.live b { color: var(--ink); font-weight: 600; }
.live .dot {
  flex: none; width: 8px; height: 8px; border-radius: 50%; margin-top: 5px;
  background: var(--s-interstate);
  box-shadow: 0 0 0 3px rgba(25, 173, 118, .20);
  animation: beat 2.6s ease-in-out infinite;
}
@keyframes beat {
  0%, 100% { box-shadow: 0 0 0 3px rgba(25, 173, 118, .20); }
  50%      { box-shadow: 0 0 0 7px rgba(25, 173, 118, 0); }
}
@media (prefers-reduced-motion: reduce) { .live .dot { animation: none; } }
@media (min-width: 740px) { .tiles { grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; } }
.tile {
  background: var(--surface); border: 1px solid var(--line);
  border-radius: var(--radius); padding: 15px 15px 14px; min-width: 0;
}
.tile-lab {
  font-size: 11.5px; letter-spacing: .07em; text-transform: uppercase;
  color: var(--ink-3); font-weight: 600; margin-bottom: 7px;
}
.tile-val { font-size: 25px; font-weight: 700; letter-spacing: -.03em; line-height: 1.1; }
.tile-note { font-size: 12.5px; color: var(--ink-2); margin-top: 5px; line-height: 1.35; }

/* ---- sections ---------------------------------------------------------- */
section { margin-bottom: 38px; }

/* ---- the opening row ----------------------------------------------------
   Below 1000px this is a plain stack and behaves exactly as it did. Above it
   the title and the headline figure take the left column and the forty-five
   year chart takes the right, so a reader meets the number and the picture in
   one glance instead of scrolling from one to the other. The chart sizes
   itself from its own column rather than from the window. */
@media (min-width: 1080px) {
  .top {
    display: grid; grid-template-columns: minmax(290px, 0.76fr) 1.24fr;
    gap: 34px; align-items: start; margin-bottom: 34px;
  }
  .top-l, .top-r { min-width: 0; }
  .top-r { margin-bottom: 0; }
  .top-l .standfirst { max-width: none; }
  /* The hero goes side by side at 740px and up. In a column this narrow it
     has to stack again, so that rule is undone here. */
  .top-l .hero { display: block; margin: 22px 0 0; padding: 24px 22px; }
  .top-l .hero-fig {
    font-size: clamp(54px, 5.2vw, 76px); margin: 0 0 10px; grid-row: auto;
  }
  .top-l .hero-say { font-size: 17px; max-width: none; }
  .top-l .hero-sub { margin-top: 9px; max-width: none; }
  /* In one column the button sits at the top right of the page. Left in the
     flow it lands between the title and the chart column, where it reads as
     though it belongs to the chart. */
  .top { position: relative; }
  .top .themer { position: absolute; top: 0; right: 0; margin-top: 0; }
  .top .topbar { display: block; }
}
h2 { font-size: 20px; font-weight: 700; letter-spacing: -.015em; margin: 0 0 5px; }
.note { color: var(--ink-2); font-size: 14.5px; margin: 0 0 15px; max-width: 64ch; }
.card {
  background: var(--surface); border: 1px solid var(--line);
  border-radius: var(--radius); padding: 18px 16px;
}
.meaning {
  font-size: 13px; color: var(--ink-2); margin: 13px 0 0;
  padding-top: 12px; border-top: 1px solid var(--line); line-height: 1.45;
}

/* ---- the equation, as a waterfall --------------------------------------
   Each column starts where the one before it finished, so the running total
   is the shape itself. The only column that descends is the only component
   that takes people away, which is the whole finding in one picture. */
.wf { display: flex; align-items: flex-end; gap: 6px; height: 232px; margin: 4px 0 0; }
@media (min-width: 560px) { .wf { gap: 14px; height: 268px; } }
.wf-col { flex: 1 1 0; min-width: 0; height: 100%; position: relative; }
.wf-bar { position: absolute; left: 0; right: 0; border-radius: 4px; }
.wf-num {
  position: absolute; left: 0; right: 0; text-align: center;
  font-size: 12.5px; font-weight: 700; letter-spacing: -.02em;
  font-variant-numeric: tabular-nums; white-space: nowrap;
}
@media (min-width: 560px) { .wf-num { font-size: 15px; } }
/* The dashed carry line from one column's finish to the next one's start. */
.wf-link {
  position: absolute; left: 50%; width: calc(100% + 6px); height: 0;
  border-top: 1px dashed var(--ink-3); opacity: .5;
}
@media (min-width: 560px) { .wf-link { width: calc(100% + 14px); } }
.wf-base {
  position: absolute; left: 0; right: 0; bottom: 0; height: 1px;
  background: var(--line);
}
.wf-labs { display: flex; gap: 6px; margin-top: 9px; }
@media (min-width: 560px) { .wf-labs { gap: 14px; } }
.wf-labs > div {
  flex: 1 1 0; min-width: 0; text-align: center; font-size: 11.5px;
  line-height: 1.3; color: var(--ink-2);
}
.wf-labs b { display: block; color: var(--ink); font-weight: 600; }
@media (min-width: 560px) { .wf-labs > div { font-size: 13px; } }
.wf-peak {
  margin-top: 16px; padding-top: 13px; border-top: 1px solid var(--line);
  font-size: 13.5px; color: var(--ink-2); line-height: 1.5;
}
.wf-peak b { color: var(--ink); font-weight: 600; }

/* ---- decade strip ------------------------------------------------------ */
.decs { display: flex; gap: 6px; }
.dc { flex: 1 1 0; min-width: 0; text-align: center; }
.dc-cell {
  position: relative; height: 54px; border-radius: 5px;
  background: var(--surface-2); overflow: hidden;
}
.dc-cell i {
  position: absolute; left: 0; right: 0; bottom: 0;
  background: var(--s-interstate);
}
.dc-val {
  margin-top: 7px; font-size: 14px; font-weight: 700; letter-spacing: -.02em;
  font-variant-numeric: tabular-nums;
}
.dc-lab { font-size: 11.5px; color: var(--ink-2); margin-top: 1px; }
.dc-sub { font-size: 11px; color: var(--ink-3); font-variant-numeric: tabular-nums; }

/* ---- nine in ten -------------------------------------------------------- */
.dots { display: flex; gap: 5px; margin: 12px 0 0; }
.dots i {
  width: 11px; height: 11px; border-radius: 50%;
  background: var(--s-overseas);
}
.dots i.off { background: var(--line); }

/* Shown only where a pointer can hover. On a phone the instruction was both
   clutter and untrue. */
.hint { display: none; }
@media (hover: hover) and (pointer: fine) {
  .hint {
    display: block; margin: -2px 0 10px; font-size: 12px; color: var(--ink-3);
  }
}
/* The hero figure sets a large negative letter-spacing in em, which computes
   against its own 86px and then inherits that pixel value to every child. Left
   alone it crushes this caption into overlapping letters, so both the spacing
   and the tight heading line-height are reset here. */
.dots-cap {
  font-size: 12px; color: var(--ink-3); margin-top: 7px;
  letter-spacing: normal; line-height: 1.35; font-weight: 400;
}

/* ---- section numbering --------------------------------------------------
   Sits above the heading rather than in a side gutter: the wrap has only a
   16px outside padding, so a gutter would be clipped at narrow widths and at
   exactly the max width. The poster numbers its sections the same way. */
.wrap section > h2::before {
  content: attr(data-n); display: block; margin-bottom: 4px;
  font-size: 11.5px; font-weight: 700; letter-spacing: .1em;
  color: var(--accent);
}

/* ---- chart ------------------------------------------------------------- */
.legend { display: flex; flex-wrap: wrap; gap: 8px 16px; margin-bottom: 12px; }
.key { display: inline-flex; align-items: center; gap: 7px; font-size: 13px; color: var(--ink-2); }
.swatch { width: 14px; height: 3px; border-radius: 2px; flex: none; }
svg { display: block; width: 100%; height: auto; }
.readout {
  display: flex; flex-wrap: wrap; gap: 3px 16px; margin-top: 12px;
  padding-top: 11px; border-top: 1px solid var(--line);
  font-size: 13px; color: var(--ink-2); font-variant-numeric: tabular-nums;
}
.readout b { color: var(--ink); font-weight: 600; }
.readout .pin { color: var(--accent); }

/* ---- turnover ---------------------------------------------------------- */
.flow3 {
  display: grid; gap: 16px 22px; grid-template-columns: repeat(2, minmax(0, 1fr));
  padding-bottom: 16px; border-bottom: 1px solid var(--line);
}
@media (min-width: 740px) { .flow3 { grid-template-columns: repeat(4, minmax(0, 1fr)); } }
.f-lab {
  font-size: 11.5px; letter-spacing: .07em; text-transform: uppercase;
  color: var(--ink-3); font-weight: 600; margin-bottom: 5px;
}
.f-val { font-size: 24px; font-weight: 700; letter-spacing: -.03em; line-height: 1.1; }
.f-sub { font-size: 12.5px; color: var(--ink-2); margin-top: 4px; line-height: 1.35; }

.lim { border: 0; background: none; margin-top: 12px; }
.lim summary { padding: 8px 0; font-size: 13px; color: var(--cited-ink); }
.lim summary::after { font-size: 17px; }
.lim[open] summary { border-bottom: 0; }
.lim ul { margin: 2px 0 4px; padding-left: 17px; font-size: 12.5px; color: var(--ink-2); }
.lim li { margin-bottom: 5px; }

/* ---- cited evidence: a different class of data, and it must look it ---- */
.cited {
  border: 1px solid var(--cited-line); border-radius: var(--radius);
  background: var(--cited-bg); padding: 18px 16px;
}
.cited-badge {
  display: inline-flex; align-items: center; gap: 7px; font-size: 11px;
  letter-spacing: .08em; text-transform: uppercase; font-weight: 600;
  color: var(--cited-ink); margin-bottom: 14px;
}
.cited-badge::before {
  content: ""; width: 7px; height: 7px; border-radius: 2px;
  background: var(--cited-ink); flex: none;
}
.cited h3 { color: var(--cited-ink); }
.bars { display: grid; gap: 13px; margin-top: 4px; }
.barpair { display: grid; grid-template-columns: 74px 1fr; gap: 10px; align-items: center; }
.barpair .age { font-size: 13px; color: var(--ink-2); font-variant-numeric: tabular-nums; }
.barset { display: grid; gap: 4px; }
.barline { display: grid; grid-template-columns: 1fr 38px; gap: 8px; align-items: center; }
.barline .track { height: 13px; border-radius: 3px; background: var(--surface-2); overflow: hidden; }
.barline .track > i { display: block; height: 100%; border-radius: 3px; }
.barline .pct { font-size: 12.5px; font-variant-numeric: tabular-nums; color: var(--ink-2); text-align: right; }
.barkey { display: flex; flex-wrap: wrap; gap: 8px 16px; margin: 2px 0 14px; }
.cite {
  font-size: 12.5px; color: var(--ink-2); line-height: 1.5;
  margin: 15px 0 0; padding-top: 13px; border-top: 1px solid var(--cited-line);
}
.cite b { color: var(--ink); font-weight: 600; }
.cite ul { margin: 7px 0 0; padding-left: 17px; }
.cite li { margin-bottom: 4px; }

/* ---- reading cards ----------------------------------------------------- */
.grid { display: grid; gap: 14px; grid-template-columns: 1fr; }
@media (min-width: 740px) { .grid { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
.card h3 {
  font-size: 11.5px; letter-spacing: .08em; text-transform: uppercase;
  color: var(--ink-3); font-weight: 600; margin: 0 0 14px;
}
.row { display: grid; grid-template-columns: 1fr auto; align-items: baseline; gap: 10px; margin-bottom: 12px; }
.row:last-of-type { margin-bottom: 0; }
.row .lab { font-size: 14px; color: var(--ink-2); min-width: 0; }
.row .val { font-variant-numeric: tabular-nums; font-weight: 700; font-size: 15px; letter-spacing: -.02em; }
.bar { grid-column: 1 / -1; height: 6px; border-radius: 3px; background: var(--surface-2); overflow: hidden; margin-top: 6px; }
.bar > i { display: block; height: 100%; border-radius: 3px; }

table { border-collapse: collapse; width: 100%; font-size: 14px; }
th, td { text-align: right; padding: 8px 4px; border-bottom: 1px solid var(--line); }
th:first-child, td:first-child { text-align: left; }
th { color: var(--ink-3); font-weight: 600; font-size: 11px; letter-spacing: .07em; text-transform: uppercase; }
td { font-variant-numeric: tabular-nums; }
tr:last-child td { border-bottom: 0; }

/* ---- method ------------------------------------------------------------ */
.check {
  display: inline-flex; align-items: center; gap: 9px; font-size: 13.5px;
  color: var(--ink-2); background: var(--surface); border: 1px solid var(--line);
  border-radius: 999px; padding: 9px 15px; margin-bottom: 16px;
  font-variant-numeric: tabular-nums;
}
.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--s-interstate); flex: none; }
details { border: 1px solid var(--line); border-radius: var(--radius); background: var(--surface); }
summary {
  cursor: pointer; padding: 15px 16px; font-weight: 600; font-size: 15px;
  list-style: none; display: flex; justify-content: space-between; align-items: center;
}
summary::-webkit-details-marker { display: none; }
summary::after { content: "+"; color: var(--ink-3); font-weight: 400; font-size: 20px; }
details[open] summary::after { content: "\2212"; }
details[open] summary { border-bottom: 1px solid var(--line); }
.method { padding: 16px; columns: 2 300px; column-gap: 32px; }
.method p { margin: 0 0 14px; break-inside: avoid; color: var(--ink-2); font-size: 14px; }
.method strong { color: var(--ink); font-weight: 600; }

footer { border-top: 1px solid var(--line); padding-top: 20px; font-size: 13px; color: var(--ink-3); line-height: 1.6; }
footer a { color: var(--accent); }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>

<div class="wrap">
  <div class="top">
    <div class="top-l">
  <header>
    <div class="topbar">
      <div class="eyebrow">Northern Territory</div>
      <button class="themer" id="themer" type="button" title="Switch theme"
              aria-label="Switch to the dark theme">
        <svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"
             aria-hidden="true">
          <path d="M20.5 14.3A8.5 8.5 0 0 1 9.7 3.5a8.5 8.5 0 1 0 10.8 10.8z"/>
        </svg>
        <svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"
             aria-hidden="true">
          <circle cx="12" cy="12" r="4.2"/>
          <path d="M12 2.3v2.2M12 19.5v2.2M4.1 4.1l1.6 1.6M18.3 18.3l1.6 1.6M2.3 12h2.2M19.5 12h2.2M4.1 19.9l1.6-1.6M18.3 5.7l1.6-1.6"/>
        </svg>
      </button>
    </div>
    <h1>The Territory&rsquo;s Population Equation</h1>
    <p class="standfirst">One part has been negative for __NIM_RUN__ straight
      quarters. The population grows anyway.</p>
  </header>

  <div class="hero">
    <div class="hero-fig">__NOM_SHARE__%
      <div class="dots" role="img"
           aria-label="Nine of ten dots filled, standing for nine in ten people">
        <i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i class="off"></i>
      </div>
    </div>
    <div class="hero-say">of the Territory&rsquo;s population growth last year
      came from overseas migration.</div>
    <div class="hero-sub">Year to __REF__. A decade ago, __DEP10__%.</div>
  </div>

    </div>

  <section class="top-r">
    <h2 data-n="01">Forty-five years of the same three parts</h2>
    <p class="note">Every person added or lost belongs to one of three
      parts.</p>
    <div class="card">
      <div class="legend">
        <span class="key"><span class="swatch" style="background:var(--s-natural)"></span>Natural increase</span>
        <span class="key"><span class="swatch" style="background:var(--s-overseas)"></span>Net overseas migration</span>
        <span class="key"><span class="swatch" style="background:var(--s-interstate)"></span>Net interstate migration</span>
      </div>
      <p class="hint">Hover any point to read that quarter, click to hold it.</p>
      <svg id="chart" role="img"
        aria-label="Northern Territory population change by component, quarterly, 1982 to 2026"></svg>
      <div class="readout" id="readout"></div>
      <p class="meaning">Births minus deaths barely moves. The other two swing
        hard, and interstate migration has spent most of forty years below zero.
        Four-quarter rolling average, __START__ to __REF__.</p>
    </div>
  </section>
  </div>

  <div class="tiles">
    <div class="tile">
      <div class="tile-lab">Population</div>
      <div class="tile-val">__ERP__</div>
      <div class="tile-note">Estimated residents, __REF__</div>
    </div>
    <div class="tile">
      <div class="tile-lab">Growth, 12 months</div>
      <div class="tile-val">+__TOTAL__</div>
      <div class="tile-note">__GROWTH_PCT__% more than a year earlier</div>
    </div>
    <div class="tile">
      <div class="tile-lab">Interstate deficit</div>
      <div class="tile-val">__NIM_RUN__ qtrs</div>
      <div class="tile-note">Unbroken since __NIM_LAST__</div>
    </div>
    <div class="tile">
      <div class="tile-lab">Validation</div>
      <div class="tile-val" style="color:var(--s-interstate)">Passed</div>
      <div class="tile-note">Parts match the published total exactly</div>
    </div>
  </div>

  <div class="live">
    <span class="dot"></span>
    <span><b>ABS __RELEASE__</b> &middot; rebuilt from the source workbooks on
      __BUILT__ &middot; published only because the three components reconciled
      against the change the ABS publishes separately</span>
  </div>

  <section>
    <h2 data-n="02">Where the growth came from</h2>
    <p class="note">The same three parts over the last twelve months. Each
      column starts where the one before it finished, so the height is the
      running total and only one column comes back down.</p>
    <div class="card">
      __EQUATION__

    </div>
  </section>

  <section>
    <h2 data-n="03">The two flows behind net interstate migration</h2>
    <p class="note">A net loss of __NIM_ABS__ does not say whether fewer arrived or
      more left. ABS tables 16A and 16B.</p>
    <div class="card">
      <div class="flow3">
        <div><div class="f-lab">Arrived</div>
          <div class="f-val" style="color:var(--s-interstate)">__ARR__</div></div>
        <div><div class="f-lab">Left</div>
          <div class="f-val" style="color:var(--s-overseas)">__DEP__</div></div>
        <div><div class="f-lab">Net</div>
          <div class="f-val">__NETF__</div></div>
        <div><div class="f-lab">Gross moves</div>
          <div class="f-val">__CHURN__</div>
          <div class="f-sub">__CHURN_PCT__% of the population, one in nine</div></div>
      </div>

      <svg id="flows" role="img" style="margin-top:18px"
        aria-label="Northern Territory interstate arrivals and departures, quarterly"></svg>
      <div class="readout" id="flowsout"></div>

      <p class="meaning">Against the previous decade, arrivals are down __ARR_CHG__%
        and departures down __DEP_CHG__%. Neither side alone explains the deficit:
        the whole exchange is slowing. <b>Validated</b> against the published net
        across all __FLOWQ__ quarters, largest difference __FLOWDIFF__.</p>
    </div>
  </section>

  <section>
    <h2 data-n="04">Who intends to stay</h2>
    <p class="note">Population data cannot say who plans to stay. This is cited
      survey evidence, not pipeline output, and the validation gate does not
      apply to it.</p>
    <div class="cited">
      <span class="cited-badge">Cited evidence &middot; not computed here</span>

      <h3>Intending to stay, by home ownership &middot; age __OWN_AGE__</h3>
      <div class="barkey">
        <span class="key"><span class="swatch" style="background:var(--s-natural)"></span>Own or purchasing</span>
        <span class="key"><span class="swatch" style="background:var(--ink-3)"></span>Do not own</span>
      </div>
      __OWNBARS__

      <h3 style="margin-top:22px">Intending to stay, by country of birth</h3>
      <div class="barkey">
        <span class="key"><span class="swatch" style="background:var(--s-overseas)"></span>Born overseas</span>
        <span class="key"><span class="swatch" style="background:var(--s-natural)"></span>Born in Australia</span>
      </div>
      __BIRTHBARS__

      <p class="cite">
        <b>Source.</b> __CITATION__<br>
        <b>Measure.</b> __MEASURE__<br>
        <b>Base.</b> __BASE__ __RESP__ people completed the survey; __RESP_CUR__ were
        current Territory residents.<br>
      </p>
      <details class="lim"><summary>Limitations</summary>
        <ul>__LIMITS__</ul>
      </details>
    </div>
  </section>

  <section>
    <h2 data-n="05">Three readings</h2>
    <p class="note">Each computed over the whole series, not a chosen window.</p>
    <div class="grid">
      <div class="card">
        <h3>Reliance on overseas migration</h3>
        __DEPENDENCY__
        <p class="meaning">Three quarters of growth over a decade, nine tenths of
          it last year.</p>
      </div>
      <div class="card">
        <h3>How much each part moves</h3>
        __VOLATILITY__
        <p class="meaning">Standard deviation over mean absolute value. Higher
          means less predictable.</p>
      </div>
      <div class="card">
        <h3>Interstate migration by decade</h3>
        <div class="decs">__DECADES__</div>
        <p class="meaning">Share of that decade's quarters in which interstate
          migration added people, with the mean per quarter below. Half the
          quarters in the 1980s. Eight per cent in the 2010s.</p>
      </div>
    </div>
  </section>

  <section>
    <h2 data-n="06">How these numbers were produced</h2>
    <span class="check"><span class="dot"></span>
      Reconciliation passed &middot; parts sum to __RECON__ against a published
      __RECON__ &middot; difference __DIFF__</span>
    <details>
      <summary>Method, limitations and scope</summary>
      <div class="method">
        <p><strong>Decomposition.</strong> Quarterly components for the Northern
        Territory from ABS table 310102, __START__ to __REF__, __QUARTERS__
        quarters. Population level from table 310104.</p>
        <p><strong>Validation before reporting.</strong> Natural increase plus net
        interstate plus net overseas migration must equal the change the ABS
        publishes separately for the same period. The pipeline checks this first
        and writes nothing at all if it fails.</p>
        <p><strong>Volatility.</strong> Coefficient of variation against the mean
        absolute value, because interstate migration is mostly negative and a
        signed mean would make the measure meaningless.</p>
        <p><strong>Smoothing.</strong> The chart plots a four-quarter rolling
        average. Quarterly figures are noisy and the shape is what matters; raw
        values are in the repository.</p>
        <p><strong>A break in the series.</strong> The ABS moved net overseas
        migration to the 12-of-16-months rule from September 2006, so levels
        either side are not comparable. The volatility ranking is unchanged on the
        full series, on the period since the change, and on the period before it.</p>
        <p><strong>What the estimates cannot do.</strong> A person can change
        category under the 12-of-16-month rule without changing address.
        Interstate movement comes from administrative address records, so people
        who rarely update them are counted late or not at all. Census undercount
        is higher in the Territory than nationally, especially in remote
        communities.</p>
        <p><strong>Scope.</strong> This work is descriptive. It characterises the
        structure of population change and the uncertainty attached to forecasting
        it. It makes no policy recommendation.</p>
      </div>
    </details>
  </section>

  <footer>
    Van Hoi (Hendrick) Dang &middot; Ngoc Ngan Le &middot; Phuong Vy Ho &middot; Thi Kim Anh Bui<br>
    Source: ABS, <i>National, state and territory population</i>, __REF__,
    tables 310102 and 310104.<br>
    Code and data: <a href="__REPO__">__REPO_SHORT__</a>
  </footer>
</div>

<script>
const DATA = __DATA__;

const S = [
  { key: "natural_increase", label: "Natural increase", short: "Natural", css: "--s-natural" },
  { key: "net_overseas_migration", label: "Net overseas migration", short: "Overseas", css: "--s-overseas" },
  { key: "net_interstate_migration", label: "Net interstate migration", short: "Interstate", css: "--s-interstate" },
];

const svg = document.getElementById("chart");
const readout = document.getElementById("readout");
const dates = DATA.series.dates;
const n = dates.length;

let lo = Infinity, hi = -Infinity;
for (const s of S) for (const v of DATA.series[s.key]) { if (v < lo) lo = v; if (v > hi) hi = v; }
const pad = (hi - lo) * 0.07;
lo -= pad; hi += pad;

/* The plot is re-laid-out, not just rescaled, when the screen is narrow: a
   phone gets a taller box and no end-of-line labels, because at that width the
   labels collide with each other and with the plot. The legend above carries
   identity in both cases. */
let W, H, M, narrow, endLabels;
function layout() {
  /* The viewBox is set to the box the chart actually occupies, so nothing is
     scaled and every font size below is the size it renders at. The window is
     the wrong thing to measure once the chart shares a row with the opening
     text: on a wide screen it can still be a 600px column. */
  const cw = Math.max(280, Math.round(svg.getBoundingClientRect().width
                                    || svg.parentElement.clientWidth));
  narrow = cw < 560;
  endLabels = cw >= 860;
  W = cw;
  H = narrow ? 400 : 380;
  M = { t: 14, r: endLabels ? 182 : 14, b: 30, l: narrow ? 38 : 54 };
  if (narrow) M.t = 10;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
}

const px = i => M.l + (i / (n - 1)) * (W - M.l - M.r);
const py = v => M.t + (1 - (v - lo) / (hi - lo)) * (H - M.t - M.b);
const ink = t => getComputedStyle(document.documentElement).getPropertyValue(t).trim();

function niceTicks(a, b, count) {
  const span = b - a, step0 = span / count;
  const mag = Math.pow(10, Math.floor(Math.log10(step0)));
  const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => s >= step0) || mag * 10;
  const out = [];
  for (let v = Math.ceil(a / step) * step; v <= b; v += step) out.push(Math.round(v));
  return out;
}

let pinned = null;

function draw() {
  layout();
  const c = { line: ink("--line"), ink2: ink("--ink-2"), ink3: ink("--ink-3") };
  const fs = narrow ? 10 : 11.5;
  let out = "";

  for (const t of niceTicks(lo, hi, narrow ? 6 : 6)) {
    const y = py(t).toFixed(1);
    out += `<line x1="${M.l}" y1="${y}" x2="${W - M.r}" y2="${y}" stroke="${c.line}" stroke-width="1"/>`;
    out += `<text x="${M.l - 7}" y="${y}" fill="${c.ink3}" font-size="${fs}" text-anchor="end" dominant-baseline="middle">${t.toLocaleString()}</text>`;
  }
  out += `<line x1="${M.l}" y1="${py(0).toFixed(1)}" x2="${W - M.r}" y2="${py(0).toFixed(1)}" stroke="${c.ink2}" stroke-width="1.5"/>`;

  const every = narrow ? 10 : 5;
  for (let i = 0; i < n; i++) {
    const y = dates[i].slice(0, 4);
    if (y % every === 0 && dates[i].slice(5) === "03") {
      out += `<text x="${px(i).toFixed(1)}" y="${H - 8}" fill="${c.ink3}" font-size="${fs}" text-anchor="middle">${narrow ? "’" + y.slice(2) : y}</text>`;
    }
  }

  for (const s of S) {
    const vals = DATA.series[s.key];
    const d = vals.map((v, i) => `${i ? "L" : "M"}${px(i).toFixed(1)} ${py(v).toFixed(1)}`).join(" ");
    out += `<path d="${d}" fill="none" stroke="${ink(s.css)}" stroke-width="${narrow ? 1.8 : 2.2}" stroke-linejoin="round" stroke-linecap="round"/>`;
    if (endLabels) {
      out += `<text x="${(W - M.r + 11).toFixed(1)}" y="${py(vals[n - 1]).toFixed(1)}" fill="${c.ink2}" font-size="12.5" dominant-baseline="middle">${s.label}</text>`;
    }
  }

  out += `<g id="hover" style="display:none"><line id="hl" y1="${M.t}" y2="${H - M.b}" stroke="${c.ink3}" stroke-width="1" stroke-dasharray="3 3"/>`;
  for (const s of S) out += `<circle class="hdot" r="${narrow ? 4 : 5}" fill="${ink(s.css)}" stroke="${ink("--surface")}" stroke-width="2"/>`;
  out += `</g>`;

  svg.innerHTML = out;
  showAt(pinned !== null ? pinned : n - 1);
}

function showAt(i) {
  const g = svg.querySelector("#hover");
  if (!g) return;
  g.style.display = "";
  g.querySelector("#hl").setAttribute("x1", px(i).toFixed(1));
  g.querySelector("#hl").setAttribute("x2", px(i).toFixed(1));
  const dots = g.querySelectorAll(".hdot");
  S.forEach((s, k) => {
    dots[k].setAttribute("cx", px(i).toFixed(1));
    dots[k].setAttribute("cy", py(DATA.series[s.key][i]).toFixed(1));
  });
  const [y, m] = dates[i].split("-");
  const q = { "03": "Mar", "06": "Jun", "09": "Sep", "12": "Dec" }[m] || m;
  readout.innerHTML = `<span><b>${q} ${y}</b></span>` + S.map(s =>
    `<span>${narrow ? s.short : s.label} <b>${Math.round(DATA.series[s.key][i]).toLocaleString()}</b></span>`).join("")
    + (pinned !== null ? `<span class="pin">held &middot; tap to release</span>` : "");
}

function indexAt(clientX) {
  const r = svg.getBoundingClientRect();
  const x = (clientX - r.left) / r.width * W;
  const i = Math.round((x - M.l) / (W - M.l - M.r) * (n - 1));
  return (i >= 0 && i < n) ? i : null;
}

svg.addEventListener("mousemove", e => {
  if (pinned !== null) return;
  const i = indexAt(e.clientX); if (i !== null) showAt(i);
});
svg.addEventListener("mouseleave", () => { if (pinned === null) showAt(n - 1); });
svg.addEventListener("click", e => {
  const i = indexAt(e.clientX);
  if (pinned !== null) { pinned = null; if (i !== null) showAt(i); return; }
  if (i !== null) { pinned = i; showAt(i); }
});
svg.addEventListener("touchmove", e => {
  const i = indexAt(e.touches[0].clientX);
  if (i !== null) { pinned = i; showAt(i); }
  e.preventDefault();
}, { passive: false });

/* The turnover chart. Same layout rules as the component chart, two series,
   and the gap between them shaded so the net reads as an area rather than a
   number you have to work out. */
const FSVG = document.getElementById("flows");
const FOUT = document.getElementById("flowsout");
const F = DATA.flows;

let fW, fH, fM, fnarrow, fEnd;
function flayout() {
  /* Measured independently of the chart above: after the split the two live
     in columns of different widths. */
  const cw = Math.max(280, Math.round(FSVG.getBoundingClientRect().width
                                    || FSVG.parentElement.clientWidth));
  fnarrow = cw < 560;
  fEnd = cw >= 860;
  fW = cw;
  fH = fnarrow ? 300 : 320;
  fM = { t: fnarrow ? 10 : 14, r: fEnd ? 100 : 14, b: 30, l: fnarrow ? 42 : 54 };
  FSVG.setAttribute("viewBox", `0 0 ${fW} ${fH}`);
}
let flo = Infinity, fhi = -Infinity;
for (const k of ["arrivals", "departures"])
  for (const v of F[k]) { if (v < flo) flo = v; if (v > fhi) fhi = v; }
const fpadv = (fhi - flo) * 0.08; flo -= fpadv; fhi += fpadv;
const fn = F.dates.length;
const fpx = i => fM.l + (i / (fn - 1)) * (fW - fM.l - fM.r);
const fpy = v => fM.t + (1 - (v - flo) / (fhi - flo)) * (fH - fM.t - fM.b);

function fdraw() {
  flayout();
  const c = { line: ink("--line"), ink2: ink("--ink-2"), ink3: ink("--ink-3") };
  const fs = fnarrow ? 10 : 11.5;
  let out = "";
  for (const tk of niceTicks(flo, fhi, fnarrow ? 4 : 5)) {
    const y = fpy(tk).toFixed(1);
    out += `<line x1="${fM.l}" y1="${y}" x2="${fW - fM.r}" y2="${y}" stroke="${c.line}" stroke-width="1"/>`;
    out += `<text x="${fM.l - 7}" y="${y}" fill="${c.ink3}" font-size="${fs}" text-anchor="end" dominant-baseline="middle">${tk.toLocaleString()}</text>`;
  }
  const every = fnarrow ? 10 : 5;
  for (let i = 0; i < fn; i++) {
    const y = F.dates[i].slice(0, 4);
    if (y % every === 0 && F.dates[i].slice(5) === "03")
      out += `<text x="${fpx(i).toFixed(1)}" y="${fH - 8}" fill="${c.ink3}" font-size="${fs}" text-anchor="middle">${fnarrow ? "\u2019" + y.slice(2) : y}</text>`;
  }
  // the gap, shaded in the colour of whichever flow is on top
  const up = [], dn = [];
  for (let i = 0; i < fn; i++) {
    up.push(`${fpx(i).toFixed(1)} ${fpy(F.arrivals[i]).toFixed(1)}`);
    dn.push(`${fpx(i).toFixed(1)} ${fpy(F.departures[i]).toFixed(1)}`);
  }
  out += `<path d="M${up.join(" L")} L${dn.reverse().join(" L")} Z" fill="${ink("--s-overseas")}" opacity="0.13"/>`;
  for (const [k, hue, label] of [["arrivals", "--s-interstate", "Arrivals"],
                                 ["departures", "--s-overseas", "Departures"]]) {
    const d = F[k].map((v, i) => `${i ? "L" : "M"}${fpx(i).toFixed(1)} ${fpy(v).toFixed(1)}`).join(" ");
    out += `<path d="${d}" fill="none" stroke="${ink(hue)}" stroke-width="${fnarrow ? 1.8 : 2.2}" stroke-linejoin="round"/>`;
    if (fEnd)
      out += `<text x="${(fW - fM.r + 10).toFixed(1)}" y="${fpy(F[k][fn - 1]).toFixed(1)}" fill="${c.ink2}" font-size="12.5" dominant-baseline="middle">${label}</text>`;
  }
  FSVG.innerHTML = out;
  fshow(fn - 1);
}
function fshow(i) {
  const [y, m] = F.dates[i].split("-");
  const q = { "03": "Mar", "06": "Jun", "09": "Sep", "12": "Dec" }[m] || m;
  FOUT.innerHTML = `<span><b>${q} ${y}</b></span>`
    + `<span>Arrived <b>${Math.round(F.arrivals[i]).toLocaleString()}</b></span>`
    + `<span>Left <b>${Math.round(F.departures[i]).toLocaleString()}</b></span>`
    + `<span>Net <b>${Math.round(F.arrivals[i] - F.departures[i]).toLocaleString()}</b></span>`;
}
FSVG.addEventListener("mousemove", e => {
  const r = FSVG.getBoundingClientRect();
  const x = (e.clientX - r.left) / r.width * fW;
  const i = Math.round((x - fM.l) / (fW - fM.l - fM.r) * (fn - 1));
  if (i >= 0 && i < fn) fshow(i);
});
FSVG.addEventListener("mouseleave", () => fshow(fn - 1));

/* The theme control. The charts are drawn from the CSS custom properties, so
   the MutationObserver below redraws them when data-theme changes. Nothing is
   stored except the word "dark" or "light", and only for this reader. */
const themer = document.getElementById("themer");
function activeTheme() {
  const set = document.documentElement.getAttribute("data-theme");
  if (set === "dark" || set === "light") return set;
  return matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}
function labelThemer() {
  themer.setAttribute("aria-label", activeTheme() === "dark"
    ? "Switch to the light theme" : "Switch to the dark theme");
}
themer.addEventListener("click", () => {
  const next = activeTheme() === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  try { localStorage.setItem("theme", next); } catch (e) {}
  labelThemer();
});
labelThemer();

draw(); fdraw();
let rt;
addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(() => { draw(); fdraw(); }, 120); });
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { draw(); fdraw(); });
new MutationObserver(() => { draw(); fdraw(); }).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
</script>
"""


def _waterfall(f: dict) -> str:
    """The equation drawn as a waterfall.

    Each column starts where the previous one finished, so the height of the
    picture at any point is the running total. Natural increase and overseas
    migration climb, interstate migration is the one column that comes back
    down, and the last column restates the result from zero.

    The peak matters as much as the result. It is everything that came in
    before anything left, and it is the denominator behind the second share
    the page quotes, so the caption names it.
    """
    nat = f["natural_increase_12m"]
    nom = f["net_overseas_migration_12m"]
    nim = f["net_interstate_migration_12m"]
    total = f["total_growth_12m"]

    # (label under the column, value, bottom, top, hue)
    steps = [("Natural<b>increase</b>", nat, 0, nat, "--s-natural")]
    steps.append(("Net overseas<b>migration</b>", nom, nat, nat + nom, "--s-overseas"))
    steps.append(("Net interstate<b>migration</b>", nim,
                  min(nat + nom, nat + nom + nim), max(nat + nom, nat + nom + nim),
                  "--s-interstate"))
    steps.append(("<b>Total growth</b>", total, 0, total, "--ink-2"))

    # Headroom above the tallest column, so the number printed above it has
    # somewhere to sit instead of spilling out of the card.
    top = (max(s[3] for s in steps) or 1) * 1.16

    cols, labs = [], []
    for i, (label, value, lo, hi, hue) in enumerate(steps):
        bottom = lo / top * 100
        height = (hi - lo) / top * 100
        # The number sits above the column, except on the last one, where the
        # column reaches high enough that an outside label would clip.
        cols.append(
            f'<div class="wf-col">'
            f'<i class="wf-bar" style="bottom:{bottom:.2f}%;height:{height:.2f}%;'
            f'background:var({hue})"></i>'
            # An arrow as well as a sign, so direction does not rest on a
            # minus sign at a distance or on the colour of the column.
            f'<span class="wf-num" style="bottom:calc({bottom + height:.2f}% + 7px);'
            f'color:var({hue})">'
            + ("" if i == len(steps) - 1 else
               ("&#9650; " if value >= 0 else "&#9660; "))
            + f'{value:+,}</span>'
            + (f'<i class="wf-link" style="bottom:{(hi if value >= 0 else lo) / top * 100:.2f}%">'
               f'</i>' if i < len(steps) - 2 else "")
            + (f'<i class="wf-link" style="bottom:{lo / top * 100:.2f}%"></i>'
               if i == len(steps) - 2 else "")
            + '</div>'
        )
        labs.append(f"<div>{label}</div>")

    peak = (f'<div class="wf-peak">Everything that came in reached '
            f'<b>{f["inflows_12m"]:,}</b> before interstate migration gave '
            f'{abs(nim):,} of it back. Against that inflow, overseas migration '
            f'is <b>{f["nom_share_of_inflows_pct"]}%</b> rather than '
            f'{f["nom_share_of_growth_pct"]}%. Both are the same year; they '
            f'differ only in what they divide by.</div>')

    return ('<div class="wf"><span class="wf-base"></span>' + "".join(cols) + "</div>"
            + '<div class="wf-labs">' + "".join(labs) + "</div>" + peak)


def _bar(label, value, hue):
    return (f'<div class="barline"><span class="track">'
            f'<i style="width:{value}%;background:var({hue})"></i></span>'
            f'<span class="pct">{value}%</span></div>')


def main() -> None:
    f = json.loads((OUT / "figures.json").read_text())
    data = json.loads((OUT / "dashboard_data.json").read_text())

    # The turnover analysis and the cited survey evidence. Both are optional:
    # if either file is absent the page still builds, it just omits nothing
    # silently, because the tokens would show. So require them explicitly and
    # say what is missing.
    flow_path = OUT / "interstate_figures.json"
    if not flow_path.exists():
        raise SystemExit(
            "Missing outputs/interstate_figures.json\n"
            "Run `python src/interstate_flows.py` first; the dashboard now "
            "reports the arrivals and departures it produces."
        )
    flows = json.loads(flow_path.read_text())

    ttam_path = ROOT / "data" / "reference" / "ttam_2019.json"
    if not ttam_path.exists():
        raise SystemExit(f"Missing {ttam_path}")
    ttam = json.loads(ttam_path.read_text())

    # Four-quarter rolling averages, so the turnover chart reads the same way
    # as the component chart above it.
    import csv
    rows = list(csv.DictReader((OUT / "interstate_flows.csv").open()))
    def roll(key):
        vals = [float(r[key]) for r in rows]
        return [round(sum(vals[i - 3:i + 1]) / 4, 1) for i in range(3, len(vals))]
    data["flows"] = {
        "dates": [r["date"][:7] for r in rows[3:]],
        "arrivals": roll("arrivals"),
        "departures": roll("departures"),
    }

    own = ttam["by_home_ownership"]
    ownbars = (
        '<div class="bars"><div class="barpair"><span class="age">'
        + own["life_stage"] + '</span><div class="barset">'
        + _bar("Own or purchasing", own["own_or_purchasing"], "--s-natural")
        + _bar("Do not own", own["do_not_own"], "--ink-3")
        + '</div></div></div>'
    )

    bb = ttam["by_birthplace"]
    birthbars = '<div class="bars">' + "".join(
        f'<div class="barpair"><span class="age">{age}</span><div class="barset">'
        + _bar("Born overseas", o, "--s-overseas")
        + _bar("Born in Australia", a, "--s-natural")
        + '</div></div>'
        for age, o, a in zip(ttam["life_stages"], bb["born_overseas"], bb["born_in_australia"])
    ) + '</div>'

    limits = "".join(f"<li>{x}</li>" for x in ttam["limitations"])

    dependency = "".join(
        f'<div class="row"><span class="lab">Last {lab}</span>'
        f'<span class="val">{f["overseas_dependency"][key]}%</span>'
        f'<span class="bar"><i style="width:{f["overseas_dependency"][key]}%;'
        f'background:var(--s-overseas)"></i></span></div>'
        for key, lab in (("10y", "10 years"), ("5y", "5 years"), ("1y", "12 months"))
    )

    vol = f["volatility"]
    top = max(vol.values())
    names = {
        "natural_increase": ("Natural increase", "--s-natural"),
        "net_overseas_migration": ("Net overseas migration", "--s-overseas"),
        "net_interstate_migration": ("Net interstate migration", "--s-interstate"),
    }
    volatility = "".join(
        f'<div class="row"><span class="lab">{names[k][0]}</span>'
        f'<span class="val">{v:.2f}</span>'
        f'<span class="bar"><i style="width:{v / top * 100:.0f}%;'
        f'background:var({names[k][1]})"></i></span></div>'
        for k, v in sorted(vol.items(), key=lambda kv: -kv[1])
    )

    equation = _waterfall(f)

    # The decade strip. One hue, light to dark, because the measure is a
    # magnitude: the share of that decade's quarters in which interstate
    # migration added people. The 2010s sit almost empty between two darker
    # blocks, which is the point and is hard to see in a table of numbers.
    dec = f["nim_by_decade"]
    hi = max(v["positive_pct"] for v in dec.values()) or 1
    cells = []
    for d, v in dec.items():
        pct = v["positive_pct"]
        # Height and tint carry the same measure. Doubling the encoding is
        # deliberate: the block for the 2010s has to read as nearly empty at a
        # glance, and a tint alone is easy to miss on a projector. The numbers
        # sit outside the block, so nothing depends on contrast against it.
        tint = 0.16 + 0.84 * (pct / hi)
        cells.append(
            f'<div class="dc">'
            f'<div class="dc-cell"><i style="height:{12 + 0.88 * pct:.0f}%;'
            f'opacity:{tint:.2f}"></i></div>'
            f'<div class="dc-val">{pct}%</div>'
            f'<div class="dc-lab">{d}s</div>'
            f'<div class="dc-sub">{v["mean_per_quarter"]:,}</div></div>'
        )
    decades = "".join(cells)

    html = TEMPLATE
    for token, value in {
        "__NOM_SHARE__": f"{f['nom_share_of_growth_pct']}",
        "__REF__": f["reference_period"],
        "__START__": f["series_start"],
        "__QUARTERS__": f"{f['quarters_in_series']}",
        "__NI__": f"{f['natural_increase_12m']:,}",
        "__NIM_ABS__": f"{abs(f['net_interstate_migration_12m']):,}",
        "__NOM__": f"{f['net_overseas_migration_12m']:,}",
        "__TOTAL__": f"{f['total_growth_12m']:,}",
        "__ERP__": f"{f['erp_latest']:,}",
        "__NIM_RUN__": f"{f['nim_consecutive_negative']}",
        "__NIM_LAST__": f["nim_last_positive"],
        "__GROWTH_PCT__": f"{f['annual_growth_pct']:+.1f}",
        "__DEP10__": f"{f['overseas_dependency']['10y']}",
        "__RECON__": f"{f['reconciliation']['components_sum']:,}",
        "__DIFF__": f"{f['reconciliation']['difference']:g}",
        "__EQUATION__": equation,
        "__ARR__": f"{flows['arrivals_12m']:,}",
        "__DEP__": f"{flows['departures_12m']:,}",
        "__NETF__": f"{flows['net_12m']:+,}",
        "__CHURN__": f"{flows['churn_12m']:,}",
        "__CHURN_PCT__": f"{flows['churn_share_of_population_pct']}",
        "__ARR_CHG__": f"{abs(flows['arrivals_vs_prior_decade_pct'])}",
        "__DEP_CHG__": f"{abs(flows['departures_vs_prior_decade_pct'])}",
        "__FLOWQ__": f"{flows['validation']['quarters_checked']}",
        "__FLOWDIFF__": f"{flows['validation']['largest_difference']:g}",
        "__OWN_AGE__": own["life_stage"],
        "__OWNBARS__": ownbars,
        "__BIRTHBARS__": birthbars,
        "__CITATION__": ttam["citation"],
        "__MEASURE__": ttam["measure"],
        "__BASE__": ttam["base"],
        "__RESP__": f"{ttam['respondents_total']:,}",
        "__RESP_CUR__": f"{ttam['respondents_current_residents']:,}",
        "__LIMITS__": limits,
        "__DEPENDENCY__": dependency,
        "__VOLATILITY__": volatility,
        "__DECADES__": decades,
        "__RELEASE__": release_label(),
        "__BUILT__": date.today().strftime("%d %B %Y").lstrip("0"),
        "__REPO__": REPO,
        "__REPO_SHORT__": REPO.replace("https://", ""),
        "__DATA__": json.dumps(data, separators=(",", ":")),
    }.items():
        html = html.replace(token, value)

    (OUT / "dashboard.html").write_text(html)
    print(f"Dashboard -> {OUT / 'dashboard.html'} "
          f"({len(html) // 1024} KB)")

    # Second copy at the repository root, so GitHub Pages serves the dashboard
    # at the bare repository address rather than a long path ending in
    # outputs/dashboard.html. That short URL is what the poster QR code
    # encodes. It is written here rather than maintained by hand so the two
    # copies cannot drift apart.
    (ROOT / "index.html").write_text(html)
    print(f"GitHub Pages copy -> {ROOT / 'index.html'}")


if __name__ == "__main__":
    main()
