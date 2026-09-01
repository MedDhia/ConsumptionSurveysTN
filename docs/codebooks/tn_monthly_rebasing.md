# The measured ratio between the two industrial-price bases where they overlap

`data/processed/tn_monthly_rebasing.csv` — 288 rows × 6 columns

The ratio between the two industrial-price bases in the months both are printed, which is the evidence for not chaining them.

A rebasing alone rescales an index, so the ratio between two bases would be one constant per sector and a single factor would carry either series onto the other. These are not constant. Across the thirty-six overlapping months of 2010–2012, chemicals ranges from 0.607 to 0.774 and textiles from 0.775 to 0.873, while food holds to within a third of a percent — so the basket was re-weighted unevenly, not merely re-based.

The consequence is visible in `tn_rdit_estimates`: over the *same* six months either side of January 2011, the two bases give industrial-price jumps that differ in sign for four of the eight sectors. A log difference is invariant to a pure rescaling, so that disagreement is entirely the re-weighting, and it says the industrial-price discontinuity is not robust to which index construction you read it on.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `group` | str | — | derived | Category within the breakdown. `all` is that table's own total row. |
| `year` | int64 | — | derived | Calendar year the observation refers to. |
| `month` | int64 | — | derived | — |
| `old_base` | int64 | — | derived | — |
| `new_base` | int64 | — | derived | — |
| `ratio` | float64 | — | derived | — |
