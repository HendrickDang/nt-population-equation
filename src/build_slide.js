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

// Colours are written as literal hex rather than theme scheme colours, so the
// script needs nothing outside this repository to produce a correctly styled
// deck on any machine.
const PALETTE = {
  bg: "FCFCFB",
  ink: "16181C",
  ink2: "52514E",
  ink3: "6F6E6A",
};

const FONTS = { headFontFace: "Cambria", bodyFontFace: "Calibri" };

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";            // 10" x 5.625"
pres.theme = FONTS;
pres.author = "Van Hoi (Hendrick) Dang";
pres.title = "The Territory's Population Equation";

pres.defineSlideMaster({
  title: "RESEARCH_SLIDE",
  background: { color: PALETTE.bg },
  objects: [
    {
      placeholder: {
        options: {
          name: "title", type: "title",
          x: 0.5, y: 0.34, w: 9.0, h: 0.52,
          fontSize: 30, bold: true, color: PALETTE.ink, margin: 0,
        },
        text: "",
      },
    },
    {
      placeholder: {
        options: {
          name: "subtitle", type: "body",
          x: 0.5, y: 0.86, w: 9.0, h: 0.3,
          fontSize: 14, color: PALETTE.ink2, margin: 0,
        },
        text: "",
      },
    },
    {
      placeholder: {
        options: {
          name: "footer", type: "body",
          x: 0.5, y: 5.06, w: 9.0, h: 0.34,
          fontSize: 9, color: PALETTE.ink3, margin: 0,
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
      options: { fontSize: 8, color: PALETTE.ink3 },
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
  .then(() => console.log("Slide -> outputs/RES003_population_equation_slide.pptx"));
