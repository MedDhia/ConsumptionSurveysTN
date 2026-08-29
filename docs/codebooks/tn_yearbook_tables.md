# Statistical yearbook table catalogue, 2001–2023

`data/processed/tn_yearbook_tables.csv` — 8,391 rows × 5 columns

Every numbered table heading found in the 22 statistical yearbooks, with the edition and the page it appears on — whether or not this pipeline extracts its data.

Read from the body pages rather than from each edition's contents list, so the page number is observed rather than transcribed, and a table missing from the contents is still indexed.

**Table numbers are not stable across editions.** 2010's 6.1.1 is 2023's 6.1.5. Match on the title, never on the number.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `edition` | int64 | — | derived | Which yearbook edition the value was taken from. |
| `table_number` | str | — | derived | Table number as printed. NOT stable across editions -- match on title. |
| `chapter` | str | — | derived | Yearbook chapter number. |
| `table_title` | str | — | derived | Table title as printed, Latin characters only. |
| `page` | int64 | — | derived | Page of the edition the value was read from. |
