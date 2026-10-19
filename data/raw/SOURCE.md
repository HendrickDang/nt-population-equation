# Source data

The workbooks in this folder are the exact files every figure in this project
was computed from. They are committed deliberately, so that cloning the
repository and running the pipeline reproduces the published numbers rather than
different ones.

## Population, the main analysis

Read by `src/pipeline.py`.

| File | ABS table | What it holds |
|---|---|---|
| `310102.xlsx` | 310102 | Components of population change, states and territories, quarterly |
| `310104.xlsx` | 310104 | Estimated resident population, states and territories, quarterly |

**Release:** National, state and territory population, March 2026
**Downloaded:** 18 October 2026
**Series covered:** June 1981 to March 2026, 180 quarters

Australian Bureau of Statistics. (2026). *National, state and territory
population, March 2026* [Data set].
https://www.abs.gov.au/statistics/people/population/national-state-and-territory-population/latest-release

## Interstate flows, the supporting analysis

Read by `src/interstate_flows.py`. Same release as the population tables above.

| File | ABS table | Series ID (NT) | What it holds |
|---|---|---|---|
| `3101016A.xlsx` | 16A | A2060858X | Interstate migration arrivals, quarterly |
| `3101016B.xlsx` | 16B | A2060867A | Interstate migration departures, quarterly |

**Downloaded:** 19 October 2026
**Series covered:** June 1981 to March 2026, 180 quarters

Table 310102 gives only the net of these two flows. Arrivals minus departures
reproduces that net exactly in all 180 quarters, which the script checks before
writing anything.

Same citation as the population tables: ABS, *National, state and territory
population, March 2026*.

## Housing and wages, the supporting analysis

Read by `src/housing.py`. Not used in the presentation; see that script's
docstring for why it exists.

| File | ABS table | Series ID | What it holds |
|---|---|---|---|
| `643202.xlsx` | 643202 | A83728569K | Median price of established house transfers, Darwin, quarterly |
| `634502b.xlsx` | 634502b | A2606269C | Wage price index, Northern Territory, all industries, quarterly |

**Downloaded:** 19 October 2026
**Common window:** March 2002 to June 2026, 98 quarters

The Darwin price series is an **unstratified median of transfers**, not a
hedonic index. It moves with the mix of houses sold as well as with prices,
which is why it differs from commercially published measures such as Cotality's
for the same period. The comparison here is stated on that basis.

Australian Bureau of Statistics. (2026). *Total value of dwellings* [Data set].
https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/total-value-dwellings/latest-release

Australian Bureau of Statistics. (2026). *Wage price index, Australia*
[Data set]. https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/wage-price-index-australia/latest-release

## Attribution

All files are Australian Bureau of Statistics data, licensed under
[Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/),
which permits redistribution with attribution. They are unmodified.

## Why these are committed rather than downloaded

The ABS publishes each quarter at the same `latest-release` URL, replacing what
was there before. A reader who follows that link in January 2027 gets the
December 2026 release, not this one, and the pipeline will produce different
figures from the ones on our poster and in our talk.

Pinning the snapshot is what makes the project reproducible. The alternative,
telling a reader to download the current release, reproduces the *method* but
not the *result*.

## Updating to a newer release

Download the two tables from the link above, replace these files keeping the
same names, and re-run `python src/pipeline.py`. Every figure, chart and the
dashboard regenerate. Update the release date and download date above in the
same commit, so the repository never claims a provenance it does not have.

If the three components stop reconciling against the published change, the
pipeline stops and writes nothing. That is the intended behaviour: check that
both files come from the same release before investigating anything else.
