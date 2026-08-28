# Product-level expenditure — EBCNV 2021

`data/processed/tn_hbs_2021_expenditure.parquet` — 3,260,352 rows × 13 columns

One row per household × product acquisition, annualised.

**The annualisation matters.** The source variable `v407` is the amount observed over the diary window for its questionnaire table; `frequence` is the multiplier that turns it into a yearly figure. `expenditure_annual_dt` applies it. Summing the raw `v407` instead understates household totals by roughly three quarters.

48,053 of the 3,308,405 source rows have neither a product code nor an amount — questionnaire lines opened but never filled — and are dropped.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `hh_id` | int64 | — | `pov_2021.dta` → `identif_menage` | «identifiant menage» |
| `product_code` | int64 | — | `produit2021_plus.dta` → `v406` | «code produit 5 chiffres» |
| `product_label_fr` | str | — | `code_produit.dta` → `libel_prdt_5` | «libellé produit» |
| `consumption_function_code` | int64 | — | derived | COICOP function 1-12, from the product code with the INS overrides applied. |
| `consumption_function` | str | — | derived | English name of the COICOP function. |
| `expenditure_annual_dt` | float64 | dinars per year | derived | Annualised expenditure on this product acquisition, in dinars: `v407 (millimes) * frequence / 1000`. The raw `v407` is a diary-period amount, not an annual one. |
| `quantity_grams` | object | grams | `produit2021_plus.dta` → `v408` | «quantite en gr» |
| `frequency` | float64 | — | `produit2021_plus.dta` → `frequence` | «Fréquence Produit» |
| `purchase_place` | categorical | — | `produit2021_plus.dta` → `v403` | «lieu acquisition prdt» |
| `production_origin` | categorical | — | `produit2021_plus.dta` → `v404` | «lieu production» |
| `acquisition_mode` | categorical | — | `produit2021_plus.dta` → `v405` | «origine prdt» |
| `covid_affected` | categorical | — | `produit2021_plus.dta` → `v409` | «depense produit normal/affecte corona» |
| `questionnaire_table` | float64 | — | `produit2021_plus.dta` → `v400` | «code tableau» |

## Categorical codes

Every code INS shipped, its original French label, and the English used in the exported file. Codes 9 and 99 mean *non déclaré* throughout the EBCNV questionnaire and are exported as missing.

### `purchase_place`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | local prive | private shop |
| 2 | grand surface | supermarket |
| 3 | marche fixe | permanent market |
| 4 | marche hebdomadaire | weekly market |
| 5 | exposition | fair or exhibition |
| 6 | en ligne | online |
| 7 | autre lieu acquisition | other |
| 9 | non déclaré | — (mapped to missing) |

### `production_origin`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | tunisie | Tunisia |
| 2 | importee | imported |
| 3 | ne sait pas | does not know |
| 9 | non déclaré | — (mapped to missing) |

### `acquisition_mode`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | achat comptant | purchase, cash |
| 2 | achat credit | purchase, credit |
| 3 | auto production | own production |
| 4 | don | gift |
| 5 | autre origine | other |
| 9 | non déclaré | — (mapped to missing) |

### `covid_affected`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | normal | normal |
| 2 | affectee | affected by COVID-19 |
| 9 | non déclaré | — (mapped to missing) |
