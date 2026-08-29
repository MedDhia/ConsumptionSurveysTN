# Statistical yearbook series, cross-checked across editions

`data/processed/tn_yearbook_series.csv` — 91,414 rows × 12 columns

Values extracted from the yearbooks' year-column tables: one row per table × row label × year, across all 22 editions.

**Read `agreement` before using a number.** Each edition carries a five-year window, so most cells are printed in two to five separate volumes. `confirmed` means every edition that printed the cell printed the same value — an independent corroboration, and the strongest guarantee here. `revised` means they differ slightly and the most recent edition's value is used, which is INS revising its own figure. `single source` means only one edition carries it (1998 and 2023 by construction, and any table that appeared once), so nothing corroborates it.

Cells where editions disagreed by more than 10% are **not here**: that is the signature of a misparse rather than a revision, and they are listed in `tn_yearbook_coverage` instead.

`row_kind` marks `aggregate` rows — totals, subtotals, regional groupings and `dont` sub-rows. Summing a table without filtering them roughly double-counts.

`provisional` carries INS's own asterisk. Note that provisional figures are sometimes last year's value carried forward, which would otherwise look like a real flat segment in a series.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `table_number` | str | — | derived | Table number as printed. NOT stable across editions -- match on title. |
| `table_title` | str | — | derived | Table title as printed, Latin characters only. |
| `title_fr` | str | — | derived | Normalised French title. The stable key across editions. |
| `row_label` | str | — | derived | The row's French label, as printed. |
| `row_kind` | str | — | derived | `data`, or `aggregate` for totals, subtotals and `dont` sub-rows. |
| `year` | int64 | — | derived | Calendar year the observation refers to. |
| `value` | float64 | — | derived | — |
| `provisional` | bool | — | derived | INS marked this figure provisional with an asterisk. |
| `n_editions` | int64 | — | derived | How many editions printed this cell. More than one means corroborated. |
| `agreement` | str | — | derived | `confirmed` (editions agree), `revised` (they differ slightly; newest used), or `single source` (nothing corroborates it). |
| `edition` | int64 | — | derived | Which yearbook edition the value was taken from. |
| `page` | int64 | — | derived | Page of the edition the value was read from. |
