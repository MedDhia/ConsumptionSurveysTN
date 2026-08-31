# Five national series at monthly frequency, 1995–2023

`data/processed/tn_monthly_series.csv` — 1,565 rows × 11 columns

Five national series at monthly frequency, 1995–2023 — the only frequency in this corpus at which a regression discontinuity in time can actually be local.

With annual data there is nothing to shrink: a five-year window holds five points either side and the estimate is whatever the assumed polynomial does over a decade. A six-month window holds six. `running` counts months from January 2011, so the cutoff sits exactly on a sample point.

Every series is checked against arithmetic printed in the same table. The twelve months must come to the printed `Total` — 82 year-panels can be checked that way and all 82 agree — and the tourist tables, printed once for all modes and again by air, land and sea, must have the parts come to the whole. That second check is the only one departures has, since no edition prints a total beside them.

**`published_share` is not a formality.** INS printed an ellipsis rather than a number for May–September and December 2011 in the tourism tables: six of twelve months absent from the source, and they are the summer peak immediately after the uprising, when any effect would be largest. The missingness is correlated with the treatment. The road and money series are complete through 2011.

One candidate was rejected outright. Rows labelled with the twelve months appear under a job-applications title, which would have been the most revolution-relevant outcome in the yearbooks; table 6.1.6 is by governorate and prints no monthly panel, and the rows sum to about 5,800 a year against a printed 391,927.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `series` | str | — | derived | — |
| `description` | str | — | derived | — |
| `unit` | str | — | derived | — |
| `year` | int64 | — | derived | Calendar year the observation refers to. |
| `month` | int64 | — | derived | — |
| `t` | float64 | — | derived | — |
| `running` | int64 | — | derived | — |
| `treated` | bool | — | derived | — |
| `value` | float64 | — | derived | — |
| `log_value` | float64 | — | derived | — |
| `published_share` | float64 | — | derived | — |
