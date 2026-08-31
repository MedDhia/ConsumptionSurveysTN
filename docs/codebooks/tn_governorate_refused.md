# Governorate-years whose parts contradict their printed national total

`data/processed/tn_governorate_refused.csv` — 463 rows × 8 columns

Indicator-years excluded from `tn_governorate_panel` because the 24 governorates do not sum to the national total printed in the same table, with both figures and the gap.

Published rather than dropped because each one marks a page worth re-reading. Library lending in 2000 fails because Manouba reads 404 books against 150,250 the following year — a misread in the only edition that prints that year, so no cross-edition check could have seen it.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `indicator` | str | — | derived | — |
| `year` | int64 | — | derived | Calendar year the observation refers to. |
| `governorate` | str | — | derived | — |
| `breakdown` | str | — | derived | Which yearbook table the row came from: `education` or `sex`. |
| `summed` | float64 | — | derived | — |
| `printed` | float64 | — | derived | — |
| `gap` | float64 | — | derived | — |
| `reason` | str | — | derived | — |
