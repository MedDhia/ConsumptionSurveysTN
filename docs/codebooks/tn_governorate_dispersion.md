# Between-governorate dispersion of each indicator, 1994–2023

`data/processed/tn_governorate_dispersion.csv` — 2,342 rows × 12 columns

How unequally each indicator is distributed across governorates, one row per indicator, basis, geography and year — the outcome series for a study of regional inequality.

Four measures, because no single one is neutral. `theil_weighted` and `cv_weighted` weight governorates by population, which is the version to report: unweighted dispersion treats Tozeur and Tunis as one observation each, answering a question about administrative units rather than about people. `cv_unweighted` is carried beside them precisely because the choice changes the answer and should be visible. `tail_ratio` is the mean of the top three governorates over the mean of the bottom three — no distributional assumption, and readable aloud.

**A dispersion value is only produced for a complete year.** A measure computed over whichever governorates happened to be printed moves when *coverage* moves, and Kasserine dropping out of one edition would register as inequality falling — an artefact indistinguishable from the finding once it is in a chart. Incomplete years keep their row and lose only their dispersion columns, so `complete` and `governorates` let a reader see exactly what is excluded.

`theil_weighted` is empty where any governorate reports none of something. The zero is usually real — Tozeur genuinely has no cinema screens in some years — and a log measure has nothing to say about it, so that column is left absent rather than floored to make it computable.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `indicator` | str | — | derived | — |
| `basis` | str | — | derived | — |
| `geography` | str | — | derived | — |
| `year` | int64 | — | derived | Calendar year the observation refers to. |
| `governorates` | int64 | — | derived | — |
| `complete` | bool | — | derived | — |
| `period` | str | — | derived | — |
| `mean` | float64 | — | derived | — |
| `theil_weighted` | float64 | — | derived | — |
| `cv_weighted` | float64 | — | derived | — |
| `cv_unweighted` | float64 | — | derived | — |
| `tail_ratio` | float64 | — | derived | — |
