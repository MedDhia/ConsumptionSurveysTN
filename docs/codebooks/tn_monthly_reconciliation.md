# Monthly panels against the totals and components printed beside them

`data/processed/tn_monthly_reconciliation.csv` — 544 rows × 11 columns

Every arithmetic check run on `tn_monthly_series`, with both figures and whether they agree.

Two kinds. The twelve months of a year against the `Total` printed beside them, which is available for 82 year-panels and holds in all 82. And, for the tourist tables, the air, land and sea panels against the combined figure printed separately — 453 months, agreeing in 98% of them. Published rather than reduced to a pass mark because each disagreement marks a page worth re-reading, and the ten months that fail are removed from the series rather than shipped.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `series` | str | — | derived | — |
| `year` | int64 | — | derived | Calendar year the observation refers to. |
| `summed` | float64 | — | derived | — |
| `months` | float64 | — | derived | — |
| `printed` | float64 | — | derived | — |
| `agrees` | bool | — | derived | — |
| `month` | float64 | — | derived | — |
| `check` | str | — | derived | — |
| `base_year` | float64 | — | derived | Year in which this index series equals 100. INS publishes the same price series on eight bases side by side; they are rescalings of one series, not eight measurements, so a chart must pick one and stay on it. |
| `monthly_mean` | float64 | — | derived | — |
| `gap` | float64 | — | derived | — |
