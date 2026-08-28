# ConsumptionSurveysTN

[![checks](https://github.com/MedDhia/ConsumptionSurveysTN/actions/workflows/tests.yml/badge.svg)](https://github.com/MedDhia/ConsumptionSurveysTN/actions/workflows/tests.yml)
[![pipeline](https://github.com/MedDhia/ConsumptionSurveysTN/actions/workflows/pipeline.yml/badge.svg)](https://github.com/MedDhia/ConsumptionSurveysTN/actions/workflows/pipeline.yml)

Research-ready datasets built from Tunisia's *Enquête Nationale sur le Budget, la
Consommation et le Niveau de vie des ménages* (EBCNV), the household consumption survey
the Institut National de la Statistique has run every five years since 1968.

Everything here is derived from what INS publishes at [ins.tn](https://www.ins.tn). The
pipeline downloads it, checksums it, builds the datasets, and then checks its own work by
reproducing INS's published headline figures from the microdata.

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

## Datasets

Built into `data/processed/`, each with a codebook in [`docs/codebooks/`](docs/codebooks).

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

All labels are translated to English; every codebook keeps the original French and Arabic
alongside, code by code.

## Quick start

```bash
make setup     # bsdtar, pdftotext, Python requirements
make fetch     # 21 INS artefacts, ~86 MB, checksummed into data/raw/manifest.json
make build     # datasets + codebooks, ~3 minutes
make test      # reproduce INS's published figures from the microdata
```

`make test-fast` skips everything needing `data/raw` and runs in under a second, so it is
worth having in a watch loop while editing.

```python
import pandas as pd, numpy as np

hh = pd.read_parquet("data/processed/tn_hbs_2021_household.parquet")

# INS's headline: mean annual expenditure per person, 5,468 DT
np.average(hh.expenditure_pc, weights=hh.weight_pop)

# Poverty headcount by region
(hh.assign(p=hh.poor.eq("poor"))
   .groupby("region", observed=True)
   .apply(lambda g: 100 * np.average(g.p, weights=g.weight_pop)))
```

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

## Continuous integration

Two workflows, split on whether they need the survey data:

**`checks`** runs on every push and pull request. Ruff, plus the 20 structural tests that
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

A weekly `upstream-drift` job re-downloads everything with the cache disabled and fails
if any checksum has moved — that is `make check-upstream`, and a red run means INS has
republished a file under the same URL, which is worth knowing before it silently changes
a number.

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
