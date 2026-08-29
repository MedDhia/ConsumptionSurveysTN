# ConsumptionSurveysTN

[![checks](https://github.com/MedDhia/ConsumptionSurveysTN/actions/workflows/tests.yml/badge.svg)](https://github.com/MedDhia/ConsumptionSurveysTN/actions/workflows/tests.yml)
[![pipeline](https://github.com/MedDhia/ConsumptionSurveysTN/actions/workflows/pipeline.yml/badge.svg)](https://github.com/MedDhia/ConsumptionSurveysTN/actions/workflows/pipeline.yml)

Research-ready datasets built from Tunisia's *Enquête Nationale sur le Budget, la
Consommation et le Niveau de vie des ménages* (EBCNV), the household consumption survey
the Institut National de la Statistique has run every five years since 1968.

Everything here is derived from what INS publishes at [ins.tn](https://www.ins.tn), plus
the *Annuaire Statistique de la Tunisie* for the annual price and labour series the
five-yearly survey cannot give. The pipeline downloads it all, checksums it, builds the
datasets, and then checks its own work by reproducing INS's published headline figures
from the microdata.

## What INS actually publishes

The short version, because it shapes everything downstream:

| Wave | What exists |
| --- | --- |
| 1968, 1975, 1980 | Conducted. Nothing published online. |
| 1985 | One national figure, from a chart in the 2005 volume. |
| 1990–2000 | Aggregate series by region and milieu, in the 2005 volume's retrospective tables. |
| 2005, 2010, 2015 | Full PDF volumes, plus retrospective series in the 2021 synthesis note. |
| 2019 | A modelled poverty rate only (13.8%), imputed from a follow-up panel. |
| **2021** | **Microdata** — seven Stata files — plus Excel annexes and volumes A and C. |

So the depth of what can be built varies by era, and the datasets below say which era
each number came from rather than presenting a smooth series that isn't one.

### The statistical yearbooks

Alongside the survey, the pipeline reads the *Annuaire Statistique de la Tunisie*,
editions 2001–2023 (2013 was never issued). These are general-statistics volumes, not
consumption surveys, and they supply two things EBCNV cannot: an annual consumer price
index, and annual unemployment by education level.

Three things about them are worth knowing before trusting anything built on them.

**They are fetched from a mirror.** The editions come from a Google Drive folder that
mirrors documents INS also publishes. A mirror can be edited by whoever owns it, so the
sha256 in `data/raw/manifest.json` is doing more work here than for the ins.tn sources —
if one moves, treat the file as untrusted until re-checked against the INS release.

**Table numbers move between editions.** The CPI evolution table is 13.6 in the 2023
edition and 13.7 in 2010. Every table is located by its French title, never by number.

**Two rendering faults will corrupt a naive parse.** Bold columns emit every glyph twice,
so 70.0 arrives as `7700..00`; and thousands are separated by a space, so `1 013.5` is one
number. Both are repaired explicitly, and both are asserted in `tests/test_yearbooks.py` —
because each one fails silently, producing a number of the right shape and the wrong
magnitude.

The unemployment series is spliced from three editions that overlap by design: 2015
appears in two of them and 2019 in two, and the builder requires the shared years to agree
exactly. That is what verifies the right column was read from each volume. It does **not**
reach before 2011 — the 2005, 2010 and 2012 editions carry no unemployment table at all.

## Datasets

Built into `data/processed/` as CSV and Parquet, each with a codebook in
[`docs/codebooks/`](docs/codebooks).

| Dataset | Rows | What it is |
| --- | --- | --- |
| `tn_hbs_2021_household` | 17,394 | Household core: expenditure, poverty status, head characteristics, composition, budget shares. |
| `tn_hbs_2021_expenditure` | 3,260,352 | Household × product acquisitions, annualised, with the product nomenclature attached. |
| `tn_hbs_2021_expenditure_by_function` | 17,394 | Household × the twelve COICOP functions, in dinars and as budget shares. |
| `tn_hbs_2021_products` | 1,446 | The 5-digit product nomenclature with COICOP function assignments. |
| `tn_hbs_2021_individuals` | 65,524 | Roster + education + health modules, one row per person. |
| `tn_hbs_2021_dwelling` | 17,394 | Housing, water, sanitation, energy, service access, 15 durable goods. |
| `tn_consumption_panel` | 759 | Long indicator panel 1985–2021: expenditure, poverty, Gini, budget shares. |
| `tn_poverty_delegations_2015` | 253 | Delegation-level poverty and school-dropout rates from the 2020 poverty map. |
| `tn_wave_coverage` | 12 | What is available for each wave since 1968. |
| `tn_cpi_annual` | 200 | Consumer price index 1999–2023, on each of INS's eight base years. |
| `tn_cpi_by_division` | 39 | Price index by COICOP function 2021–2023, base 2015 = 100, with INS weights. |
| `tn_unemployment_annual` | 104 | Unemployment by education level and by sex, 2011–2023. |

All labels are translated to English; every codebook keeps the original French and Arabic
alongside, code by code.

## Quick start

```bash
make setup           # bsdtar, pdftotext, Python requirements
make fetch           # 21 INS artefacts, ~86 MB, checksummed into data/raw/manifest.json
make build           # datasets + codebooks, ~3 minutes
make test            # reproduce INS's published figures from the microdata

make check-upstream  # has INS republished any of the 21 files? ~2 minutes
```

`make test-fast` skips everything needing `data/raw` and runs in under a second, so it is
worth having in a watch loop while editing; `make lint` is the same ruff check CI runs.

`make check-upstream` is the one to reach for when you want to know whether the sources
have moved. It re-downloads all 21 artefacts with the cache bypassed and compares them to
the committed manifest, exiting non-zero if anything changed. It needs no CI and no
waiting for a schedule. `make verify` is the cheaper cousin: it only checks the files
already on disk, so it cannot see an upstream change you have not fetched.

## File formats

Every dataset is committed in two formats, so the repository is usable without running
anything:

| Format | Use it when |
| --- | --- |
| `.csv` | You want it to just open — R, Python, Stata, a spreadsheet, no package needed. |
| `.parquet` | You want dtypes preserved and a much faster load. `arrow` in R, `pandas` in Python. |

`tn_hbs_2021_expenditure` is the one exception: 3.26M rows is 419 MB as plain CSV, past
GitHub's 100 MB per-file limit, so its CSV is gzipped. Both languages read that directly —
no need to decompress it first.

### Python

```python
import pandas as pd, numpy as np

hh = pd.read_csv("data/processed/tn_hbs_2021_household.csv")       # or .parquet
exp = pd.read_csv("data/processed/tn_hbs_2021_expenditure.csv.gz")  # gzip auto-detected

# INS's headline: mean annual expenditure per person, 5,468 DT
np.average(hh.expenditure_pc, weights=hh.weight_pop)

# Poverty headcount by region
(hh.assign(p=hh.poor.eq("poor"))
   .groupby("region", observed=True)
   .apply(lambda g: 100 * np.average(g.p, weights=g.weight_pop)))
```

### R

```r
hh  <- read.csv("data/processed/tn_hbs_2021_household.csv", fileEncoding = "UTF-8")
exp <- read.csv(gzfile("data/processed/tn_hbs_2021_expenditure.csv.gz"))

# 5468.3 -- the same figure INS publishes
weighted.mean(hh$expenditure_pc, hh$weight_pop)

# 16.59%
100 * weighted.mean(hh$poor == "poor", hh$weight_pop)

# Poverty headcount by region
tapply(seq_len(nrow(hh)), hh$region,
       function(i) 100 * weighted.mean(hh$poor[i] == "poor", hh$weight_pop[i]))
```

Product labels are French and carry accents, so the files are UTF-8. Base `read.csv`
inherits your session's locale, which on Windows or a bare container may not be UTF-8 —
pass `fileEncoding = "UTF-8"` as above, or use `readr::read_csv()`, which assumes UTF-8.
Skip it and accents come back as `<U+00E9>` escapes. Both were checked against the same
files: R and Python agree on 496 accented and 438 comma-containing product labels.

## Four things that will bite you

These are the traps this pipeline hit, documented so you don't have to hit them too.

**1. `unar` silently truncates the microdata.** `unar` and the `unrar`-backed `rarfile`
package stop at 1,310,720 of `pov_2021.dta`'s 1,411,290 bytes and leave an unreadable
Stata file. libarchive's `bsdtar` extracts it correctly. That is why `make setup`
installs `libarchive-tools` and why `extract.py` refuses to fall back.

**2. Product amounts are not annual.** In `produit2021_plus.dta`, `v407` is the amount
observed over the diary window for its questionnaire table; `frequence` is the
annualisation multiplier. Sum `v407 * frequence` and you reproduce INS's household
totals exactly. Sum `v407` alone and you understate them by about three quarters.

**3. There are two weights and they answer different questions.** `weight_pop` (`v701`)
is the individual factor and equals `weight_hh * hh_size`. Per-person statistics —
mean per-capita expenditure, poverty headcount — take `weight_pop` and give 5,468 DT and
16.6%. The same expenditure variable weighted by `weight_hh` gives 6,164 DT: a real
quantity, but not the one INS publishes.

**4. The poverty series has a methodological break in it.** INS revised its poverty
methodology in 2011. The 2005 volume reports national poverty of 3.8% for 2005; the 2021
note reports 23.1% for that same year. Both are correct as published. The panel tags
every row `pre-2011` or `revised (2011)` and the two must never be plotted as one line.

## Validating against INS

`make test` runs 64 checks — 20 structural ones that need no data, and 44 that do. The
substantive ones recompute INS's published figures from the microdata:

| Quantity | Published | Source |
| --- | --- | --- |
| Mean expenditure per person | 5,468 DT | Tableau 1 |
| — urban / rural | 6,141 / 4,041 DT | Tableau 1 |
| Mean expenditure per household | 20,328 DT | Tableau 1 |
| Per-person expenditure, all 7 regions | 3,614–6,874 DT | Tableau 2 |
| Expenditure across all 12 COICOP functions | 8–1,645 DT | Tableau 4 |
| Poverty lines, urban / rural | 2,683 / 2,224 DT | Tableau 5 |
| Poverty rate / extreme poverty rate | 16.6% / 2.9% | Tableau 6 |
| Poor / extremely poor persons | 1,950,000 / 337,141 | landing page |
| Poverty rate, all 7 regions | 4.7–37.0% | Tableau 7 |
| Gini index | 35.3 | Tableau 10 |

All ten reproduce within the precision INS prints them at, on a clean CI runner as well
as locally. Reproducing Tableau 4 needed
one non-obvious correction: nine ready-to-eat products coded `11171`–`11179` (pizza,
crêpe, brik, ice cream and so on) are counted under food, not under restaurants and
cafés. The override is read off INS's own `DPA_5Cfiffres` sheet and moves 32.3 DT per
person — without it, two of the twelve functions are wrong and the other ten are right,
which is exactly the kind of error that survives casual checking.

## Figures

[`figures/`](figures) holds twenty-six charts on inequality, with a light and a dark
version of each. Six trace its evolution from 1985 to 2021; six look inside the groups the
first six average over; four compare the two waves before January 2011 with the two after;
three come from the statistical yearbooks and cover prices and unemployment annually; and
seven use the health, education and labour modules and the product-level file, none of
which any earlier figure had touched. **None of them uses a composite index of
inequality** — no Gini, no Theil, no Atkinson. Every figure shows an observed quantity or
the relation between two observed quantities, so any number in them can be recovered from
the datasets by hand. `make figures` redraws them.

Two caveats the figures carry in their own text rather than in a footnote. Figures 13–16
are descriptive before-and-after comparisons, not causal estimates: the 2010–2021 window
contains the revolution alongside the 2015 attacks, the tourism collapse, dinar
depreciation and COVID, and nothing here separates them. And the consumer price index in
figures 17 and 18 is a price level, not a summary of a distribution — it is not the kind
of index the rule above is about.

## Continuous integration

Two workflows, split on whether they need the survey data:

**`checks`** runs on every pull request, and on pushes to `main`. (Not on pushes to a
branch with an open PR — that would run it twice for every commit.) Ruff, plus the 20
structural tests that
need no data and no network — that every decode rule names a real value set, that no
value set is orphaned, that every source URL is HTTPS on ins.tn, that the committed
manifest covers every registered source, that no dataset is missing a codebook title. It
finishes in well under a minute, and a red result always means something about the diff.

**`pipeline`** does the real work: installs bsdtar and pdftotext, fetches the 86 MB from
ins.tn, builds every dataset, and runs the full suite including the reproduction of INS's
published figures. It also asserts that a fresh build reproduces the committed datasets
and codebooks byte for byte, and uploads `data/processed` as an artifact so the built
datasets can be downloaded without running anything. It runs weekly, on demand, and on
pull requests that touch the pipeline. `data/raw` is cached on the committed manifest's
hash, so ins.tn is only contacted when the manifest changes or the cache expires.

The `upstream-drift` job re-downloads everything with the cache disabled and fails if any
checksum has moved — that is `make check-upstream`, and a red run means INS has
republished a file under the same URL, which is worth knowing before it silently changes
a number. It runs on the weekly schedule **and on demand**: Actions → `pipeline` → Run
workflow, or just `make check-upstream` locally. You never have to wait for Monday.

It is deliberately excluded from pull requests. Force-fetching 86 MB with the cache off
is not a cost a PR should pay, and INS changing a file unrelated to the diff is not a
reason to block one.

## Layout

```
.github/workflows/  checks (fast, gating) and pipeline (full, data-dependent)
.claude/hooks/      SessionStart hook: installs dependencies in a fresh web session
src/consumptiontn/
  config.py          source registry: 21 INS artefacts, one place to fix a moved URL
  download.py        fetch + SHA-256 + manifest
  extract.py         RAR -> Stata (bsdtar only), .dta reading
  extract_pdf.py     the poverty map's delegation tables
  labels.py          French/Arabic -> English, written out explicitly
  build_*.py         one module per dataset
  panel_sources.py   published figures, transcribed with table-level citations
  codebook.py        codebook generation
docs/SOURCES.md      every URL, checksum and retrieval date (generated)
docs/codebooks/      one per dataset
tests/               reproduce INS's published figures
```

Pre-2015 INS volumes are right-to-left Arabic; `pdftotext` returns their columns in
reversed visual order with headers split across lines. Rather than ship a parser whose
failures would be invisible, those figures are transcribed in `panel_sources.py` with
the table number attached, so any row can be checked against the PDF in under a minute.

## Licence and attribution

Code is MIT (see [LICENSE](LICENSE)). The underlying data is published by the Institut
National de la Statistique de Tunisie; cite INS and the EBCNV wave, and see INS's
[conditions d'utilisation](https://www.ins.tn/conditions-utilisation). This repository
redistributes no INS file — `make fetch` downloads them from ins.tn directly.
