# Consumer and industrial price indices by month, on each printed base

`data/processed/tn_monthly_prices.csv` — 2,604 rows × 10 columns

The consumer price index and the industrial selling price index at monthly frequency, on every base each is printed on — the price channel of the revolution, at the frequency an RD needs.

Prices are the outcome least contaminated by everything else that happened. The strongest monthly count series is tourism, and a tourist arrival responds to the 2015 attacks and the Libyan war as much as to the uprising; prices respond to the thing the uprising was about. Bouazizi was a fruit seller.

**Neither index is chained, and that is measured rather than assumed.** Both were rebased in the period — CPI from 2000 to 2005, IPI from 2000 to 2010 — and this repository already chains across a rebasing where the two bases overlap. Here it would be wrong: the IPI tables overlap in 2010–2012 and the ratio between them is not constant within a sector. Chemicals runs 0.607 to 0.774 across thirty-six months, where a pure rebasing would give one number. INS re-weighted the basket as well as moving the base, so `tn_monthly_rebasing` publishes the factors instead of a splice.

That costs the design nothing, because **one base spans January 2011 on each index**: CPI base 2005 covers 2009–2012 with twenty-four months either side, IPI base 2000 covers 1998–2012 with a hundred and fifty-six before. Estimating on each base apart makes them independent measurements rather than one measurement of an assumed join — and on the IPI they disagree, which is the point of having both.

**The base is verified, not trusted.** Where a column heading states one it is used, and the assignment is then checked against `tn_cpi_annual`, built from a different table: the twelve months of a year must average to the annual index printed for that base. They do, to between 0.01 and 0.37 index points on values near 120. A year that fails is refused, because a monthly series on the wrong base would sit in an RD looking perfectly normal and be wrong by tens of percent.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `series` | str | — | derived | — |
| `group` | str | — | derived | Category within the breakdown. `all` is that table's own total row. |
| `base_year` | int64 | — | derived | Year in which this index series equals 100. INS publishes the same price series on eight bases side by side; they are rescalings of one series, not eight measurements, so a chart must pick one and stay on it. |
| `year` | int64 | — | derived | Calendar year the observation refers to. |
| `month` | int64 | — | derived | — |
| `t` | float64 | — | derived | — |
| `running` | int64 | — | derived | — |
| `treated` | bool | — | derived | — |
| `value` | float64 | — | derived | — |
| `log_value` | float64 | — | derived | — |
