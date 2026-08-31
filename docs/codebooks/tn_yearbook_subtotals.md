# Printed regional subtotals against the governorates they are made of

`data/processed/tn_yearbook_subtotals.csv` — 12,246 rows × 11 columns

Every printed regional subtotal in the corpus beside the sum of the governorates it is made of — 5,847 checks that need no outside source and run over every table carrying both.

**98.96% agree.** All 61 that do not sit in two pages: population by age group in the 2009 edition and again in 2018. Every one of them is a *region* row that disagrees with its parts, not a governorate row, which is why the governorate panel built from the same corpus passes its own checks.

Both figures are published with the gap rather than either being dropped: a sum cannot say which side is misread, and a reader is better served knowing exactly which cells to distrust than having one of them silently removed.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `title_fr` | str | — | derived | Normalised French title. The stable key across editions. |
| `panel` | str | — | derived | — |
| `region` | str | — | `pov_2021.dta` → `region` | «region» |
| `column_label` | str | — | derived | The column this value sat under: the year itself where columns are years, otherwise the classification category (an age band, an indicator code). |
| `year` | int64 | — | derived | Calendar year the observation refers to. |
| `parts_sum` | float64 | — | derived | — |
| `parts_mean` | float64 | — | derived | — |
| `printed` | float64 | — | derived | — |
| `gap` | float64 | — | derived | — |
| `additive` | bool | — | derived | — |
| `agrees` | object | — | derived | — |

## Categorical codes

Every code INS shipped, its original French label, and the English used in the exported file. Codes 9 and 99 mean *non déclaré* throughout the EBCNV questionnaire and are exported as missing.

### `region`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | Grand Tunis | Grand Tunis |
| 2 | Nord Est | North East |
| 3 | Nord Ouest | North West |
| 4 | Centre Est | Centre East |
| 5 | Centre Ouest | Centre West |
| 6 | Sud Est | South East |
| 7 | Sud ouest | South West |
