# Spatial Gini across regions, by consumption good and wave

`data/processed/tn_spatial_gini_by_product.csv` — 1,604 rows × 5 columns

The Gini coefficient across the seven regions of per-capita spending on each product, one row per product per wave.

**This is a between-region measure, not a between-household one.** It is zero when every region spends the same per head on a good and rises as spending concentrates in some regions. It says nothing about inequality between households inside a region, which is a different and larger quantity.

**Regions are weighted by population**, using shares recovered from the source table itself, so a small region cannot move the measure as much as a large one.

111 products appear in all four waves; use `wave` counts before treating any product as a series. Product names are matched across waves on the Arabic label, which is the only one all four documents print; `product_fr` is filled from the 2021 annex where the same Arabic label appears there.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `wave` | int64 | — | derived | — |
| `product_ar` | str | — | derived | — |
| `product_fr` | str | — | derived | — |
| `expenditure_pc_national` | float64 | — | derived | — |
| `spatial_gini` | float64 | — | derived | — |
