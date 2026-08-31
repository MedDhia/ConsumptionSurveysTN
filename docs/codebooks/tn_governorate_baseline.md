# Pre-revolution starting point and region of each governorate

`data/processed/tn_governorate_baseline.csv` — 648 rows × 6 columns

Each governorate's pre-revolution starting point, per indicator: its mean per head over 2005–2010, its rank on that, its region and whether it is coastal.

These are the pre-determined characteristics a differential design needs. The 2011 revolution is simultaneous and national, so there is no untreated governorate and no average effect to recover; what the data can identify is how governorates that differed *beforehand* diverged afterwards. The baseline window closes in 2010, so nothing in it is post-treatment.

`region` is INS's own grouping into seven grandes régions. `baseline_per_head` and `baseline_rank` are read off the data. `littoral` is the one coding decision — the standard coastal/interior divide, with Manouba counted coastal as part of Grand Tunis and Zaghouan interior despite its Nord-Est grouping. It is spelled out in the source rather than buried, because it is contestable.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `indicator` | str | — | derived | — |
| `governorate` | str | — | derived | — |
| `baseline_per_head` | float64 | — | derived | — |
| `region` | str | — | `pov_2021.dta` → `region` | «region» |
| `littoral` | bool | — | derived | — |
| `baseline_rank` | int64 | — | derived | — |

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
