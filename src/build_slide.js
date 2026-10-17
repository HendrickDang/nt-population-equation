/*
 * Builds the single static PowerPoint slide for the Research Competition.
 *
 * Rules the slide must obey (CDU IT Code Fair 2026, 3MT format):
 *   one slide, no animation, no transitions, no audio or video.
 *
 * The 3MT guidance is that the slide supports the speech rather than carrying
 * it, so no figure printed here is one a speaker says aloud. The chart shows
 * shape; the speakers supply the numbers.
 *
 *   node src/build_slide.js
 */

const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, "outputs");
const f = JSON.parse(fs.readFileSync(path.join(OUT, "figures.json"), "utf8"));

const THEME = {
  name: "NT Population Equation",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "16181C", lt1: "FCFCFB",
    dk2: "52514E", lt2: "E8E7E3",
    accent1: "2A78D6", accent2: "EB6834", accent3: "1BAF7A",
    accent4: "6F6E6A", accent5: "C9C8C4", accent6: "0B0B0B",
    hlink: "2A78D6", folHlink: "6250D6",
  },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";            // 10" x 5.625"
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.author = "Van Hoi (Hendrick) Dang";
pres.title = "The Territory's Population Equation";

const C = pres.SchemeColor;

pres.defineSlideMaster({
  title: "RESEARCH_SLIDE",
  background: { color: THEME.colors.lt1 },
  objects: [
    {
      placeholder: {
        options: {
          name: "title", type: "title",
          x: 0.5, y: 0.34, w: 9.0, h: 0.52,
          fontSize: 30, bold: true, color: C.text1, margin: 0,
        },
        text: "",
      },
    },
    {
      placeholder: {
        options: {
          name: "subtitle", type: "body",
          x: 0.5, y: 0.86, w: 9.0, h: 0.3,
          fontSize: 14, color: C.text2, margin: 0,
        },
        text: "",
      },
    },
    {
      placeholder: {
        options: {
          name: "footer", type: "body",
          x: 0.5, y: 5.06, w: 9.0, h: 0.34,
          fontSize: 9, color: THEME.colors.accent4, margin: 0,
        },
        text: "",
      },
    },
  ],
});

const slide = pres.addSlide({ masterName: "RESEARCH_SLIDE" });

slide.addText("The Territory's Population Equation", { placeholder: "title" });

slide.addText(
  `Northern Territory population change by component, ` +
  `${f.series_start} to ${f.reference_period}`,
  { placeholder: "subtitle" },
);

// The chart is the slide. Everything else is a caption.
slide.addImage({
  path: path.join(OUT, "components_slide.png"),
  x: 0.42, y: 1.24, w: 9.16, h: 3.77,
  objectName: "componentsChart",
});

slide.addText(
  [
    {
      text: "Van Hoi (Hendrick) Dang  ·  Ngoc Ngan Le  ·  Phuong Vy Ho  ·  Thi Kim Anh Bui",
      options: { breakLine: true },
    },
    {
      text:
        "Four-quarter rolling average. Source: ABS, National, state and territory " +
        "population, tables 310102 and 310104 (March 2026).  " +
        "Code and data: github.com/HendrickDang/nt-population-equation",
      options: { fontSize: 8, color: THEME.colors.accent5 === undefined ? "6F6E6A" : "6F6E6A" },
    },
  ],
  { placeholder: "footer" },
);

slide.addNotes(
  "One static slide. No animation, no transitions, no audio or video.\n" +
  "Figures are spoken, not printed: overseas migration accounted for " +
  `${f.nom_share_of_growth_pct}% of growth in the year to ${f.reference_period}.`
);

pres.writeFile({ fileName: path.join(OUT, "RES003_population_equation_slide.pptx") })
  .then(async () => {
    const { applyTheme } = require(
      "/root/.claude/skills/synced/e15b6dca-e10c-4ff4-8122-2af941d18169_bf341102-e215-4b50-83a0-e1221ef0b088/pptx/scripts/apply_theme.js"
    );
    await applyTheme(path.join(OUT, "RES003_population_equation_slide.pptx"), THEME);
    console.log("Slide written to outputs/RES003_population_equation_slide.pptx");
  });
