# Expenditure per person by product and region, four survey waves

`data/processed/tn_expenditure_by_product_region.csv` — 12,832 rows × 4 columns

Mean annual expenditure per person on each product, by grande region, for the 2005, 2010, 2015 and 2021 waves. Values are millimes per person per year, as printed.

**Read from four different documents.** 2021 comes from the spreadsheet annex, which names its columns in French. The other three exist only as Arabic-language PDFs whose tables run right to left, and `pdftotext` reorders the header words badly enough that they cannot be used to say which column is which region.

**So the columns are identified, not assumed.** Each table ends with a grand-total row, and each wave's regional means are published elsewhere; matching the two names every column. This is done per wave because the printed order is not stable — 2005 puts Centre East before Centre West and the later waves reverse them.

**Every row is checked against itself.** The national column must equal the population-weighted mean of the seven regional columns. The weights are recovered by least squares from the table, and land on the true regional population shares to three decimals, which is a check on the column mapping as much as on the arithmetic. Rows that fail are in `tn_regional_products_refused`, not here.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `wave` | int64 | — | derived | — |
| `product_ar` | str | — | derived | — |
| `region` | str | — | `pov_2021.dta` → `region` | «region» |
| `expenditure_pc_millimes` | float64 | — | derived | — |

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
