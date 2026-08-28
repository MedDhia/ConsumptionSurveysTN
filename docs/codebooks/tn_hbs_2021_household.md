# Household core — EBCNV 2021

`data/processed/tn_hbs_2021_household.csv` — 17,394 rows × 40 columns

One row per surveyed household. The workhorse file: expenditure, poverty status, head characteristics, composition and budget shares.

**Weights.** Use `weight_pop` for per-person statistics and `weight_hh` for household-unit statistics. Weighting `expenditure_pc` by `weight_pop` reproduces INS's headline 5,468 DT; weighting it by `weight_hh` gives 6,164 DT, a different quantity that INS does not publish.

**Units.** All monetary columns are dinars. The source file stores millimes.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `hh_id` | int64 | — | `pov_2021.dta` → `identif_menage` | «identifiant menage» |
| `survey_year` | int64 | — | derived | EBCNV wave, added by the pipeline. Always 2021 in the microdata files. |
| `region` | categorical | — | `pov_2021.dta` → `region` | «region» |
| `milieu` | categorical | — | `pov_2021.dta` → `milieu` | «milieu» |
| `weight_hh` | float64 | — | `pov_2021.dta` → `v700` | «extrapolation menage» |
| `weight_pop` | float64 | — | `pov_2021.dta` → `v701` | «extrapolation individu» |
| `hh_size` | int64 | — | `pov_2021.dta` → `hh_size` | «taille du menage» |
| `hh_size_class` | categorical | — | `pov_2021.dta` → `cat_taille` | «Catégorie Taille» |
| `n_children_0_14` | int64 | — | derived | Household members aged 0-14, counted from the individual roster. |
| `n_working_age_15_59` | int64 | — | derived | Household members aged 15-59, counted from the individual roster. |
| `n_elderly_60_plus` | int64 | — | derived | Household members aged 60 and over, counted from the individual roster. |
| `n_female` | int64 | — | derived | Female household members, counted from the individual roster. |
| `head_sex` | categorical | — | `pov_2021.dta` → `sexe_chef` | «sexe» |
| `head_age` | Int64 | years | `pov_2021.dta` → `age_chef` | «age du chef du menage» |
| `head_marital_status` | categorical | — | `pov_2021.dta` → `etat_mat_chef` | «etat matrimonial du chef du menage» |
| `head_education` | categorical | — | `pov_2021.dta` → `niveau_instr_chef` | «niveau instruction du chef du menage» |
| `head_csp` | categorical | — | `pov_2021.dta` → `csp_chef` | «categorie socioprofessionnelle du chef du menage» |
| `expenditure_pc` | float64 | dinars per person per year | `pov_2021.dta` → `dep_an_pc` | «depense annuelle menage» |
| `expenditure_total` | float64 | dinars per year | derived | Total annual household expenditure, `expenditure_pc * hh_size`. Dinars. |
| `consumption_pc` | float64 | dinars per person per year | `pov_2021.dta` → `conso_an_pc` | «consommation annuelle menage» |
| `consumption_total` | float64 | dinars per year | derived | Total annual household consumption, `consumption_pc * hh_size`. Dinars. |
| `expenditure_bracket` | categorical | — | `pov_2021.dta` → `tranche_dep` | «tranche de depense» |
| `quintile` | int64 | — | `pov_2021.dta` → `quintile` | «5 quantiles of conspc» |
| `decile` | int64 | — | `pov_2021.dta` → `decile` | «10 quantiles of conspc» |
| `poverty_line` | float64 | dinars per person per year | `pov_2021.dta` → `seuilhaut_2021` | «seuil de pauvreté» |
| `extreme_poverty_line` | float64 | dinars per person per year | `pov_2021.dta` → `seuilbas_2021` | «seuil de pauvreté extrême» |
| `poor` | categorical | — | `pov_2021.dta` → `pauv` | «pauvre» |
| `extreme_poor` | categorical | — | `pov_2021.dta` → `pauv_extreme` | «pauv_extreme» |
| `food_share` | float64 | fraction of 1 | derived | Share of annual household expenditure on COICOP function 01. Fraction of 1. |
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

### `milieu`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | urbain | urban |
| 2 | rural | rural |

### `hh_size_class`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | 1-2 personnes | 1-2 persons |
| 2 | 3-4 personnes | 3-4 persons |
| 3 | 5-6 personnes | 5-6 persons |
| 4 | 7-8 personnes | 7-8 persons |
| 5 | 9 et plus | 9 or more persons |

### `head_sex`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | masculin | male |
| 2 | feminin | female |
| 3 | feminin enceinte | female, pregnant |
| 4 | feminin allaitement | female, breastfeeding |
| 9 | non déclaré | — (mapped to missing) |

### `head_marital_status`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | celibataire | single |
| 2 | marie | married |
| 3 | veuf | widowed |
| 4 | divorce | divorced |
| 9 | non déclaré | — (mapped to missing) |

### `head_education`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | neant | none |
| 2 | niveau primaire | primary |
| 3 | niveau secondaire | secondary |
| 4 | niveau superieur | higher |

### `head_csp`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | cadres et professions liberales superieurs | senior managers and professionals |
| 2 | cadres et professions liberales moyens | mid-level managers and professionals |
| 3 | autres employes | other employees |
| 4 |  patrons des petits metiers dans l'industrie, commerce et services | employers in industry, trade and services |
| 5 |  artisans et independants des petits metiers dans l'industrie, commerce et services | own-account workers and artisans in industry, trade and services |
| 6 |  ouvriers non agricoles | non-agricultural workers |
| 7 |  exploitants agricoles | farm operators |
| 8 |  ouvriers agricloes | agricultural workers |
| 9 |  chomeurs | unemployed |
| 10 |  retraites | retired |
| 11 |  autres inactifs | other inactive |

### `expenditure_bracket`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | inferieure-500 dinars | under 500 DT |
| 2 | entre 500 dinars et 750 dinars | 500-750 DT |
| 3 | entre 750 dinars et 1000 dinars | 750-1,000 DT |
| 4 | entre 1000 dinars et 1500 dinars | 1,000-1,500 DT |
| 5 | entre 1500 dinars et 2000 dinars | 1,500-2,000 DT |
| 6 | entre 2000 dinars et 3000 dinars | 2,000-3,000 DT |
| 7 | entre 3000 dinars et 4500 dinars | 3,000-4,500 DT |
| 8 | superieure a 5000 dinars | above 5,000 DT |

### `poor`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 0 | No pauv | not poor |
| 1 | pauv | poor |

### `extreme_poor`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 0 | No pauv_extreme | not extremely poor |
| 1 | pauv_extreme | extremely poor |
