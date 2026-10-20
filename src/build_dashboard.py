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

TEMPLATE = """<title>Territory Population Equation</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Inter:wght@400;500;600&display=swap">
<style>
/* Layout: a stated headline, the long series, then the three supporting
   readings, then method. Palette is Territory ground: ochre-biased
   neutrals, with the three validated series hues carrying all the data. */
:root {
  --bg: #fbfaf7;
  --surface: #ffffff;
  --line: #e6e2d9;
  --ink: #1c1a16;
  --ink-2: #57524a;
  --ink-3: #8b857a;
  --ochre: #a8552a;
  --s-natural: #2a78d6;
  --s-overseas: #eb6834;
  --s-interstate: #1baf7a;
  --display: "Fraunces", Georgia, "Times New Roman", serif;
  --body: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #15140f;
    --surface: #1e1c16;
    --line: #322e25;
    --ink: #f3f0e8;
    --ink-2: #c0b9aa;
    --ink-3: #8b857a;
    --ochre: #d98a5c;
    --s-natural: #3987e5;
    --s-overseas: #ef7c4e;
    --s-interstate: #22c88b;
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #15140f;
  --surface: #1e1c16;
  --line: #322e25;
  --ink: #f3f0e8;
  --ink-2: #c0b9aa;
  --ink-3: #8b857a;
  --ochre: #d98a5c;
  --s-natural: #3987e5;
  --s-overseas: #ef7c4e;
  --s-interstate: #22c88b;
  color-scheme: dark;
}

* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: var(--body);
  font-size: 15px;
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
}
.wrap {
  max-width: 1120px;
  margin: 0 auto;
  padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px));
  padding-block: 40px 56px;
}
header { display: flex; flex-direction: column; gap: 6px; margin-bottom: 34px; }
.eyebrow {
  font-size: 11px; letter-spacing: .13em; text-transform: uppercase;
  color: var(--ochre); font-weight: 600;
}
h1 {
  font-family: var(--display); font-weight: 600;
  font-size: clamp(30px, 5vw, 46px); line-height: 1.08;
  margin: 0; text-wrap: balance; letter-spacing: -.015em;
}
.sub { color: var(--ink-2); max-width: 62ch; margin: 2px 0 0; }

.headline {
  display: flex; flex-wrap: wrap; align-items: baseline; gap: 10px 18px;
  padding: 22px 0 26px; border-bottom: 1px solid var(--line); margin-bottom: 30px;
}
.big {
  font-family: var(--display); font-size: clamp(54px, 11vw, 84px);
  line-height: .9; font-weight: 600; color: var(--s-overseas);
  font-variant-numeric: tabular-nums; letter-spacing: -.03em;
}
.big-say { max-width: 46ch; color: var(--ink-2); font-size: 15px; }
.big-say strong { color: var(--ink); font-weight: 600; }

/* The equation, drawn. Every bar is measured from a shared centre line, so
   the one component that subtracts points the other way and is impossible to
   misread. */
.eq { margin: 4px 0 0; }
.eq-row {
  display: grid; grid-template-columns: minmax(130px, 190px) 1fr 92px;
  align-items: center; gap: 8px 14px; padding: 5px 0;
}
.eq-name { font-size: 13.5px; color: var(--ink-2); }
.eq-track { position: relative; height: 17px; }
.eq-track::before {
  content: ""; position: absolute; left: 50%; top: -4px; bottom: -4px;
  width: 1px; background: var(--line);
}
.eq-fill { position: absolute; top: 0; height: 100%; border-radius: 3px; }
.eq-val {
  text-align: right; font-variant-numeric: tabular-nums;
  font-weight: 600; font-size: 14px;
}
.eq-row.total { border-top: 1px solid var(--line); margin-top: 6px; padding-top: 11px; }
.eq-row.total .eq-name, .eq-row.total .eq-val { color: var(--ink); font-weight: 600; }
.eq-row.total .eq-name { font-size: 14px; }
.eq-hint { color: var(--ink-3); font-size: 12.5px; margin: 10px 0 0; }

h2 {
  font-family: var(--display); font-weight: 600; font-size: 21px;
  margin: 0 0 4px; letter-spacing: -.01em;
}
.note { color: var(--ink-3); font-size: 13px; margin: 0 0 16px; max-width: 70ch; }
section { margin-bottom: 42px; }

.chartcard {
  background: var(--surface); border: 1px solid var(--line);
  border-radius: 10px; padding: 18px 16px 10px;
}
.legend { display: flex; flex-wrap: wrap; gap: 8px 20px; margin: 0 0 10px; }
.key { display: inline-flex; align-items: center; gap: 7px; font-size: 13px; color: var(--ink-2); }
.swatch { width: 15px; height: 3px; border-radius: 2px; flex: none; }
.plot { width: 100%; overflow-x: auto; }
svg { display: block; width: 100%; height: auto; }
.readout {
  display: flex; flex-wrap: wrap; gap: 4px 20px; min-height: 22px;
  font-size: 13px; color: var(--ink-2); font-variant-numeric: tabular-nums;
  padding: 6px 2px 2px;
}
.readout b { color: var(--ink); font-weight: 600; }

.grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(238px, 1fr)); }
.card {
  background: var(--surface); border: 1px solid var(--line);
  border-radius: 10px; padding: 18px; min-width: 0;
}
.card h3 {
  font-size: 12px; letter-spacing: .09em; text-transform: uppercase;
  color: var(--ink-3); font-weight: 600; margin: 0 0 14px;
}
.row { display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 10px; margin-bottom: 11px; }
.row:last-child { margin-bottom: 0; }
.row .lab { font-size: 13.5px; color: var(--ink-2); min-width: 0; }
.row .val { font-variant-numeric: tabular-nums; font-weight: 600; font-size: 14px; }
.bar { grid-column: 1 / -1; height: 5px; border-radius: 3px; background: var(--line); overflow: hidden; }
.bar > i { display: block; height: 100%; border-radius: 3px; }

table { border-collapse: collapse; width: 100%; font-size: 13.5px; }
th, td { text-align: right; padding: 7px 6px; border-bottom: 1px solid var(--line); }
th:first-child, td:first-child { text-align: left; }
th { color: var(--ink-3); font-weight: 600; font-size: 11.5px;
     letter-spacing: .07em; text-transform: uppercase; }
td { font-variant-numeric: tabular-nums; }
.tablewrap { overflow-x: auto; }

.check {
  display: inline-flex; align-items: center; gap: 8px; font-size: 13px;
  color: var(--ink-2); background: var(--surface); border: 1px solid var(--line);
  border-radius: 999px; padding: 7px 14px; font-variant-numeric: tabular-nums;
}
.dot { width: 7px; height: 7px; border-radius: 50%; background: var(--s-interstate); flex: none; }

.method { columns: 2 280px; column-gap: 34px; }
.method p { margin: 0 0 13px; break-inside: avoid; color: var(--ink-2); font-size: 14px; }
.method strong { color: var(--ink); font-weight: 600; }

footer {
  border-top: 1px solid var(--line); padding-top: 18px;
  font-size: 13px; color: var(--ink-3);
}
footer a { color: var(--ochre); }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>

<div class="wrap">
  <header>
    <div class="eyebrow">CDU IT Code Fair 2026 &middot; Northern Territory</div>
    <h1>The Territory&rsquo;s Population Equation</h1>
    <p class="sub">Population change has exactly three parts. For the Northern
    Territory one of them has been negative for __NIM_RUN__ straight quarters, and
    the Territory grows anyway. This tracks which part makes up the difference,
    and how steady that part is.</p>
  </header>

  <div class="headline">
    <div class="big">__NOM_SHARE__%</div>
    <div class="big-say">of the Territory&rsquo;s population growth in the year to
      __REF__ came from <strong>net overseas migration</strong>. Natural increase
      added __NI__, interstate migration subtracted __NIM_ABS__, and overseas
      migration added __NOM__, for total growth of __TOTAL__ on a population of
      __ERP__.</div>
  </div>

  <section>
    <h2>The equation</h2>
    <p class="note">Where the year&rsquo;s growth came from. Each bar is measured
      from the centre line, so the component that subtracts points the other way.</p>
    <div class="card">
      <div class="eq">__EQUATION__</div>
      <p class="eq-hint">Read it as arithmetic: the three parts add to the total,
        and that total matches the figure the ABS publishes separately.</p>
    </div>
  </section>

  <section>
    <h2>Forty-five years, three components</h2>
    <p class="note">Four-quarter rolling average, __START__ to __REF__. Above
      the zero line a component adds people; below it, the component subtracts
      them. Hover to read any quarter, or click to pin a quarter in place.</p>
    <div class="chartcard">
      <div class="plot"><svg id="chart" viewBox="0 0 1000 390" role="img"
        aria-label="Northern Territory population change by component, quarterly, 1982 to 2026"></svg></div>
      <div class="readout" id="readout"></div>
    </div>
  </section>

  <section>
    <h2>What the series says</h2>
    <p class="note">Three readings, each computed over the whole series rather
      than a chosen window.</p>
    <div class="grid">
      <div class="card">
        <h3>Reliance on overseas migration</h3>
        __DEPENDENCY__
      </div>
      <div class="card">
        <h3>Volatility of each component</h3>
        __VOLATILITY__
        <p class="note" style="margin:14px 0 0">Standard deviation over mean
          absolute value. Natural increase is steady; both migration components
          move several times more.</p>
      </div>
      <div class="card">
        <h3>Interstate migration, by decade</h3>
        <div class="tablewrap"><table>
          <thead><tr><th>Decade</th><th>Quarters positive</th><th>Mean/quarter</th></tr></thead>
          <tbody>__DECADES__</tbody>
        </table></div>
      </div>
    </div>
  </section>

  <section>
    <h2>Method</h2>
    <p class="note">
      <span class="check"><span class="dot"></span>
      Reconciliation passed: components sum to __RECON__, matching the change
      ABS publishes, difference __DIFF__.</span>
    </p>
    <div class="method">
      <p><strong>Decomposition.</strong> Quarterly components for the Northern
      Territory from ABS table 310102, __START__ to __REF__, __QUARTERS__
      quarters. Population level from table 310104.</p>
      <p><strong>Validation before reporting.</strong> Natural increase plus net
      interstate plus net overseas migration must equal the change ABS publishes
      for the same period. The pipeline checks this first and refuses to report
      a pass that is not one.</p>
      <p><strong>Volatility.</strong> Coefficient of variation against the mean
      absolute value, because interstate migration is mostly negative and a
      signed mean would make the measure meaningless.</p>
      <p><strong>Smoothing.</strong> The chart plots a four-quarter rolling
      average. Quarterly figures are noisy and the shape is what matters; raw
      values are in the repository.</p>
      <p><strong>What the estimates cannot do.</strong> Net overseas migration
      uses the 12-of-16-month rule, so a person can change category without
      changing address. Interstate movement is derived from administrative
      address records, so people who rarely update them are counted late or not
      at all. Census undercount is higher in the Territory than nationally,
      especially in remote communities.</p>
      <p><strong>Scope.</strong> This work is descriptive. It characterises the
      structure of population change and the uncertainty attached to
      forecasting it. It makes no policy recommendation.</p>
    </div>
  </section>

  <footer>
    Van Hoi (Hendrick) Dang &middot; Ngoc Ngan Le &middot; Phuong Vy Ho &middot; Thi Kim Anh Bui<br>
    Source: ABS, <i>National, state and territory population</i>, March 2026,
    tables 310102 and 310104. Code and data:
    <a href="__REPO__">__REPO_SHORT__</a>
  </footer>
</div>

<script>
const DATA = __DATA__;

const S = [
  { key: "natural_increase", label: "Natural increase", css: "--s-natural" },
  { key: "net_overseas_migration", label: "Net overseas migration", css: "--s-overseas" },
  { key: "net_interstate_migration", label: "Net interstate migration", css: "--s-interstate" },
];

const svg = document.getElementById("chart");
const readout = document.getElementById("readout");
const W = 1000, H = 390, M = { t: 14, r: 182, b: 30, l: 54 };
const dates = DATA.series.dates;
const n = dates.length;

let lo = Infinity, hi = -Infinity;
for (const s of S) for (const v of DATA.series[s.key]) { if (v < lo) lo = v; if (v > hi) hi = v; }
const pad = (hi - lo) * 0.06;
lo -= pad; hi += pad;

const px = i => M.l + (i / (n - 1)) * (W - M.l - M.r);
const py = v => M.t + (1 - (v - lo) / (hi - lo)) * (H - M.t - M.b);
const ink = n2 => getComputedStyle(document.documentElement).getPropertyValue(n2).trim();

function niceTicks(a, b, count) {
  const span = b - a, step0 = span / count;
  const mag = Math.pow(10, Math.floor(Math.log10(step0)));
  const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => s >= step0) || mag * 10;
  const out = [];
  for (let v = Math.ceil(a / step) * step; v <= b; v += step) out.push(Math.round(v));
  return out;
}

function draw() {
  const c = { line: ink("--line"), ink2: ink("--ink-2"), ink3: ink("--ink-3"), ink1: ink("--ink") };
  let out = "";

  for (const t of niceTicks(lo, hi, 6)) {
    const y = py(t).toFixed(1);
    out += `<line x1="${M.l}" y1="${y}" x2="${W - M.r}" y2="${y}" stroke="${c.line}" stroke-width="1"/>`;
    out += `<text x="${M.l - 9}" y="${y}" fill="${c.ink3}" font-size="11.5" text-anchor="end" dominant-baseline="middle">${t.toLocaleString()}</text>`;
  }
  out += `<line x1="${M.l}" y1="${py(0).toFixed(1)}" x2="${W - M.r}" y2="${py(0).toFixed(1)}" stroke="${c.ink2}" stroke-width="1.5"/>`;

  for (let i = 0; i < n; i++) {
    const y = dates[i].slice(0, 4);
    if (y % 5 === 0 && dates[i].slice(5) === "03") {
      out += `<text x="${px(i).toFixed(1)}" y="${H - 10}" fill="${c.ink3}" font-size="11.5" text-anchor="middle">${y}</text>`;
    }
  }

  for (const s of S) {
    const vals = DATA.series[s.key];
    const d = vals.map((v, i) => `${i ? "L" : "M"}${px(i).toFixed(1)} ${py(v).toFixed(1)}`).join(" ");
    out += `<path d="${d}" fill="none" stroke="${ink(s.css)}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>`;
    out += `<text x="${(W - M.r + 10).toFixed(1)}" y="${py(vals[n - 1]).toFixed(1)}" fill="${c.ink2}" font-size="12.5" dominant-baseline="middle">${s.label}</text>`;
  }

  out += `<g id="hover" style="display:none"><line id="hl" y1="${M.t}" y2="${H - M.b}" stroke="${c.ink3}" stroke-width="1" stroke-dasharray="3 3"/>`;
  for (const s of S) out += `<circle class="hdot" r="4.5" fill="${ink(s.css)}" stroke="${ink("--surface")}" stroke-width="2"/>`;
  out += `</g>`;

  svg.innerHTML = out;
  showAt(n - 1);
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
    `<span>${s.label} <b>${Math.round(DATA.series[s.key][i]).toLocaleString()}</b></span>`).join("")
    + (pinned !== null ? `<span style="color:var(--ochre)">pinned &middot; click to release</span>` : "");
}

let pinned = null;

function fromEvent(e) {
  if (pinned !== null) return;
  const r = svg.getBoundingClientRect();
  const x = ((e.touches ? e.touches[0].clientX : e.clientX) - r.left) / r.width * W;
  const i = Math.round((x - M.l) / (W - M.l - M.r) * (n - 1));
  if (i >= 0 && i < n) showAt(i);
}
svg.addEventListener("mousemove", fromEvent);
svg.addEventListener("touchmove", e => { fromEvent(e); e.preventDefault(); }, { passive: false });
svg.addEventListener("mouseleave", () => { if (pinned === null) showAt(n - 1); });
svg.addEventListener("click", e => {
  if (pinned !== null) { pinned = null; fromEvent(e); return; }
  const r = svg.getBoundingClientRect();
  const x = (e.clientX - r.left) / r.width * W;
  const i = Math.round((x - M.l) / (W - M.l - M.r) * (n - 1));
  if (i >= 0 && i < n) { pinned = i; showAt(i); }
});

draw();
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

    # The equation as a centre-origin bar chart: every component is measured
    # against the largest absolute contribution, so the single negative one
    # reads as a subtraction rather than just a minus sign.
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
            f'<div class="eq-row"><span class="eq-name">{label}</span>'
            f'<span class="eq-track"><i class="eq-fill" style="{side};'
            f'background:var({hue})"></i></span>'
            f'<span class="eq-val">{value:+,}</span></div>'
        )
    rows.append(
        f'<div class="eq-row total"><span class="eq-name">Total growth</span>'
        f'<span class="eq-track"></span>'
        f'<span class="eq-val">{f["total_growth_12m"]:+,}</span></div>'
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
