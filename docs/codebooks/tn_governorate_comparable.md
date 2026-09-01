# Governorate indicators per head and as shares, on two geographies

`data/processed/tn_governorate_comparable.csv` — 54,494 rows × 9 columns

`tn_governorate_panel` made comparable across governorates: every count carried onto a basis that does not simply track population size, one row per governorate, year, indicator, basis and geography.

A count cannot be compared across governorates — Tunis has roughly nine times Tozeur's people, so ranking them on a count of schools mostly ranks them by population. Two normalisations answer that, and they are both here because they trade off against each other. **`per_head`** divides by population and is the quantity anyone means by provision, but it exists only from 2005, leaving six pre-revolution years. **`share_of_national`** is the governorate's share of the national total, needs no denominator, and so runs the full span.

Two geographies, because the map changed. **`as_printed`** is the 24 governorates as INS prints them. **`constant`** adds Manouba back into Ariana — summing the count *and* the population, so the pair is one fixed area whatever the boundary did inside it — giving 23 units on one geography from 1994. `share_of_national` on the constant geography is what reaches **seventeen pre-2011 years**, against six on `per_head`; on the as-printed geography the same basis stops at 2000, because a complete year needs every unit and Manouba does not exist before then.

`money_orders_from_abroad` is deflated to constant 2015 dinars here. It is the one series in the panel denominated in money, and comparing 2003 with 2023 without deflating measures the currency rather than the remittances.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `governorate` | str | — | derived | — |
| `year` | int64 | — | derived | Calendar year the observation refers to. |
| `indicator` | str | — | derived | — |
| `unit` | str | — | derived | — |
| `basis` | str | — | derived | — |
| `value` | float64 | — | derived | — |
| `population_thousands` | float64 | — | derived | — |
| `comparable` | float64 | — | derived | — |
| `geography` | str | — | derived | — |
