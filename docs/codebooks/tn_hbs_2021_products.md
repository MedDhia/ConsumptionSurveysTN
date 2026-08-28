# Product nomenclature — EBCNV 2021

`data/processed/tn_hbs_2021_products.csv` — 1,446 rows × 5 columns

The 5-digit product nomenclature (1,446 products) with each product's COICOP function.

The function is the product code's leading digits, with one documented exception: INS counts nine ready-to-eat items coded 11171–11179 (pâtisserie, crêpe, pizza, brik, ice cream and so on) under food rather than under restaurants and cafés. The override is read off the `DPA_5Cfiffres` sheet of INS's own Annexe 3 and moves 32.3 DT per person; without it, two of the twelve published function totals do not reproduce.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `product_code` | int64 | — | `produit2021_plus.dta` → `v406` | «code produit 5 chiffres» |
| `product_label_fr` | str | — | `code_produit.dta` → `libel_prdt_5` | «libellé produit» |
| `consumption_function_code` | int64 | — | derived | COICOP function 1-12, from the product code with the INS overrides applied. |
| `consumption_function` | str | — | derived | English name of the COICOP function. |
| `consumption_function_fr` | str | — | derived | French name of the COICOP function as INS writes it. |
