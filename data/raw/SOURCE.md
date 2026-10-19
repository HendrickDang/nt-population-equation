# Source data

The two workbooks in this folder are the exact files every figure in this
project was computed from. They are committed deliberately, so that cloning the
repository and running the pipeline reproduces the published numbers rather than
different ones.

| File | ABS table | What it holds |
|---|---|---|
| `310102.xlsx` | 310102 | Components of population change, states and territories, quarterly |
| `310104.xlsx` | 310104 | Estimated resident population, states and territories, quarterly |

**Release:** National, state and territory population, March 2026
**Downloaded:** 18 October 2026
**Series covered:** June 1981 to March 2026, 180 quarters

## Attribution

Australian Bureau of Statistics. (2026). *National, state and territory
population, March 2026* [Data set].
https://www.abs.gov.au/statistics/people/population/national-state-and-territory-population/latest-release

Licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/),
which permits redistribution with attribution. These files are unmodified.

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
