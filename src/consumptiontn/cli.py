"""Build every dataset and its codebook.

    python -m consumptiontn.cli fetch      # download the INS artefacts
    python -m consumptiontn.cli build      # build datasets + codebooks
    python -m consumptiontn.cli verify     # re-check raw files against the manifest

Outputs land in ``data/processed`` as CSV, plus Parquet for the two large files.
``tn_hbs_2021_expenditure`` (3.26M rows) is written as Parquet only and is not committed
-- it is a two-minute rebuild from the raw archive.
"""

from __future__ import annotations

import sys

import pandas as pd

from . import build_dwelling, build_expenditure, build_household, build_individual, build_panel, codebook, download, extract_pdf, panel_sources
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
}

# Files large enough that CSV is the wrong default.
PARQUET_ONLY = {"tn_hbs_2021_expenditure"}


def _write(name: str, df: pd.DataFrame) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if name in PARQUET_ONLY:
        df.to_parquet(PROCESSED_DIR / f"{name}.parquet", index=False)
    else:
        df.to_csv(PROCESSED_DIR / f"{name}.csv", index=False)
        df.to_parquet(PROCESSED_DIR / f"{name}.parquet", index=False)
    extension = "parquet" if name in PARQUET_ONLY else "csv"
    path = codebook.write(name, df, title=TITLES[name], intro=INTROS[name], extension=extension)
    print(f"  {name:<40} {len(df):>9,} rows  -> {path.name}")


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
    for name, df in datasets.items():
        _write(name, df)
    return datasets


def main(argv: list[str]) -> int:
    command = argv[1] if len(argv) > 1 else "build"
    if command == "fetch":
        download.fetch_all()
    elif command == "build":
        build_all()
    elif command == "verify":
        problems = download.verify()
        if problems:
            print("\n".join(problems))
            return 1
        print("all raw files match the manifest")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
