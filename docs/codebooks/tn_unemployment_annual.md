# Unemployment by education and sex, 2011–2023

`data/processed/tn_unemployment_annual.csv` — 104 rows × 6 columns

Unemployment rate by education level and by sex, 2011–2023, surveyed each May, spliced from the 2015, 2019 and 2023 statistical yearbooks.

**This series does not reach back before the revolution.** The 2005, 2010 and 2012 editions carry no unemployment table — checked in the documents, not assumed. 2011 is the earliest year available, so this describes the period since the revolution and cannot be used to compare across it.

Editions overlap: 2015 appears in two of them and 2019 in two. The builder requires the overlapping years to agree exactly, which is what verifies that the right column was read from each volume.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `year` | int64 | — | derived | Calendar year the observation refers to. |
| `breakdown` | str | — | derived | Which yearbook table the row came from: `education` or `sex`. |
| `group` | str | — | derived | Category within the breakdown. `all` is that table's own total row. |
| `unemployment_rate` | float64 | percent | derived | Unemployed as a percentage of the labour force, surveyed in May of that year. |
| `source_key` | str | — | derived | Key of the source document in `src/consumptiontn/config.py`. |
| `source_table` | str | — | derived | Table number within that document, as INS numbers it. |
