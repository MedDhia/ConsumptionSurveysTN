"""Build every dataset and its codebook.

    python -m consumptiontn.cli fetch            # download the INS artefacts
    python -m consumptiontn.cli fetch --force    # re-download even if already present
    python -m consumptiontn.cli build            # build datasets + codebooks
    python -m consumptiontn.cli verify           # re-check raw files against the manifest
    python -m consumptiontn.cli check-upstream   # has INS republished anything?

Every dataset is written to ``data/processed`` in two formats: CSV, so it opens in R,
Python, Stata or a spreadsheet with no extra package; and Parquet, which keeps dtypes and
is far faster to load.

One exception on the CSV side. ``tn_hbs_2021_expenditure`` is 3.26M rows and 419 MB as
plain CSV, past GitHub's 100 MB per-file limit, so it is written gzipped. Both languages
read that transparently -- ``pandas.read_csv`` sniffs the extension, and R's
``read.csv(gzfile(...))`` and ``readr::read_csv`` both handle it.
"""

from __future__ import annotations

import sys

import pandas as pd

from . import (
    build_dwelling,
    build_expenditure,
    build_household,
    build_individual,
    build_labour,
    build_panel,
    build_prices,
    build_yearbook,
    codebook,
    download,
    extract_pdf,
    panel_sources,
)
from .config import PROCESSED_DIR

INTROS = {
    "tn_hbs_2021_household": (
        "One row per surveyed household. The workhorse file: expenditure, poverty status, "
        "head characteristics, composition and budget shares.\n\n"
        "**Weights.** Use `weight_pop` for per-person statistics and `weight_hh` for "
        "household-unit statistics. Weighting `expenditure_pc` by `weight_pop` reproduces "
        "INS's headline 5,468 DT; weighting it by `weight_hh` gives 6,164 DT, a different "
        "quantity that INS does not publish.\n\n"
        "**Units.** All monetary columns are dinars. The source file stores millimes."
    ),
    "tn_hbs_2021_expenditure": (
        "One row per household × product acquisition, annualised.\n\n"
        "**The annualisation matters.** The source variable `v407` is the amount observed "
        "over the diary window for its questionnaire table; `frequence` is the multiplier "
        "that turns it into a yearly figure. `expenditure_annual_dt` applies it. Summing "
        "the raw `v407` instead understates household totals by roughly three quarters.\n\n"
        "48,053 of the 3,308,405 source rows have neither a product code nor an amount — "
        "questionnaire lines opened but never filled — and are dropped."
    ),
    "tn_hbs_2021_expenditure_by_function": (
        "One row per household, with annual expenditure and budget share for each of the "
        "twelve COICOP consumption functions. Summing the twelve reproduces the household "
        "total in `tn_hbs_2021_household` to within half a millime."
    ),
    "tn_hbs_2021_products": (
        "The 5-digit product nomenclature (1,446 products) with each product's COICOP "
        "function.\n\n"
        "The function is the product code's leading digits, with one documented exception: "
        "INS counts nine ready-to-eat items coded 11171–11179 (pâtisserie, crêpe, pizza, "
        "brik, ice cream and so on) under food rather than under restaurants and cafés. "
        "The override is read off the `DPA_5Cfiffres` sheet of INS's own Annexe 3 and "
        "moves 32.3 DT per person; without it, two of the twelve published function "
        "totals do not reproduce."
    ),
    "tn_hbs_2021_individuals": (
        "One row per household member (65,524), combining the roster with the education "
        "and health modules.\n\n"
        "**Coverage differs by module.** The roster and education module cover all 65,524 "
        "individuals; the health module covers 54,041, because its questions were not put "
        "to the youngest children. Health columns are missing outside that scope — a fact "
        "about the survey, not a defect in the extraction."
    ),
    "tn_hbs_2021_dwelling": (
        "One row per household: dwelling type and materials, tenure, water, sanitation, "
        "energy, distance to public services, and ownership of 15 durable goods.\n\n"
        "Despite sitting with the individual education and health modules on the INS "
        "download page, `microdonnees_condvie.dta` is household-level."
    ),
    "tn_consumption_panel": (
        "Long indicator panel, 1985–2021. One row per wave × geography × milieu × "
        "subgroup × indicator.\n\n"
        "**Read the `basis` column first.** `recomputed` rows are calculated here from the "
        "2021 microdata; `published` rows are transcribed from an INS document named in "
        "`source_key` and `source_table`. 2021 appears in both forms deliberately, so the "
        "reproduction is visible rather than asserted.\n\n"
        "**Read the `methodology` column second.** INS revised its poverty methodology in "
        "2011. The 2005 volume reports national poverty of 3.8% for 2005; the 2021 note "
        "reports 23.1% for the same year on the revised basis. Rows are tagged `pre-2011` "
        "and `revised (2011)`. Plotting them on one line would be wrong.\n\n"
        "Waves 1968, 1975 and 1980 were conducted but nothing from them is published on "
        "ins.tn, so they have no rows. See `tn_wave_coverage`."
    ),
    "tn_wave_coverage": (
        "What this project could find published for each EBCNV wave since 1968. The "
        "honest map of the gaps."
    ),
    "tn_poverty_delegations_2015": (
        "Poverty and school-dropout rates for 253 delegations across 23 governorates, "
        "extracted from the 2020 poverty map.\n\n"
        "**These are modelled small-area estimates, not survey estimates.** EBCNV is "
        "designed to be representative at the region × milieu level; anything below that "
        "comes from a small-area model combining EBCNV 2015 with the 2014 census. Use "
        "them for description and mapping, not as if they carried survey standard errors. "
        "Siliana is absent because its table in the source report has dropout rates only."
    ),
    "tn_cpi_annual": (
        "Consumer price index for Tunisia, 1999–2023, on each of the eight base years INS "
        "publishes side by side, read from the 2023 statistical yearbook.\n\n"
        "**Pick one base year and stay on it.** The eight columns are the same series "
        "rescaled, not eight different measurements; mixing them produces nonsense. Each "
        "base year reads exactly 100.0 in its own year, which the builder asserts.\n\n"
        "This is a price level, not a quantity: it says what a fixed basket cost, not what "
        "anyone bought. Pair it with the budget shares in `tn_consumption_panel`."
    ),
    "tn_cpi_by_division": (
        "Price index for each of the twelve COICOP consumption functions, 2021–2023, on "
        "base 2015 = 100, with the weights INS used to aggregate them.\n\n"
        "The functions match `tn_consumption_panel`'s `COICOP function` subgroup exactly, "
        "so price change and budget-share change can be set side by side. Because 2015 is "
        "the base and 2021 an EBCNV wave, the 2021 column reads directly as the price "
        "change between two survey waves.\n\n"
        "`weight_per_100000` is INS's expenditure weight and sums to 100,000 across the "
        "twelve. `function_code` 0 is INS's own all-items total, kept because it "
        "cross-checks against `tn_cpi_annual`."
    ),
    "tn_unemployment_annual": (
        "Unemployment rate by education level and by sex, 2011–2023, surveyed each May, "
        "spliced from the 2015, 2019 and 2023 statistical yearbooks.\n\n"
        "**This series does not reach back before the revolution.** The 2005, 2010 and "
        "2012 editions carry no unemployment table — checked in the documents, not "
        "assumed. 2011 is the earliest year available, so this describes the period since "
        "the revolution and cannot be used to compare across it.\n\n"
        "Editions overlap: 2015 appears in two of them and 2019 in two. The builder "
        "requires the overlapping years to agree exactly, which is what verifies that the "
        "right column was read from each volume."
    ),
    "tn_yearbook_tables": (
        "Every numbered table heading found in the 22 statistical yearbooks, with the "
        "edition and the page it appears on \u2014 whether or not this pipeline extracts "
        "its data.\n\n"
        "Read from the body pages rather than from each edition's contents list, so the "
        "page number is observed rather than transcribed, and a table missing from the "
        "contents is still indexed.\n\n"
        "**Table numbers are not stable across editions.** 2010's 6.1.1 is 2023's 6.1.5. "
        "Match on the title, never on the number."
    ),
    "tn_yearbook_series": (
        "Values extracted from the yearbooks' tables: one row per table \u00d7 row label "
        "\u00d7 column \u00d7 year, across all 22 editions.\n\n"
        "**Column shapes.** Where the columns are years, `column_label` is that year and "
        "the table carries several years at once. Where they are school or judicial "
        "years \u2014 written by INS as `24-23` for 2023/24 \u2014 `column_label` keeps that "
        "notation and `year` is the calendar year it starts in. Where they are a "
        "classification \u2014 age bands, indicator codes \u2014 the table describes a single "
        "year taken from the page rather than from the edition's cover.\n\n"
        "**`label_inferred` marks a weaker row.** Some tables print a row's label above "
        "its numbers, or wrapped around them, rather than beside them. Those labels are "
        "reassembled from the neighbouring lines, which is less certain than reading one "
        "off the same line \u2014 so they are flagged, and where two rows in a table would "
        "end up with the same reassembled label the rows are dropped rather than "
        "guessed at.\n\n"
        "**Read `agreement` before using a number.** Each edition carries a five-year "
        "window, so most cells are printed in two to five separate volumes. `confirmed` "
        "means every edition that printed the cell printed the same value \u2014 an "
        "independent corroboration, and the strongest guarantee here. `revised` means they "
        "differ slightly and the most recent edition's value is used, which is INS "
        "revising its own figure. `single source` means only one edition carries it "
        "(1998 and 2023 by construction, and any table that appeared once), so nothing "
        "corroborates it.\n\n"
        "Almost every classification cell is `single source`, and correctly so: table "
        "1.4 in the 2023 edition is the population at 1.7.2023 while the same table in "
        "the 2019 edition is the population at 1.7.2019. Those are different data, so "
        "the cell is never printed twice and nothing can cross-check it.\n\n"
        "Cells where editions disagreed by more than 10% are **not here**: that is the "
        "signature of a misparse rather than a revision, and they are listed in "
        "`tn_yearbook_coverage` instead.\n\n"
        "`row_kind` marks `aggregate` rows \u2014 totals, subtotals, regional groupings and "
        "`dont` sub-rows. Summing a table without filtering them roughly double-counts.\n\n"
        "`provisional` carries INS's own asterisk. Note that provisional figures are "
        "sometimes last year's value carried forward, which would otherwise look like a "
        "real flat segment in a series."
    ),
    "tn_yearbook_coverage": (
        "What was attempted, what was extracted, and what was refused \u2014 the honest map "
        "of how much of the corpus this pipeline actually reads.\n\n"
        "The parser is deliberately strict, and this table is the record of what that "
        "strictness cost. A row is only accepted when the page's year header parses and "
        "the row yields exactly as many numbers as there are year columns. Ellipses for "
        "missing years, footnote digits glued to a label, and two values printed with no "
        "separator between them all fail that test \u2014 which is the intent, because each "
        "one otherwise parses into a plausible wrong number.\n\n"
        "`values_in_conflict` counts cells removed because editions disagreed by more "
        "than 10%. A non-zero count is a signal to read that table by hand, not evidence "
        "that INS is inconsistent."
    ),
}

TITLES = {
    "tn_hbs_2021_household": "Household core — EBCNV 2021",
    "tn_hbs_2021_expenditure": "Product-level expenditure — EBCNV 2021",
    "tn_hbs_2021_expenditure_by_function": "Expenditure by COICOP function — EBCNV 2021",
    "tn_hbs_2021_products": "Product nomenclature — EBCNV 2021",
    "tn_hbs_2021_individuals": "Individuals: demographics, education, health — EBCNV 2021",
    "tn_hbs_2021_dwelling": "Dwelling, amenities and durables — EBCNV 2021",
    "tn_consumption_panel": "Consumption and poverty indicator panel, 1985–2021",
    "tn_wave_coverage": "EBCNV wave coverage, 1968–2021",
    "tn_poverty_delegations_2015": "Delegation-level poverty, 2015 small-area estimates",
    "tn_cpi_annual": "Consumer price index, 1999–2023",
    "tn_cpi_by_division": "Consumer price index by COICOP function, 2021–2023",
    "tn_unemployment_annual": "Unemployment by education and sex, 2011–2023",
    "tn_yearbook_tables": "Statistical yearbook table catalogue, 2001–2023",
    "tn_yearbook_series": "Statistical yearbook series, cross-checked across editions",
    "tn_yearbook_coverage": "Statistical yearbook extraction coverage",
}

# Datasets whose plain CSV would exceed GitHub's 100 MB per-file limit. Written as
# .csv.gz instead; pandas and R both read that without ceremony.
GZIP_CSV = {"tn_hbs_2021_expenditure"}


def _write(name: str, df: pd.DataFrame) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    extension = "csv.gz" if name in GZIP_CSV else "csv"
    # gzip stamps an mtime into its header, so a default-compressed file differs byte for
    # byte on every rebuild even when the CSV inside is identical -- which trips the
    # pipeline's "committed outputs match a fresh build" check. Pin it to 0.
    compression = {"method": "gzip", "mtime": 0} if name in GZIP_CSV else "infer"
    df.to_csv(PROCESSED_DIR / f"{name}.{extension}", index=False, compression=compression)
    df.to_parquet(PROCESSED_DIR / f"{name}.parquet", index=False)
    codebook.write(name, df, title=TITLES[name], intro=INTROS[name], extension=extension)
    print(f"  {name:<40} {len(df):>9,} rows  -> {name}.{extension} + .parquet")


def build_all() -> dict[str, pd.DataFrame]:
    print("building datasets")
    household = build_household.build()
    by_function = build_expenditure.build_by_function()
    datasets = {
        "tn_hbs_2021_household": household,
        "tn_hbs_2021_expenditure": build_expenditure.build_expenditure_long(),
        "tn_hbs_2021_expenditure_by_function": by_function,
        "tn_hbs_2021_products": build_expenditure.build_products(),
        "tn_hbs_2021_individuals": build_individual.build(),
        "tn_hbs_2021_dwelling": build_dwelling.build(),
        "tn_consumption_panel": build_panel.build(household=household, by_function=by_function),
        "tn_wave_coverage": panel_sources.WAVE_COVERAGE,
        "tn_poverty_delegations_2015": extract_pdf.delegation_poverty(),
    }
    cpi_annual, cpi_divisions = build_prices.build()
    datasets["tn_cpi_annual"] = cpi_annual
    datasets["tn_cpi_by_division"] = cpi_divisions
    datasets["tn_unemployment_annual"] = build_labour.build()
    tables, series, coverage = build_yearbook.build()
    datasets["tn_yearbook_tables"] = tables
    datasets["tn_yearbook_series"] = series
    datasets["tn_yearbook_coverage"] = coverage
    for name, df in datasets.items():
        _write(name, df)
    return datasets


def main(argv: list[str]) -> int:
    command = argv[1] if len(argv) > 1 else "build"
    flags = set(argv[2:])
    if command == "fetch":
        download.fetch_all(force="--force" in flags)
    elif command == "build":
        build_all()
    elif command == "verify":
        problems = download.verify()
        if problems:
            print("\n".join(problems))
            return 1
        print("all raw files match the manifest")
    elif command == "check-upstream":
        changed = download.check_upstream()
        if changed:
            print(
                "INS has republished: "
                + ", ".join(changed)
                + "\n  Re-run `make fetch build` and check whether the numbers moved "
                "before committing the new manifest."
            )
            return 1
        print(f"all {len(download.SOURCES)} sources match the committed manifest")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
