# Statistical yearbook series, cross-checked across editions

`data/processed/tn_yearbook_series.csv` — 174,473 rows × 14 columns

Values extracted from the yearbooks' tables: one row per table × row label × column × year, across all 22 editions.

**Column shapes.** Where the columns are years, `column_label` is that year and the table carries several years at once. Where they are school or judicial years — written by INS as `24-23` for 2023/24 — `column_label` keeps that notation and `year` is the calendar year it starts in. Where they are a classification — age bands, indicator codes — the table describes a single year taken from the page rather than from the edition's cover.

**`label_inferred` marks a weaker row.** Some tables print a row's label above its numbers, or wrapped around them, rather than beside them. Those labels are reassembled from the neighbouring lines, which is less certain than reading one off the same line — so they are flagged, and where two rows in a table would end up with the same reassembled label the rows are dropped rather than guessed at.

**Read `agreement` before using a number.** Each edition carries a five-year window, so most cells are printed in two to five separate volumes. `confirmed` means every edition that printed the cell printed the same value — an independent corroboration, and the strongest guarantee here. `revised` means they differ slightly and the most recent edition's value is used, which is INS revising its own figure. `single source` means only one edition carries it (1998 and 2023 by construction, and any table that appeared once), so nothing corroborates it.

Almost every classification cell is `single source`, and correctly so: table 1.4 in the 2023 edition is the population at 1.7.2023 while the same table in the 2019 edition is the population at 1.7.2019. Those are different data, so the cell is never printed twice and nothing can cross-check it.

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
| `column_label` | str | — | derived | The column this value sat under: the year itself where columns are years, otherwise the classification category (an age band, an indicator code). |
| `year` | int64 | — | derived | Calendar year the observation refers to. |
| `value` | float64 | — | derived | — |
| `provisional` | bool | — | derived | INS marked this figure provisional with an asterisk. |
| `label_inferred` | bool | — | derived | The row label was read from a neighbouring line rather than printed beside the numbers. Weaker evidence than the rest; filter these out if that matters. |
| `n_editions` | int64 | — | derived | How many editions printed this cell. More than one means corroborated. |
| `agreement` | str | — | derived | `confirmed` (editions agree), `revised` (they differ slightly; newest used), or `single source` (nothing corroborates it). |
| `edition` | int64 | — | derived | Which yearbook edition the value was taken from. |
| `page` | int64 | — | derived | Page of the edition the value was read from. |
