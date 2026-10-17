# The Territory's Population Equation

Where Northern Territory population growth comes from, and which component
makes forecasting it hardest.

**CDU IT Code Fair 2026** | Research Competition (RES003) and Poster
Competition (POS006)
Van Hoi (Hendrick) Dang, Ngoc Ngan Le, Phuong Vy Ho, Thi Kim Anh Bui

---

## The question

The Northern Territory plans schools, hospitals and housing from population
forecasts. A forecast is only as stable as the parts it is built from.

Population change has exactly three components:

```
change  =  natural increase  +  net interstate migration  +  net overseas migration
```

The NT is the only Australian jurisdiction that loses residents to other
states while still growing. This project asks which component makes up the
difference, how that has shifted, and which component carries the forecast
risk.

## Findings

ABS release of March 2026. Series: June 1981 to March 2026, 180 quarters.

![NT population change by component](outputs/components.png)

**Net overseas migration accounted for 90.4% of the Territory's population
growth in the year to March 2026.** Natural increase added 1,969, interstate
migration subtracted 1,589, and overseas migration added 3,585, for total
growth of 3,965 on a population of 268,899.

**That reliance is rising**, not steady: 74.4% across the last ten years,
84.5% across five, 90.4% across twelve months.

**The interstate deficit is recent.** Net interstate migration was positive in
49% of quarters during the 1980s and 8% during the 2010s. It has been negative
for 18 consecutive quarters, since September 2021.

**Growth has shifted onto the least stable inputs.** Natural increase is the
only steady component, with a coefficient of variation of 0.13. Interstate
migration is 1.14 and overseas migration 0.96, roughly eight times more
variable. Forecast uncertainty is therefore concentrated in the migration
components, which a single headline growth rate does not reveal.

**The components reconcile exactly.** They sum to 3,965 against the 3,965 the
ABS publishes for the same period, a difference of zero. The headline figure
is arithmetic, not an estimate of ours.

## What this repository does

1. Reads ABS tables 310102 and 310104, quarterly, Northern Territory only.
2. Decomposes population change into the three components.
3. **Validates** that they reconcile against the published change in estimated
   resident population. If they do not, the pipeline says so rather than
   reporting a number nobody checked.
4. Measures the volatility of each component across the full series.
5. Writes the headline figures, the cleaned series, the chart images and an
   interactive dashboard.

The analysis is a pipeline rather than a report. The ABS revises these tables
every quarter; re-running three commands against a newer download reproduces
every figure in the project.

The slide and the poster are laid out separately. This repository supplies the
numbers and the finished chart images that go into them.

## Getting the data

The ABS files are not committed, because shipping a snapshot means shipping
one that silently goes stale.

1. Open [ABS, National, state and territory population](https://www.abs.gov.au/statistics/people/population/national-state-and-territory-population/latest-release)
2. Download **310102** (components of population change) and **310104**
   (estimated resident population)
3. Save them as `data/raw/310102.xlsx` and `data/raw/310104.xlsx`

Licensed CC BY 4.0 by the Australian Bureau of Statistics.

## Running it

Python 3.9 or newer.

```bash
pip install -r requirements.txt

python src/pipeline.py              # analysis, headline figures, main chart
python src/build_poster_figures.py  # poster-sized charts and the QR code
python src/build_dashboard.py       # the interactive page
```

Run `pipeline.py` first: the other two read `outputs/figures.json`.

## What it writes

Everything lands in `outputs/`.

**Numbers**

| File | What it is |
|---|---|
| `figures.json` | every headline figure, including the reconciliation result |
| `nt_components.csv` | the cleaned quarterly series, raw values |
| `dashboard_data.json` | the smoothed series behind the dashboard |

**Charts**, 300 dpi PNG and vector SVG, ready to place in a slide or poster.

| File | What it shows |
|---|---|
| `components.png` / `.svg` | the three components over 45 years, with a title |
| `components_slide.png` / `.svg` | the same chart with no title, for a layout that supplies its own heading |
| `poster_components.png` | the same chart again, sized and weighted for A1 |
| `poster_dependency.png` | share of growth from overseas migration, over three windows |
| `poster_volatility.png` | volatility of each component |
| `poster_decades.png` | quarters with a net interstate gain, by decade |
| `qr_repo.png` | QR code pointing at this repository |

**Page**

| File | What it is |
|---|---|
| `dashboard.html` | self-contained interactive page, no server or build step |

## Reading the workbook

The ABS changes these files' layout between releases: sometimes one sheet per
state, sometimes every state side by side on one sheet. Rather than hard-code
a layout that breaks next quarter, the pipeline searches the workbook for the
header row naming the components, then matches the Northern Territory columns
by their header text. It prints what it found on each sheet, so a layout
change produces a diagnosis rather than a silent wrong answer.

## Method notes

**Reconciliation.** The three components should sum to the change in
population that the ABS publishes for the same period. The pipeline checks
this before reporting anything. This is what makes the headline figure
arithmetic rather than an estimate of our own.

**Volatility.** Coefficient of variation, computed against the mean *absolute*
value of each series. Interstate migration is mostly negative, so dividing by
a signed mean would make the measure meaningless. The question is how much
each component moves relative to its own typical size.

**Smoothing.** The charts plot a four-quarter rolling average. Quarterly
figures are noisy and the shape is what matters. Raw values remain in
`outputs/nt_components.csv`.

**Colour.** Each component keeps the same hue in every chart, so the three
read as one system. Charts that encode a single measure rather than three
identities use one hue instead. The palette is validated for colour-vision
deficiency and for contrast against a light background.

## Known limitations of the source data

These belong in any honest presentation of the results:

- **Net overseas migration** uses the 12-of-16-month rule. A person counts as
  a migrant only once they have been in Australia twelve months out of
  sixteen, so somebody can change category without changing address.
- **Net interstate migration** is derived from administrative address records.
  People who rarely update those records are counted late, or not at all.
- **Census undercount** is higher in the Northern Territory than nationally,
  particularly in remote communities, and estimated resident population is
  rebased after each Census.

These are careful estimates, published quarterly and reconciled against each
other. They are still estimates, and this project treats them as such.

## Scope

This work is descriptive. It characterises the structure of population change
and the uncertainty attached to forecasting it. It makes no policy
recommendation.

## Source

Australian Bureau of Statistics. (2026). *National, state and territory
population, March 2026* [Data set]. https://www.abs.gov.au/statistics/people/population/national-state-and-territory-population/latest-release

## Licence

MIT for the code. The ABS data carries its own CC BY 4.0 terms.
