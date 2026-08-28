# Expenditure by COICOP function — EBCNV 2021

`data/processed/tn_hbs_2021_expenditure_by_function.csv` — 17,394 rows × 26 columns

One row per household, with annual expenditure and budget share for each of the twelve COICOP consumption functions. Summing the twelve reproduces the household total in `tn_hbs_2021_household` to within half a millime.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `hh_id` | int64 | — | `pov_2021.dta` → `identif_menage` | «identifiant menage» |
| `exp_food_01` | float64 | dinars per year | derived | Annual household expenditure on COICOP function 01. |
| `exp_alcohol_02` | float64 | dinars per year | derived | Annual household expenditure on COICOP function 02. |
| `exp_clothing_03` | float64 | dinars per year | derived | Annual household expenditure on COICOP function 03. |
| `exp_housing_04` | float64 | dinars per year | derived | Annual household expenditure on COICOP function 04. |
| `exp_furniture_05` | float64 | dinars per year | derived | Annual household expenditure on COICOP function 05. |
| `exp_health_06` | float64 | dinars per year | derived | Annual household expenditure on COICOP function 06. |
| `exp_transport_07` | float64 | dinars per year | derived | Annual household expenditure on COICOP function 07. |
| `exp_communication_08` | float64 | dinars per year | derived | Annual household expenditure on COICOP function 08. |
| `exp_recreation_09` | float64 | dinars per year | derived | Annual household expenditure on COICOP function 09. |
| `exp_education_10` | float64 | dinars per year | derived | Annual household expenditure on COICOP function 10. |
| `exp_restaurants_11` | float64 | dinars per year | derived | Annual household expenditure on COICOP function 11. |
| `exp_other_12` | float64 | dinars per year | derived | Annual household expenditure on COICOP function 12. |
| `exp_total` | float64 | — | derived | — |
| `share_food_01` | float64 | fraction of 1 | derived | Budget share of COICOP function 01. |
| `share_alcohol_02` | float64 | fraction of 1 | derived | Budget share of COICOP function 02. |
| `share_clothing_03` | float64 | fraction of 1 | derived | Budget share of COICOP function 03. |
| `share_housing_04` | float64 | fraction of 1 | derived | Budget share of COICOP function 04. |
| `share_furniture_05` | float64 | fraction of 1 | derived | Budget share of COICOP function 05. |
| `share_health_06` | float64 | fraction of 1 | derived | Budget share of COICOP function 06. |
| `share_transport_07` | float64 | fraction of 1 | derived | Budget share of COICOP function 07. |
| `share_communication_08` | float64 | fraction of 1 | derived | Budget share of COICOP function 08. |
| `share_recreation_09` | float64 | fraction of 1 | derived | Budget share of COICOP function 09. |
| `share_education_10` | float64 | fraction of 1 | derived | Budget share of COICOP function 10. |
| `share_restaurants_11` | float64 | fraction of 1 | derived | Budget share of COICOP function 11. |
| `share_other_12` | float64 | fraction of 1 | derived | Budget share of COICOP function 12. |
