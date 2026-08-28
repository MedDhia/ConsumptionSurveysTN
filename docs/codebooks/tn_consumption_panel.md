# Consumption and poverty indicator panel, 1985–2021

`data/processed/tn_consumption_panel.csv` — 759 rows × 13 columns

Long indicator panel, 1985–2021. One row per wave × geography × milieu × subgroup × indicator.

**Read the `basis` column first.** `recomputed` rows are calculated here from the 2021 microdata; `published` rows are transcribed from an INS document named in `source_key` and `source_table`. 2021 appears in both forms deliberately, so the reproduction is visible rather than asserted.

**Read the `methodology` column second.** INS revised its poverty methodology in 2011. The 2005 volume reports national poverty of 3.8% for 2005; the 2021 note reports 23.1% for the same year on the revised basis. Rows are tagged `pre-2011` and `revised (2011)`. Plotting them on one line would be wrong.

Waves 1968, 1975 and 1980 were conducted but nothing from them is published on ins.tn, so they have no rows. See `tn_wave_coverage`.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `wave` | int64 | — | derived | — |
| `geography_level` | str | — | derived | — |
| `geography` | str | — | derived | — |
| `milieu` | str | — | `pov_2021.dta` → `milieu` | «milieu» |
| `subgroup_type` | str | — | derived | — |
| `subgroup` | str | — | derived | — |
| `indicator` | str | — | derived | — |
| `value` | float64 | — | derived | — |
| `unit` | str | — | derived | — |
| `basis` | str | — | derived | — |
| `methodology` | str | — | derived | — |
| `source_key` | str | — | derived | — |
| `source_table` | str | — | derived | — |

## Categorical codes

Every code INS shipped, its original French label, and the English used in the exported file. Codes 9 and 99 mean *non déclaré* throughout the EBCNV questionnaire and are exported as missing.

### `milieu`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | urbain | urban |
| 2 | rural | rural |
