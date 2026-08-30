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

### Reading the whole corpus

Beyond those hand-verified series, `build_yearbook.py` extracts the corpus's tabular
content — 178,021 values from 915 tables across all 22 editions — into
`tn_yearbook_series`.

Column headers come in four arrangements, and each needs its own reading:

- **A row of years.** The common case, and it dates itself.
- **School or judicial years**, written reversed as `24-23` for 2023/24. These date
  themselves too, and matter because the education and justice chapters use nothing else.
  Age bands are written identically — `04-00`, `44-40` — so the notation cannot tell them
  apart; the span does, one year against four. Reading an age-band header as years would
  turn a cross-section into a fake time series.
- **A classification** — age bands, indicator codes — for a single year taken from the
  page, never from the edition's cover.
- **Neither on one line.** Nested headers put 2023 and 2022 across the top with
  Masculin / Feminin beneath each, so six columns hang off two year cells; continuation
  pages split the labels over three lines in an order that is not the reading order.
  These are resolved from the column geometry `pdftotext -layout` preserves: a header
  cell governs the columns beneath it. That reader runs only where the first two found
  nothing, so it can add tables but never alter one already read.

A lone `-` is read as zero, which is what INS's own conventions table defines it as
(*résultat rigoureusement nul*), distinct from `>>` and `...` which mean unavailable.

**Hand-verifying that many tables is not possible, so the checking is mechanical.** Each
edition carries a five-year window, so 24 of the corpus's 26 years appear in two or more
editions, most in five. Where two editions print the same cell they must agree:

| `agreement` | Cells | What it means |
| --- | --- | --- |
| `confirmed` | 78,243 | Every edition that printed this cell printed the same value. |
| `revised` | 9,911 | They differ slightly — INS revising itself. The newest edition wins. |
| `single source` | 89,867 | Only one edition carries it. Nothing corroborates it. |

Among **year-column** cells — the ones a later edition reprints — 61.5% are confirmed.
Classification cells are 91% `single source`, and correctly so: table 1.4 in the 2023
edition is the population at 1.7.2023 while the same table in the 2019 edition is the
population at 1.7.2019. Those are different data, so nothing can cross-check them, and
the `agreement` column says so rather than implying a corroboration that does not exist.

Cells where editions disagreed by more than 10% are **not in the series at all** — that
gap is the signature of a misparse rather than a revision. They are counted in
`tn_yearbook_coverage`, which also records the 722 tables that yielded nothing.

Some tables print a row's label above its numbers, or wrapped around them, instead of
beside them. Those labels are reassembled from the neighbouring lines and the rows are
marked `label_inferred` — 2,078 cells — because that is weaker evidence than a label read
off the same line. Where two rows in one table would end up with the same reassembled
label, both are dropped rather than guessed at: on page 43 of the 2023 edition the
first-cycle and second-cycle teacher counts are named identically once the Arabic is
stripped, and nothing downstream could tell them apart.

**The parser is deliberately strict**, because surveying real pages turned up a long list
of ways a table parses cleanly and comes out wrong. `146 406.9134 862.0` is two values
printed with no separator. `Taux d'endettement5 52.3 …` glues a footnote marker to the
label and shifts every value by one. The 2010 edition prints whole columns with every
glyph doubled and no decimal point, so `1111 335511` is 11 654 and 11 351 — and no local
rule can repair that safely, because `5599` in the 2015 edition passes the same test and
is a genuine weight. Table 13.8 in the 2023 edition covers 2018–2022, not the 2019–2023 on
its own cover.

So the year header is always read from the page and never inferred, a row is accepted only
when it yields exactly as many numbers as there are year columns, and a label ending in a
digit is refused. Strictness costs coverage; `tn_yearbook_coverage` records what it cost.
Two independent code paths — the bespoke unemployment builder and the generic extractor —
read the same printed table and are asserted to agree exactly.

`row_kind` marks totals, subtotals and `dont` sub-rows as `aggregate`: summing a table
without filtering them roughly double-counts.

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
| `tn_yearbook_tables` | 8,391 | Every numbered table heading in all 22 yearbooks, with edition and page. |
| `tn_yearbook_series` | 178,021 | Values from the yearbooks' tables, reconciled across editions. |
| `tn_yearbook_coverage` | 1,637 | What was extracted, what was refused, and why. |

All labels are translated to English; every codebook keeps the original French and Arabic
alongside, code by code.

## Quick start

```bash
make setup           # bsdtar, pdftotext, Python requirements
make fetch           # 43 documents, ~290 MB, checksummed into data/raw/manifest.json
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

[`figures/`](figures) holds thirty charts on inequality, with a light and a dark
version of each. Six trace its evolution from 1985 to 2021; six look inside the groups the
first six average over; four compare the two waves before January 2011 with the two after;
three come from the statistical yearbooks and cover prices and unemployment annually; and
seven use the health, education and labour modules and the product-level file; and four
ask whether the revolution's effect can be identified at all from the yearbooks'
governorate panel, and show that it cannot. **None of them uses a composite index of
inequality** — no Gini, no Theil, no Atkinson. Every figure shows an observed quantity or
the relation between two observed quantities, so any number in them can be recovered from
the datasets by hand. `make figures` redraws them.

Two caveats the figures carry in their own text rather than in a footnote. Figures 13–16
are descriptive before-and-after comparisons, not causal estimates: the 2010–2021 window
contains the revolution alongside the 2015 attacks, the tourism collapse, dinar
depreciation and COVID, and nothing here separates them. And the consumer price index in
figures 17 and 18 is a price level, not a summary of a distribution — it is not the kind
of index the rule above is about.

Figures 27–30 go further and test the identification directly. With every governorate
treated at the same instant there is no control group, so the two candidate designs are an
interrupted time series and a difference-in-differences on differential exposure. A
placebo test moving the assumed break year shows 2011 is not distinguishable from 2010,
2012, 2014 or 2015; and the interior–coastal gap was already widening by 0.21 a year for
twelve years before 2011. Both requirements fail, which is a finding about the limits of
the evidence rather than a claim that the revolution had no effect.

## Continuous integration

Two workflows, split on whether they need the survey data:

**`checks`** runs on every pull request, and on pushes to `main`. (Not on pushes to a
branch with an open PR — that would run it twice for every commit.) Ruff, plus the 20
structural tests that
need no data and no network — that every decode rule names a real value set, that no
value set is orphaned, that every source URL is HTTPS on ins.tn, that the committed
manifest covers every registered source, that no dataset is missing a codebook title. It
finishes in well under a minute, and a red result always means something about the diff.

**`pipeline`** does the real work: installs bsdtar and pdftotext, fetches the 290 MB from
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

It is deliberately excluded from pull requests. Force-fetching 290 MB with the cache off
is not a cost a PR should pay, and INS changing a file unrelated to the diff is not a
reason to block one.

## Layout

```
.github/workflows/  checks (fast, gating) and pipeline (full, data-dependent)
.claude/hooks/      SessionStart hook: installs dependencies in a fresh web session
src/consumptiontn/
  config.py          source registry: 43 documents, one place to fix a moved URL
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
