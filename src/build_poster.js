/*
 * Builds the A1 poster for the CDU IT Code Fair 2026 Poster Competition.
 *
 * A1 is 594 x 841 mm = 23.39 x 33.11 inches, portrait. CDU prints from the
 * PDF we submit, so the .pptx is the editable source and the PDF is what
 * gets uploaded.
 *
 * Judges assess the poster alone, with no spoken explanation, so the poster
 * has to carry the argument by itself: required sections in order, one hero
 * chart, three supporting readings, and a QR to the code.
 *
 *   node src/build_poster.js
 */

const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, "outputs");
const f = JSON.parse(fs.readFileSync(path.join(OUT, "figures.json"), "utf8"));

const W = 23.39, H = 33.11;            // A1 portrait, inches
const M = 1.15;                         // outer margin
const GUT = 0.62;                       // gutter between columns
const COLW = (W - 2 * M - 2 * GUT) / 3; // three-column grid

const THEME = {
  name: "NT Population Equation Poster",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "16181C", lt1: "FCFCFB",
    dk2: "52514E", lt2: "F2F0EB",
    accent1: "2A78D6", accent2: "EB6834", accent3: "1BAF7A",
    accent4: "A8552A", accent5: "8B857A", accent6: "0B0B0B",
    hlink: "2A78D6", folHlink: "6250D6",
  },
};

const INK = "16181C", INK2 = "52514E", INK3 = "8B857A";
const OCHRE = "A8552A", OVERSEAS = "EB6834", PANEL = "F2F0EB", LINE = "E0DCD3";

const pres = new pptxgen();
pres.defineLayout({ name: "A1", width: W, height: H });
pres.layout = "A1";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.author = "Van Hoi (Hendrick) Dang";
pres.title = "The Territory's Population Equation";

const slide = pres.addSlide();
slide.background = { color: "FCFCFB" };

const col = i => M + i * (COLW + GUT);
let y = M;

/* ---------- Title block ------------------------------------------------ */

slide.addText("CDU IT CODE FAIR 2026   ·   POSTER COMPETITION   ·   POS006", {
  x: M, y, w: W - 2 * M, h: 0.34, fontSize: 15, bold: true,
  color: OCHRE, charSpacing: 2.4, isTextBox: true, margin: 0,
});
y += 0.52;

slide.addText("The Territory's Population Equation", {
  x: M, y, w: W - 2 * M, h: 1.5, fontSize: 76, bold: true, color: INK,
  fontFace: "Cambria", isTextBox: true, margin: 0,
});
y += 1.6;

slide.addText(
  "Where Northern Territory population growth comes from, and which component makes forecasting it hardest",
  { x: M, y, w: W - 2 * M, h: 0.62, fontSize: 25, color: INK2, isTextBox: true, margin: 0 },
);
y += 0.82;

slide.addText(
  "Van Hoi (Hendrick) Dang  ·  Ngoc Ngan Le  ·  Phuong Vy Ho  ·  Thi Kim Anh Bui    |    " +
  "Master of Data Science, Faculty of Science and Technology, Charles Darwin University",
  { x: M, y, w: W - 2 * M, h: 0.4, fontSize: 15.5, color: INK3, isTextBox: true, margin: 0 },
);
y += 0.62;

slide.addShape(pres.ShapeType.rect, {
  x: M, y, w: W - 2 * M, h: 0.022, fill: { color: INK },
});
y += 0.44;

/* ---------- Headline figure ------------------------------------------- */

const headlineH = 2.26;
slide.addShape(pres.ShapeType.roundRect, {
  x: M, y, w: W - 2 * M, h: headlineH, rectRadius: 0.1,
  fill: { color: PANEL }, line: { color: LINE, width: 1 },
});
slide.addText(`${f.nom_share_of_growth_pct}%`, {
  x: M + 0.5, y: y + 0.22, w: 5.1, h: 1.82, fontSize: 118, bold: true,
  color: OVERSEAS, fontFace: "Cambria", align: "left", valign: "middle",
  isTextBox: true, margin: 0,
});
slide.addText([
  { text: "of the Northern Territory's population growth in the year to " +
          `${f.reference_period} came from net overseas migration.`,
    options: { bold: true, breakLine: true } },
  { text: `Natural increase added ${f.natural_increase_12m.toLocaleString()}. ` +
          `Interstate migration subtracted ${Math.abs(f.net_interstate_migration_12m).toLocaleString()}. ` +
          `Overseas migration added ${f.net_overseas_migration_12m.toLocaleString()}. ` +
          `Total growth ${f.total_growth_12m.toLocaleString()}, on a population of ${f.erp_latest.toLocaleString()}.`,
    options: { bold: false, color: INK2 } },
], {
  x: M + 5.9, y: y + 0.3, w: W - 2 * M - 6.5, h: 1.66, fontSize: 22,
  color: INK, lineSpacing: 30, valign: "middle", isTextBox: true, margin: 0,
});
y += headlineH + 0.5;

/* ---------- Row 1: Abstract | Background | Objectives ------------------ */

const sectionTitle = (text, x, yy, w) => {
  slide.addText(text.toUpperCase(), {
    x, y: yy, w, h: 0.34, fontSize: 15, bold: true, color: OCHRE,
    charSpacing: 2.2, isTextBox: true, margin: 0,
  });
  return yy + 0.46;
};

const body = (text, x, yy, w, h, opts = {}) => {
  slide.addText(text, {
    x, y: yy, w, h, fontSize: opts.fontSize || 17, color: opts.color || INK,
    lineSpacing: opts.lineSpacing || 24, valign: "top", isTextBox: true,
    margin: 0, ...(opts.extra || {}),
  });
  return yy + h;
};

const ROW1 = 7.72, RESULTS = 15.10, FIGS = 23.05, BOTTOM = 26.65;

const rowTop = ROW1;
let ry = sectionTitle("Abstract", col(0), rowTop, COLW);
body(
  `The Northern Territory is the only Australian jurisdiction that loses residents ` +
  `to other states while still growing. This project asked how much of that growth ` +
  `comes from each of the three components of population change, and how reliable ` +
  `those estimates are. Quarterly components for the NT were extracted from ABS ` +
  `table 310102, ${f.series_start} to ${f.reference_period} (${f.quarters_in_series} ` +
  `quarters), and reconciled against the published change before analysis. In the ` +
  `latest twelve months net overseas migration accounted for ` +
  `${f.nom_share_of_growth_pct}% of growth, up from ${f.overseas_dependency["10y"]}% ` +
  `across the last decade. Net interstate migration has been negative for ` +
  `${f.nim_consecutive_negative} consecutive quarters, and was positive in only ` +
  `${f.nim_by_decade["2010"].positive_pct}% of quarters in the 2010s against ` +
  `${f.nim_by_decade["1980"].positive_pct}% in the 1980s. Both migration components ` +
  `are far more volatile than natural increase. Territory population growth now ` +
  `rests on its least stable inputs. The analysis is descriptive and makes no ` +
  `policy recommendation.`,
  col(0), ry, COLW, 5.5, { fontSize: 16.5, lineSpacing: 23 },
);

ry = sectionTitle("Background", col(1), rowTop, COLW);
body(
  "The Northern Territory plans schools, hospitals and housing from population " +
  "forecasts. A forecast is only as stable as the parts it is built from.\n\n" +
  "Population change has exactly three components:\n\n" +
  "change  =  natural increase  +  net interstate migration  +  net overseas migration\n\n" +
  "The ABS publishes all three every quarter, for every state and territory. What " +
  "is not published is how much of the Territory's growth each component carries, " +
  "or how steady each one is. Those two questions decide how much confidence a " +
  "planner can place in a headline growth figure.",
  col(1), ry, COLW, 6.4, { fontSize: 16.5, lineSpacing: 23 },
);

ry = sectionTitle("Objectives", col(2), rowTop + 3.85, COLW);
slide.addText([
  { text: "Quantify the contribution of each component to NT population growth, "
          + `${f.series_start} to ${f.reference_period}.`, options: { bullet: true, breakLine: true } },
  { text: "Measure the volatility of each component across the full series.",
    options: { bullet: true, breakLine: true } },
  { text: "Determine whether growth depends on the components that are least stable.",
    options: { bullet: true, breakLine: true } },
  { text: "Validate every figure against the change ABS publishes, before reporting it.",
    options: { bullet: true } },
], {
  x: col(2), y: ry, w: COLW, h: 2.90, fontSize: 16.5, color: INK,
  lineSpacing: 25, paraSpaceAfter: 12, isTextBox: true, margin: 0,
});

let my = sectionTitle("Methodology", col(2), rowTop, COLW);
slide.addText([
  { text: "Source. ", options: { bold: true } },
  { text: "ABS tables 310102 (components) and 310104 (population), March 2026.\n", options: {} },
  { text: "Extract. ", options: { bold: true } },
  { text: "Python pipeline locates the NT columns by header text, so an ABS layout change fails loudly rather than silently.\n", options: {} },
  { text: "Validate. ", options: { bold: true } },
  { text: `Components must sum to the published change. They do, exactly: ${f.reconciliation.components_sum.toLocaleString()} against ${f.reconciliation.abs_published_change.toLocaleString()}.\n`, options: {} },
  { text: "Measure. ", options: { bold: true } },
  { text: "Coefficient of variation against mean absolute value, because interstate migration is mostly negative.\n", options: {} },
  { text: "Reproduce. ", options: { bold: true } },
  { text: "One command re-runs everything when the next quarter publishes.", options: {} },
], {
  x: col(2), y: my, w: COLW, h: 3.40, fontSize: 16.5, color: INK,
  lineSpacing: 23, valign: "top", isTextBox: true, margin: 0,
});

y = RESULTS;

/* ---------- Results ----------------------------------------------------- */

y = sectionTitle("Results", M, y, W - 2 * M);

slide.addText(
  "Natural increase is steady and slowly declining. Overseas migration has become " +
  "the Territory's engine of growth. Interstate migration has spent most of the " +
  "last fifteen years below zero.",
  { x: M, y, w: W - 2 * M, h: 0.74, fontSize: 18, color: INK2,
    lineSpacing: 25, isTextBox: true, margin: 0 },
);
y += 0.80;

slide.addImage({
  path: path.join(OUT, "poster_components.png"),
  x: M, y, w: W - 2 * M, h: 6.18, objectName: "componentsChart",
});
y += 6.18;

slide.addText(
  `Northern Territory population change by component. Four-quarter rolling average, ` +
  `${f.series_start} to ${f.reference_period}. Source: ABS table 310102.`,
  { x: M, y: y + 0.08, w: W - 2 * M, h: 0.34, fontSize: 14, color: INK3,
    isTextBox: true, margin: 0 },
);
y = FIGS;

const figW = COLW, figH = 3.55;
[["poster_dependency.png", 0], ["poster_volatility.png", 1], ["poster_decades.png", 2]]
  .forEach(([file, i]) => {
    slide.addImage({ path: path.join(OUT, file), x: col(i), y, w: figW, h: figH,
                     objectName: file.replace(".png", "") });
  });
y = BOTTOM;

/* ---------- Conclusions | Limitations | QR ----------------------------- */

const lastTop = y;
const WIDE = COLW * 2 + GUT;

let cy = sectionTitle("Conclusions", col(0), lastTop, WIDE);
slide.addText([
  { text: `Overseas migration now carries ${f.nom_share_of_growth_pct}% of the Territory's growth, `
        + `up from ${f.overseas_dependency["5y"]}% over five years and ${f.overseas_dependency["10y"]}% over ten. `
        + `The reliance is increasing, not steady.`,
    options: { bullet: true, breakLine: true } },
  { text: `The interstate deficit is recent. Net interstate migration was positive in `
        + `${f.nim_by_decade["1980"].positive_pct}% of quarters in the 1980s and `
        + `${f.nim_by_decade["2010"].positive_pct}% in the 2010s, and has been negative for `
        + `${f.nim_consecutive_negative} straight quarters since ${f.nim_last_positive}.`,
    options: { bullet: true, breakLine: true } },
  { text: `Natural increase is the only steady component (coefficient of variation `
        + `${f.volatility.natural_increase.toFixed(2)}). Interstate (`
        + `${f.volatility.net_interstate_migration.toFixed(2)}) and overseas (`
        + `${f.volatility.net_overseas_migration.toFixed(2)}) migration are roughly eight times more variable.`,
    options: { bullet: true, breakLine: true } },
  { text: "Territory growth has shifted onto its least stable inputs, so forecast uncertainty "
        + "now sits in the migration components. A single headline growth rate does not show this.",
    options: { bullet: true } },
], {
  x: col(0), y: cy, w: WIDE, h: 3.00, fontSize: 16.5, color: INK,
  lineSpacing: 23, paraSpaceAfter: 9, valign: "top", isTextBox: true, margin: 0,
});

let ly = sectionTitle("Limitations", col(0), lastTop + 3.60, WIDE);
slide.addText(
  "Net overseas migration uses the 12-of-16-month rule, so a person can change category without " +
  "changing address. Interstate movement is derived from administrative address records, so people " +
  "who rarely update them are counted late or not at all. Census undercount is higher in the Territory " +
  "than nationally, particularly in remote communities, and estimated resident population is rebased " +
  "after each Census. These remain estimates, and this project treats them as such.",
  { x: col(0), y: ly, w: WIDE, h: 1.15, fontSize: 15.5, color: INK2,
    lineSpacing: 21, isTextBox: true, margin: 0 },
);

let qy = sectionTitle("Code and data", col(2), lastTop, COLW);
slide.addImage({ path: path.join(OUT, "qr_repo.png"), x: col(2), y: qy, w: 2.35, h: 2.35,
                 objectName: "qrRepo" });
slide.addText(
  "Every figure on this poster is produced by the pipeline in this repository, from the " +
  "ABS files cited below. Scan for the code, the cleaned series and an interactive version " +
  "of the chart above.",
  { x: col(2) + 2.6, y: qy + 0.02, w: COLW - 2.6, h: 2.3, fontSize: 14.5,
    color: INK2, lineSpacing: 20, isTextBox: true, margin: 0 },
);
slide.addText("github.com/HendrickDang/nt-population-equation", {
  x: col(2), y: qy + 2.5, w: COLW, h: 0.34, fontSize: 14.5, bold: true, color: OCHRE,
  isTextBox: true, margin: 0,
});

const ry2 = sectionTitle("References", col(2), lastTop + 3.60, COLW);
slide.addText(
  "Australian Bureau of Statistics. (2026). National, state and territory population, " +
  "March 2026 [Data set]. abs.gov.au\n" +
  "Northern Territory Government. (2026). Population. NT Economy. nteconomy.nt.gov.au",
  { x: col(2), y: ry2, w: COLW, h: 1.32, fontSize: 14, color: INK2,
    lineSpacing: 19, isTextBox: true, margin: 0 },
);

pres.writeFile({ fileName: path.join(OUT, "POS006_population_equation_poster_A1.pptx") })
  .then(async () => {
    const { applyTheme } = require(
      "/root/.claude/skills/synced/e15b6dca-e10c-4ff4-8122-2af941d18169_bf341102-e215-4b50-83a0-e1221ef0b088/pptx/scripts/apply_theme.js"
    );
    await applyTheme(path.join(OUT, "POS006_population_equation_poster_A1.pptx"), THEME);
    console.log("Poster -> outputs/POS006_population_equation_poster_A1.pptx");
  });
