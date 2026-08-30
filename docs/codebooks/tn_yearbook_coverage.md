# Statistical yearbook extraction coverage

`data/processed/tn_yearbook_coverage.csv` — 1,254 rows × 6 columns

What was attempted, what was extracted, and what was refused — the honest map of how much of the corpus this pipeline actually reads.

The parser is deliberately strict, and this table is the record of what that strictness cost. A row is only accepted when the page's year header parses and the row yields exactly as many numbers as there are year columns. Ellipses for missing years, footnote digits glued to a label, and two values printed with no separator between them all fail that test — which is the intent, because each one otherwise parses into a plausible wrong number.

`values_in_conflict` counts cells removed because editions disagreed by more than 10%. A non-zero count is a signal to read that table by hand, not evidence that INS is inconsistent.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `title_fr` | str | — | derived | Normalised French title. The stable key across editions. |
| `editions` | int64 | — | derived | How many editions this table appears in. |
| `values_read` | int64 | — | derived | Cells parsed from this table before reconciliation. |
| `values_kept` | int64 | — | derived | Cells that survived reconciliation and appear in the series. |
| `values_in_conflict` | int64 | — | derived | Cells dropped because editions disagreed by more than 10%. |
| `status` | str | — | derived | Whether this table was extracted, extracted with conflicts, or not at all. |
