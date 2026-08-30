# Product rows refused by the national-versus-regions check

`data/processed/tn_regional_products_refused.csv` — 2 rows × 12 columns

Rows read out of the product-by-region tables whose printed national value contradicts their own regional columns, with the value those columns imply.

Published so that the coverage claim can be audited rather than taken on trust. Two rows out of 1,606 fail.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `wave` | int64 | — | derived | — |
| `product_ar` | str | — | derived | — |
| `Grand Tunis` | float64 | — | derived | — |
| `North East` | float64 | — | derived | — |
| `North West` | float64 | — | derived | — |
| `Centre East` | float64 | — | derived | — |
| `Centre West` | float64 | — | derived | — |
| `South East` | float64 | — | derived | — |
| `South West` | float64 | — | derived | — |
| `National` | float64 | — | derived | — |
| `implied_national` | float64 | — | derived | — |
| `reason` | str | — | derived | — |
