# Consumer price index by COICOP function, 2012–2023

`data/processed/tn_cpi_by_division.csv` — 182 rows × 9 columns

Price index for each of the twelve COICOP consumption functions, 2012–2023, with the weights INS used to aggregate them. Read from the ten yearbook editions that print the table, each carrying three years.

**Two bases, and they must not be mixed.** INS rebased in 2016: 2012–2017 is published on base 2010 = 100 and 2016–2023 on base 2015 = 100. `base_year` says which, and the two years printed on both bases are what a chained series would have to be spliced on.

The functions match `tn_consumption_panel`'s `COICOP function` subgroup exactly, so price change and budget-share change can be set side by side. Because 2015 is a base and 2021 an EBCNV wave, the 2021 column reads directly as the price change between two survey waves.

`weight_per_100000` is INS's expenditure weight and sums to 100,000 across the twelve. `function_code` 0 is INS's own all-items total, kept because it cross-checks against `tn_cpi_annual` — which it now does for fourteen year-and-base combinations rather than three. `n_editions` counts the editions printing a cell; where more than one does, they were required to agree.

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
| `n_editions` | int64 | — | derived | How many editions printed this cell. More than one means corroborated. |
| `source_table` | str | — | derived | Table number within that document, as INS numbers it. |
