# Consumer price index, 1999–2023

`data/processed/tn_cpi_annual.csv` — 200 rows × 5 columns

Consumer price index for Tunisia, 1999–2023, on each of the eight base years INS publishes side by side, read from the 2023 statistical yearbook.

**Pick one base year and stay on it.** The eight columns are the same series rescaled, not eight different measurements; mixing them produces nonsense. Each base year reads exactly 100.0 in its own year, which the builder asserts.

This is a price level, not a quantity: it says what a fixed basket cost, not what anyone bought. Pair it with the budget shares in `tn_consumption_panel`.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `year` | int64 | — | derived | Calendar year the observation refers to. |
| `base_year` | int64 | — | derived | Year in which this index series equals 100. INS publishes the same price series on eight bases side by side; they are rescalings of one series, not eight measurements, so a chart must pick one and stay on it. |
| `index` | float64 | index, base year = 100 | derived | Consumer price index. Reads 100.0 in its own base year. |
| `source_key` | str | — | derived | Key of the source document in `src/consumptiontn/config.py`. |
| `source_table` | str | — | derived | Table number within that document, as INS numbers it. |
