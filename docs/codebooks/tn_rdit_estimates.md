# RDiT estimates of the January 2011 break, with bias-aware intervals

`data/processed/tn_rdit_estimates.csv` — 355 rows × 19 columns

Regression-discontinuity-in-time estimates of the January 2011 break, for every outcome this corpus supports — monthly and annual, across a range of bandwidths.

The design question the whole repository circles: did the revolution change anything measurable, and can a change be attributed to it rather than merely dated to it. The answer depends on frequency, and both cases are reported here so the contrast is visible in one table rather than argued for in prose.

`tau` is the jump at the cutoff, in logs for the monthly counts so it reads as a proportional change. `se` is HAC, because monthly series are autocorrelated. `honest_lo`/`honest_hi` are the Armstrong–Kolesár bias-aware interval: as the bandwidth widens the worst-case bias grows with it, so **an interval that is tight at six months and explodes at sixty is telling you the wide-bandwidth number was never identified**. Watching that happen across the bandwidth column is how to read this dataset.

`randomisation_p` is permutation inference inside the window and `randomisation_floor` is the smallest p-value that window could possibly produce. With few periods the floor sits above 0.05, and then the test cannot reject whatever the data say — a p of 0.12 against a floor of 0.11 is not weak evidence of no effect, it is no evidence either way.

Every monthly outcome is estimated with and without a one-month donut. Ben Ali left on 14 January 2011, so that month is half of each regime; if the two estimates disagree, the design is picking up the transition rather than a step.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `outcome` | str | — | derived | — |
| `frequency` | str | — | `produit2021_plus.dta` → `frequence` | «Fréquence Produit» |
| `scale` | str | — | derived | — |
| `method` | str | — | derived | — |
| `bandwidth` | int64 | — | derived | — |
| `donut` | int64 | — | derived | — |
| `n_left` | int64 | — | derived | — |
| `n_right` | int64 | — | derived | — |
| `tau` | float64 | — | derived | — |
| `se` | float64 | — | derived | — |
| `honest_lo` | float64 | — | derived | — |
| `honest_hi` | float64 | — | derived | — |
| `worst_case_bias` | float64 | — | derived | — |
| `honest_excludes_zero` | bool | — | derived | — |
| `bias_exceeds_estimate` | bool | — | derived | — |
| `randomisation_p` | float64 | — | derived | — |
| `randomisation_floor` | float64 | — | derived | — |
| `smoothness` | float64 | — | derived | — |
| `refused` | str | — | derived | — |
