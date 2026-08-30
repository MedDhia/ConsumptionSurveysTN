# Poverty and inequality by region 2000-2010, on the revised 2010 basis

`data/processed/tn_poverty_inequality_2000_2010.csv` — 66 rows × 8 columns

Consumption per head, poverty lines and Gini coefficients by region and by stratum for 2000, 2005 and 2010, from INS's report on the 2010 revision of the poverty line.

**Everything here is on the revised basis.** The 2010 revision changed how the poverty line is built, and the report recomputes 2000 and 2005 to match, so these figures differ from what those waves published at the time on purpose — Grand Tunis in 2005 is 14.6% poor on this basis against 12.3% as published. The `basis` column says so on every row; do not splice them into `tn_consumption_panel` without deciding which basis you want.

**Why it is worth having.** It is the only source in the corpus giving mean consumption per head by region for 2010, the one wave the panel lacks, and the only one giving Gini coefficients by region at all. The Gini figures agree to the last digit with table 11 of the 2010 survey volume, which is an independent printing of the same numbers.

**What is not here.** Tables 7 and 8 (poverty incidence) wrap too irregularly for the layout to say which value belongs to which wave, and are left out rather than guessed at. Where a table sets a second measure beside the first — constant-price aggregates, the Gini of consumption rather than expenditure — only the headline measure is carried.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `indicator` | str | — | derived | — |
| `geography` | str | — | derived | — |
| `year` | int64 | — | derived | Calendar year the observation refers to. |
| `value` | float64 | — | derived | — |
| `standard_error` | object | — | derived | — |
| `unit` | str | — | derived | — |
| `basis` | str | — | derived | — |
| `source_table` | str | — | derived | Table number within that document, as INS numbers it. |
