# Pre- and post-2011 means, against what the pre-2011 trend predicted

`data/processed/tn_gini_pre_post.csv` — 117 rows × 12 columns

The period means either side of 2011 for each measure in `tn_gini_decomposition`, and — the column that matters — how much of the difference the pre-2011 trend already predicted.

`change` is the raw difference between the two period means. `predicted` is what a line fitted to the pre-revolution years alone, extrapolated across the post-revolution years, would have produced on its own. `excess` is what is left.

**Read `excess`, not `change`.** The largest structural shift in the corpus is the between-region share of secondary schooling, which rises 0.15 across the cutoff — and had been rising at 0.15 per decade since 2000, through 2011, without a visible break. `change` dates that to the revolution; `excess` says how much of it needs the revolution to explain, and for that indicator the answer is close to none.

Neither column is a causal estimate. A fitted pre-trend is not a counterfactual, and nothing here rules out the trend itself turning for reasons of its own; `tn_rdit_estimates` is where the attempt to identify a break is recorded, along with what became of it.

Indicators with fewer than seven pre-revolution or eight post-revolution years are absent, because a period mean over one or two printed years is not a period mean and a trend fitted to it is worse. `n_pre`, `n_post`, `first_year` and `last_year` state the window each row rests on, since the windows are not the same.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `indicator` | str | — | derived | — |
| `measure` | str | — | derived | Which column of `tn_gini_decomposition` this row summarises. |
| `n_pre` | int64 | — | derived | Years before 2011 behind the `pre` mean. |
| `n_post` | int64 | — | derived | Years from 2011 onward behind the `post` mean. |
| `first_year` | int64 | — | derived | First year of the window this row rests on. |
| `last_year` | int64 | — | derived | Last year of the window this row rests on. The windows differ by row. |
| `pre` | float64 | — | derived | Mean of `measure` over the pre-2011 years. |
| `post` | float64 | — | derived | Mean of `measure` over the post-2011 years. |
| `change` | float64 | — | derived | `post − pre`. A difference between two periods, not an effect. |
| `pre_trend_per_decade` | float64 | — | derived | Slope of a line fitted to the pre-2011 years alone, per decade. |
| `predicted` | float64 | — | derived | What that pre-2011 line, extrapolated across the post-2011 years, would give for `change` on its own. |
| `excess` | float64 | — | derived | `change − predicted`: the part the pre-2011 trend does not already account for. Read this rather than `change`, or a decade of drift gets dated to the revolution. |
