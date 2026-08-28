# Delegation-level poverty, 2015 small-area estimates

`data/processed/tn_poverty_delegations_2015.csv` — 253 rows × 9 columns

Poverty and school-dropout rates for 253 delegations across 23 governorates, extracted from the 2020 poverty map.

**These are modelled small-area estimates, not survey estimates.** EBCNV is designed to be representative at the region × milieu level; anything below that comes from a small-area model combining EBCNV 2015 with the 2014 census. Use them for description and mapping, not as if they carried survey standard errors. Siliana is absent because its table in the source report has dropout rates only.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `governorate` | str | — | derived | — |
| `delegation` | str | — | derived | — |
| `dropout_primary_pct` | float64 | — | derived | — |
| `dropout_secondary_pct` | float64 | — | derived | — |
| `dropout_both_cycles_pct` | float64 | — | derived | — |
| `poverty_rate_pct` | float64 | — | derived | — |
| `reference_year` | int64 | — | derived | — |
| `estimate_type` | str | — | derived | — |
| `source_document` | str | — | derived | — |
