# Consumer price index by function, chained to base 2015, 2012–2023

`data/processed/tn_cpi_chained.csv` — 156 rows × 7 columns

The two bases of `tn_cpi_by_division` spliced into one series, 2012–2023, all of it on base 2015 = 100 — the form needed to deflate anything across the 2016 rebasing.

INS prints 2016 and 2017 on **both** bases, so the factor carrying a base-2010 figure onto base 2015 is measured rather than assumed, and measured twice. That second measurement is what says whether the splice is sound: across the thirteen functions the two overlap years give factors agreeing to better than half a percent, most to a tenth.

`basis` says whether a figure was published on base 2015 or chained onto it, and `chain_disagreement` carries the gap between the two measurements of that function's factor. A reader comparing 2013 with 2022 is relying on it, so it is a column rather than a footnote.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `year` | int64 | — | derived | Calendar year the observation refers to. |
| `function_code` | int64 | — | derived | COICOP function 1-12, matching `tn_consumption_panel`. Code 0 is INS's own all-items total, kept because it cross-checks against `tn_cpi_annual`. |
| `function` | str | — | derived | English name of the COICOP function. |
| `index` | float64 | index, base year = 100 | derived | Consumer price index. Reads 100.0 in its own base year. |
| `base_year` | int64 | — | derived | Year in which this index series equals 100. INS publishes the same price series on eight bases side by side; they are rescalings of one series, not eight measurements, so a chart must pick one and stay on it. |
| `basis` | str | — | derived | — |
| `chain_disagreement` | float64 | — | derived | — |
