# Thirty indicators for the 24 governorates, 1994–2023

`data/processed/tn_governorate_panel.csv` — 34,031 rows × 9 columns

Thirty indicators for all 24 governorates, 1994–2023, drawn out of the statistical yearbooks: population, schooling, employment, libraries, road casualties, banking, sport and communications. Ten of them run the full 1995–2023.

This is `tn_yearbook_series` made usable. The same numbers are there, but reaching them means filtering 174,473 rows on a French title you would have to know, and working out whether a given table's columns are years or something else. Here the shape is settled: one row per governorate, year and indicator, under English names **read off the printed page rather than inferred from the title**, which is a real distinction — the job-placements table still carries a title saying it breaks down by profession, from an edition where it did.

**86% of cells are confirmed** by two or more editions printing the same figure. The check that runs over everything at once is the printed national total: the 24 governorates must sum to the "Total" row of their own table. That found three faults nothing else could, all published in `tn_governorate_refused` rather than shipped — including a year of money orders where a column had been shuffled, and a single misread cell in a table printed by only one edition.

Tables that look like governorate tables and are not are left out and named in the module: the three justice tables are by **court of first instance**, so Grombalia appears and Tunis is split in two.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `governorate` | str | — | derived | — |
| `year` | int64 | — | derived | Calendar year the observation refers to. |
| `indicator` | str | — | derived | — |
| `breakdown` | str | — | derived | Which yearbook table the row came from: `education` or `sex`. |
| `value` | float64 | — | derived | — |
| `unit` | str | — | derived | — |
| `n_editions` | int64 | — | derived | How many editions printed this cell. More than one means corroborated. |
| `agreement` | str | — | derived | `confirmed` (editions agree), `revised` (they differ slightly; newest used), or `single source` (nothing corroborates it). |
| `source_title` | str | — | derived | — |
