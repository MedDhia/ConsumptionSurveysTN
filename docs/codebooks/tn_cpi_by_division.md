# Consumer price index by COICOP function, 2021–2023

`data/processed/tn_cpi_by_division.csv` — 39 rows × 8 columns

Price index for each of the twelve COICOP consumption functions, 2021–2023, on base 2015 = 100, with the weights INS used to aggregate them.

The functions match `tn_consumption_panel`'s `COICOP function` subgroup exactly, so price change and budget-share change can be set side by side. Because 2015 is the base and 2021 an EBCNV wave, the 2021 column reads directly as the price change between two survey waves.

`weight_per_100000` is INS's expenditure weight and sums to 100,000 across the twelve. `function_code` 0 is INS's own all-items total, kept because it cross-checks against `tn_cpi_annual`.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `year` | int64 | — | derived | Calendar year the observation refers to. |
| `function_code` | int64 | — | derived | COICOP function 1-12, matching `tn_consumption_panel`. Code 0 is INS's own all-items total, kept because it cross-checks against `tn_cpi_annual`. |
| `function` | str | — | derived | English name of the COICOP function. |
| `index` | float64 | index, base year = 100 | derived | Consumer price index. Reads 100.0 in its own base year. |
| `weight_per_100000` | int64 | parts per 100,000 | derived | INS's expenditure weight for this COICOP function, in parts per 100,000. Sums to exactly 100,000 across the twelve functions. |
| `base_year` | int64 | — | derived | Year in which this index series equals 100. INS publishes the same price series on eight bases side by side; they are rescalings of one series, not eight measurements, so a chart must pick one and stay on it. |
| `source_key` | str | — | derived | Key of the source document in `src/consumptiontn/config.py`. |
| `source_table` | str | — | derived | Table number within that document, as INS numbers it. |
