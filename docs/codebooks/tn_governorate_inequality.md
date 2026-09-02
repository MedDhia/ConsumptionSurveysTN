# Gini, Theil, Atkinson and percentile ratios across governorates, 1994–2023

`data/processed/tn_governorate_inequality.csv` — 3,889 rows × 17 columns

The conventional inequality indices for the distribution of each indicator across governorates, one row per indicator, basis, geography, year and weighting — the longitudinal form needed to ask how regional inequality *evolved*.

Elsewhere this repository avoided composite indices and showed observed quantities instead. That constraint is lifted here, because a question about evolution needs one comparable number per year. Several indices are computed rather than one, since the choice of index is a choice about which part of the distribution matters: `gini` reads the middle, `theil_t` the top, `theil_l` (mean log deviation) the bottom, and `atkinson_05/1/2` the same distribution with rising aversion to the worst-off. `cv` is the most outlier-driven of the set; `p90_p10` and `p80_p20` are ratios between positions rather than summaries of everything, which is why they belong beside the others. **Where Theil-T and Theil-L disagree, that disagreement is the finding** — it locates the change in the distribution.

Every index is computed twice. `population` weighting treats the distribution as one over people: a Tunisian picked at random. `unweighted` treats it as one over administrative units, which is what a governorate-level regression does to its observations. They can move in opposite directions, and when they do it means a change concentrated in small governorates. The weighted family needs a population and so begins in 2005, while the unweighted runs from 1994.

Theil-L and Atkinson at ε≥1 are undefined where any governorate reports zero, and those cells are left empty rather than floored — a governorate with no cinema screens is a real observation that a log measure has nothing to say about. `gini`, `cv` and the ratios survive zeros.

Only complete years are measured, for the reason `tn_governorate_dispersion` gives: an index computed over whichever governorates were printed moves when coverage moves, and that artefact is indistinguishable from a trend once plotted.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `indicator` | str | — | derived | — |
| `basis` | str | — | derived | — |
| `geography` | str | — | derived | — |
| `year` | int64 | — | derived | Calendar year the observation refers to. |
| `weighting` | str | — | derived | — |
| `period` | str | — | derived | `pre` for years before 2011, `post` for 2011 onward. A label, not a design. |
| `governorates` | int64 | — | derived | — |
| `mean` | float64 | — | derived | — |
| `gini` | float64 | — | derived | — |
| `theil_t` | float64 | — | derived | — |
| `theil_l` | float64 | — | derived | — |
| `cv` | float64 | — | derived | — |
| `atkinson_05` | float64 | — | derived | — |
| `atkinson_1` | float64 | — | derived | — |
| `atkinson_2` | float64 | — | derived | — |
| `p90_p10` | float64 | — | derived | — |
| `p80_p20` | float64 | — | derived | — |
