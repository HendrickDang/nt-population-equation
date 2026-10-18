# Slide brief

Everything needed to build the one presentation slide for the Research
Competition (RES003), without reading any code.

Build it in Canva. This file is the specification; the chart image is already
rendered and sits in `outputs/`.

---

## The rules we have to obey

From the competition format:

- **One slide.** Not a deck.
- **Static.** No animation, no transitions, no audio, no video.
- **No props.** Nothing physical, nothing handed to judges.
- The slide is a backdrop to the spoken presentation, not a document.

A slide that breaks any of these can cost the round regardless of content.

---

## Canvas

| Setting | Value |
|---|---|
| Size | 16:9, 1920 x 1080 px |
| Background | `#FCFCFB` (warm off-white, not pure white) |
| Heading font | Cambria, or any serif with real weight |
| Body font | Calibri, or any clean sans |

Do not use a dark background. The chart image is rendered on the off-white
above and will show a visible rectangle against anything else.

---

## Layout, top to bottom

### 1. Title block, top left

**Title** (approx 54 pt, `#16181C`):

```
The Territory's Population Equation
```

**Subtitle** (approx 26 pt, `#52514E`):

```
Where Northern Territory population growth comes from,
and which component makes it hardest to forecast
```

Left-aligned. Do not centre it.

### 2. The equation, one line under the subtitle

Approx 22 pt, `#6F6E6A`, letter-spaced slightly if Canva allows:

```
change  =  natural increase  +  net interstate migration  +  net overseas migration
```

This line does a lot of work. It tells a judge in one glance that the topic has
exactly three moving parts, before anybody has spoken a number.

### 3. The chart, dominant

Use **`outputs/components_slide.png`**.

That is the correct file. It is the same chart as `components.png` but with the
title and source note removed, because the slide supplies its own heading. Do
not use `components.png` (duplicate title) or `poster_components.png` (sized
for A1, too wide here).

- Place it to fill the middle band of the slide, edge to edge horizontally with
  a small margin.
- Scale proportionally. Never stretch it.
- The three series already carry their own labels at the right-hand end, so no
  legend is needed and none should be added.

### 4. Footer strip, bottom

Approx 16 pt, `#6F6E6A`, one line:

```
Van Hoi (Hendrick) Dang · Ngoc Ngan Le · Phuong Vy Ho · Thi Kim Anh Bui
Charles Darwin University · IT Code Fair 2026 · RES003
```

Source line, same size, right-hand side or directly beneath:

```
Source: ABS, National, state and territory population, March 2026. Tables 310102 and 310104.
```

**QR code**, bottom-right corner, approx 110 x 110 px: use
`outputs/qr_repo.png`. It points at this repository, so a judge can reach the
code and the validation output.

---

## Colours, exactly

The chart uses these three hues and every other element on the slide must stay
out of their way. Do not recolour anything to match a Canva template.

| Component | Hex | Where it appears |
|---|---|---|
| Natural increase | `#2A78D6` blue | the steady line near the middle |
| Net overseas migration | `#EB6834` orange | the line that climbs |
| Net interstate migration | `#1BAF7A` aqua | the line below zero |

These three were checked for colour-vision deficiency and for contrast against
the off-white background. Changing them breaks that.

---

## What must NOT go on the slide

This is the part most teams get wrong, so it is worth being blunt.

- **No numbers.** Not 90.4%, not 3,965, not 268,899. Every figure is spoken.
  A judge reading numbers is not listening to the presenter.
- **No bullet-point list.** There is no list on this slide at all.
- **No logos** other than the university's, if one is required.
- **No second chart.** The other images in `outputs/` are for the A1 poster.
- **No stock photography.** No maps of Australia, no crowds, no sunsets over
  Uluru. The chart is the picture.
- **No methodology text.** That is what the presenter is for.

If the slide can be read in full and understood without the presenter, it has
too much on it.

---

## Why the slide is this empty

The format gives three minutes and one slide. The slide's only job is to hold
the shape of the finding while the presenter supplies the content: three lines,
one of them below zero, and that one is the Territory losing residents to other
states while the population still grows.

A judge should be able to see that shape from the back of the room in two
seconds, then look at the presenter for the rest.

---

## Reference figures, for the presenter only

Not for the slide. These are the figures in the script, all of them produced by
`src/pipeline.py` and present in `outputs/figures.json`.

| Figure | Value |
|---|---|
| Reference period | March 2026 |
| Series | June 1981 to March 2026, 180 quarters |
| Natural increase, 12 months | +1,969 |
| Net interstate migration, 12 months | -1,589 |
| Net overseas migration, 12 months | +3,585 |
| Total growth, 12 months | +3,965 |
| Overseas share of growth | 90.4% |
| Estimated resident population | 268,899 |
| Annual growth | 1.5% |
| Reconciliation | 3,965 vs 3,965 published, difference 0.0, PASS |
| Volatility, natural increase | 0.125 |
| Volatility, overseas migration | 0.959 |
| Volatility, interstate migration | 1.143 (most volatile) |
| Interstate migration last positive | September 2021, negative 18 quarters since |
| Volatility ranking, post-2006 window only | unchanged: 0.942 / 0.773 / 0.148 |

The last row is the answer to the hardest question a judge can ask. The ABS
changed how net overseas migration is measured from the September quarter of
2006, so levels before and after are not comparable. The volatility ranking is
the same whether computed on the full 45 years, the 79 quarters since the
change, or the 101 quarters before it, so the finding does not rest on the
break. The check runs inside `src/pipeline.py` and is recorded in
`outputs/figures.json` under `robustness_post_2006`.

---

## If the chart image needs regenerating

Only necessary if the ABS publishes a new release before the competition.

```bash
pip install -r requirements.txt
python src/pipeline.py
```

That rewrites `outputs/components_slide.png` and every figure above. See the
README for where to put the two ABS workbooks first. If the three components
fail to reconcile against the published change, the pipeline stops and writes
nothing, so a failed run leaves the existing slide image untouched.
