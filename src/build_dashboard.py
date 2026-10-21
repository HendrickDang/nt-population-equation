"""
Builds outputs/dashboard.html from the pipeline's outputs.

The page is self-contained: the quarterly series is embedded, so it opens
from a file, a web host, or an artifact link with nothing to fetch. Re-run
this after the pipeline whenever a new ABS release is loaded.

    python src/build_dashboard.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"

REPO = "https://github.com/HendrickDang/nt-population-equation"

TEMPLATE = """<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Territory Population Equation</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
<style>
/* Phone first. One column, big numbers, every figure captioned in plain words.
   The three series hues are the project's validated set and carry all the data;
   everything else is ink and surface. */
:root {
  --bg: #fbfaf8;
  --surface: #ffffff;
  --surface-2: #f4f2ee;
  --line: #e4e0d8;
  --ink: #17161300;
  --ink: #171613;
  --ink-2: #55504a;
  --ink-3: #87817a;
  --accent: #a8552a;
  --s-natural: #2a78d6;
  --s-overseas: #eb6834;
  --s-interstate: #1baf7a;
  --radius: 14px;
  --body: "Inter", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #121110; --surface: #1a1916; --surface-2: #232019; --line: #322e27;
    --ink: #f4f1ea; --ink-2: #bdb6ab; --ink-3: #8b857c; --accent: #e09a6d;
    --s-natural: #4a90ea; --s-overseas: #e26a35; --s-interstate: #19ad76;
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #121110; --surface: #1a1916; --surface-2: #232019; --line: #322e27;
  --ink: #f4f1ea; --ink-2: #bdb6ab; --ink-3: #8b857c; --accent: #e09a6d;
  --s-natural: #4a90ea; --s-overseas: #e26a35; --s-interstate: #19ad76;
  color-scheme: dark;
}

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
  display: grid; gap: 10px; margin-bottom: 36px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
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

/* ---- the equation ------------------------------------------------------ */
.eq-row { padding: 11px 0; border-bottom: 1px solid var(--line); }
.eq-row:first-child { padding-top: 2px; }
.eq-top { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; margin-bottom: 7px; }
.eq-name { font-size: 14.5px; color: var(--ink); font-weight: 500; }
.eq-val { font-size: 16px; font-weight: 700; letter-spacing: -.02em; font-variant-numeric: tabular-nums; }
.eq-track { position: relative; height: 14px; }
.eq-track::before {
  content: ""; position: absolute; left: 50%; top: -2px; bottom: -2px;
  width: 1px; background: var(--line);
}
.eq-fill { position: absolute; top: 0; height: 100%; border-radius: 4px; }
.eq-total {
  display: flex; justify-content: space-between; align-items: baseline;
  gap: 12px; padding-top: 14px;
}
.eq-total .eq-name { font-weight: 700; font-size: 15.5px; }
.eq-total .eq-val { font-size: 22px; }
.eq-key { font-size: 12.5px; color: var(--ink-3); margin-top: 4px; }

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
  <header>
    <div class="eyebrow">CDU IT Code Fair 2026 &middot; Northern Territory</div>
    <h1>The Territory&rsquo;s Population Equation</h1>
    <p class="standfirst">Population change has exactly three parts. In the
      Northern Territory one of them has been negative for __NIM_RUN__ straight
      quarters, and the population grows anyway. This page shows which part makes
      up the difference, and how steady that part is.</p>
  </header>

  <div class="hero">
    <div class="hero-fig">__NOM_SHARE__%</div>
    <div class="hero-say">Nine in every ten people added to the Territory last
      year arrived from overseas.</div>
    <div class="hero-sub">Net overseas migration supplied __NOM_SHARE__% of all
      population growth in the year to __REF__. A decade ago the same measure was
      __DEP10__%.</div>
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

  <section>
    <h2>Where the growth came from</h2>
    <p class="note">The year&rsquo;s change, split into its three parts. Bars run
      from the centre line: to the right a part adds people, to the left it takes
      them away.</p>
    <div class="card">
      __EQUATION__
      <p class="meaning">Only one part subtracts. Overseas migration is large
        enough to cover that loss and still leave the Territory growing, which is
        why the total is positive at all.</p>
    </div>
  </section>

  <section>
    <h2>Forty-five years of the same three parts</h2>
    <p class="note">Four-quarter rolling average, __START__ to __REF__. Above the
      zero line a part adds people; below it, the part takes them away. Tap or
      hover the chart to read any quarter, and tap again to hold it.</p>
    <div class="card">
      <div class="legend">
        <span class="key"><span class="swatch" style="background:var(--s-natural)"></span>Natural increase</span>
        <span class="key"><span class="swatch" style="background:var(--s-overseas)"></span>Net overseas migration</span>
        <span class="key"><span class="swatch" style="background:var(--s-interstate)"></span>Net interstate migration</span>
      </div>
      <svg id="chart" role="img"
        aria-label="Northern Territory population change by component, quarterly, 1982 to 2026"></svg>
      <div class="readout" id="readout"></div>
      <p class="meaning">The blue line barely moves: births minus deaths is the
        Territory&rsquo;s steady part. The other two swing hard, and the green one
        has spent most of the last forty years below zero.</p>
    </div>
  </section>

  <section>
    <h2>Three readings</h2>
    <p class="note">Each computed over the whole series rather than a window
      chosen to suit the argument.</p>
    <div class="grid">
      <div class="card">
        <h3>Reliance on overseas migration</h3>
        __DEPENDENCY__
        <p class="meaning">The share is climbing. What was about three quarters of
          growth over a decade is now nine tenths of it.</p>
      </div>
      <div class="card">
        <h3>How much each part moves</h3>
        __VOLATILITY__
        <p class="meaning">Standard deviation over mean absolute value. Higher
          means less predictable. Natural increase is close to flat; both
          migration parts move several times more, and interstate migration moves
          most of all.</p>
      </div>
      <div class="card">
        <h3>Interstate migration by decade</h3>
        <table>
          <thead><tr><th>Decade</th><th>Qtrs positive</th><th>Mean/qtr</th></tr></thead>
          <tbody>__DECADES__</tbody>
        </table>
        <p class="meaning">The Territory used to gain people from other states
          about half the time. In the 2010s that fell to eight per cent.</p>
      </div>
    </div>
  </section>

  <section>
    <h2>How these numbers were produced</h2>
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
let W, H, M, narrow;
function layout() {
  narrow = window.innerWidth < 700;
  if (narrow) { W = 360; H = 420; M = { t: 10, r: 10, b: 26, l: 38 }; }
  else        { W = 1000; H = 400; M = { t: 14, r: 186, b: 30, l: 56 }; }
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
    if (!narrow) {
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

draw();
let rt;
addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(draw, 120); });
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", draw);
new MutationObserver(draw).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
</script>
"""


def main() -> None:
    f = json.loads((OUT / "figures.json").read_text())
    data = json.loads((OUT / "dashboard_data.json").read_text())

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

    # The equation as a centre-origin bar chart. Label and value sit above the
    # bar rather than beside it, so the row survives a phone's width without
    # squeezing the bar into nothing.
    parts = [
        ("Natural increase", f["natural_increase_12m"], "--s-natural"),
        ("Net overseas migration", f["net_overseas_migration_12m"], "--s-overseas"),
        ("Net interstate migration", f["net_interstate_migration_12m"], "--s-interstate"),
    ]
    scale = max(abs(v) for _, v, _ in parts) or 1
    rows = []
    for label, value, hue in parts:
        pct = abs(value) / scale * 50
        side = f"left:50%;width:{pct:.1f}%" if value >= 0 else f"right:50%;width:{pct:.1f}%"
        rows.append(
            f'<div class="eq-row">'
            f'<div class="eq-top"><span class="eq-name">{label}</span>'
            f'<span class="eq-val" style="color:var({hue})">{value:+,}</span></div>'
            f'<div class="eq-track"><i class="eq-fill" style="{side};'
            f'background:var({hue})"></i></div></div>'
        )
    rows.append(
        f'<div class="eq-total"><span class="eq-name">Total growth</span>'
        f'<span class="eq-val">{f["total_growth_12m"]:+,}</span></div>'
        f'<div class="eq-key">Matches the change the ABS publishes separately, '
        f'to the person.</div>'
    )
    equation = "".join(rows)

    decades = "".join(
        f"<tr><td>{d}s</td><td>{v['positive_pct']}%</td>"
        f"<td>{v['mean_per_quarter']:,}</td></tr>"
        for d, v in f["nim_by_decade"].items()
    )

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
        "__DEPENDENCY__": dependency,
        "__VOLATILITY__": volatility,
        "__DECADES__": decades,
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
