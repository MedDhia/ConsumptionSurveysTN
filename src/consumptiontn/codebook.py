"""Generate a codebook per exported dataset.

Each entry carries the exported English name, the original INS variable it came from,
that variable's French label verbatim, the unit, and -- for categorical columns -- every
code with both its French original and its English translation. The point is that a
reader can go from any column in the output back to the questionnaire without leaving
the document.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyreadstat

from . import labels
from .config import CODEBOOK_DIR
from .extract import find, value_labels

# Where each RENAMES block came from, so the codebook can cite the file.
SOURCE_FILES: dict[str, tuple[str, str]] = {
    "pov_2021": ("ebcnv2021_depenses", "pov_2021.dta"),
    "donnindiv2021": ("ebcnv2021_depenses", "donnindiv2021.dta"),
    "produit2021_plus": ("ebcnv2021_depenses", "produit2021_plus.dta"),
    "code_produit": ("ebcnv2021_depenses", "code_produit.dta"),
    "microdonnees_condvie": ("ebcnv2021_condvie", "microdonnees_condvie.dta"),
    "Education2021": ("ebcnv2021_educsante", "Education2021.dta"),
    "Sante2021": ("ebcnv2021_educsante", "Sante2021.dta"),
}

# Columns this pipeline derives rather than renames.
DERIVED: dict[str, str] = {
    "survey_year": "EBCNV wave, added by the pipeline. Always 2021 in the microdata files.",
    "expenditure_total": "Total annual household expenditure, `expenditure_pc * hh_size`. Dinars.",
    "consumption_total": "Total annual household consumption, `consumption_pc * hh_size`. Dinars.",
    "n_children_0_14": "Household members aged 0-14, counted from the individual roster.",
    "n_working_age_15_59": "Household members aged 15-59, counted from the individual roster.",
    "n_elderly_60_plus": "Household members aged 60 and over, counted from the individual roster.",
    "n_female": "Female household members, counted from the individual roster.",
    "food_share": "Share of annual household expenditure on COICOP function 01. Fraction of 1.",
    "expenditure_annual_dt": (
        "Annualised expenditure on this product acquisition, in dinars: "
        "`v407 (millimes) * frequence / 1000`. The raw `v407` is a diary-period amount, "
        "not an annual one."
    ),
    "consumption_function_code": (
        "COICOP function 1-12, from the product code with the INS overrides applied."
    ),
    "consumption_function": "English name of the COICOP function.",
    "consumption_function_fr": "French name of the COICOP function as INS writes it.",
    "product_label_fr": "INS product label, verbatim French.",
    "weight": "Household extrapolation factor (`v700`), applied to each member of the household.",
    "weight_hh": "Household extrapolation factor (`v700`). Use for household-unit statistics.",
    "weight_pop": (
        "Individual extrapolation factor (`v701`), equal to `weight_hh * hh_size`. "
        "Use for per-person statistics: mean per-capita expenditure, poverty headcount."
    ),
    # Yearbook-derived series. These come from published tables in the Annuaire
    # Statistique de la Tunisie rather than from microdata, so they have no .dta origin.
    "year": "Calendar year the observation refers to.",
    "base_year": (
        "Year in which this index series equals 100. INS publishes the same price series "
        "on eight bases side by side; they are rescalings of one series, not eight "
        "measurements, so a chart must pick one and stay on it."
    ),
    "index": "Consumer price index. Reads 100.0 in its own base year.",
    "weight_per_100000": (
        "INS's expenditure weight for this COICOP function, in parts per 100,000. "
        "Sums to exactly 100,000 across the twelve functions."
    ),
    "function_code": (
        "COICOP function 1-12, matching `tn_consumption_panel`. Code 0 is INS's own "
        "all-items total, kept because it cross-checks against `tn_cpi_annual`."
    ),
    "function": "English name of the COICOP function.",
    "unemployment_rate": (
        "Unemployed as a percentage of the labour force, surveyed in May of that year."
    ),
    "breakdown": "Which yearbook table the row came from: `education` or `sex`.",
    "group": "Category within the breakdown. `all` is that table's own total row.",
    "source_key": "Key of the source document in `src/consumptiontn/config.py`.",
    "source_table": "Table number within that document, as INS numbers it.",
}

UNITS: dict[str, str] = {
    "expenditure_pc": "dinars per person per year",
    "consumption_pc": "dinars per person per year",
    "expenditure_total": "dinars per year",
    "consumption_total": "dinars per year",
    "poverty_line": "dinars per person per year",
    "extreme_poverty_line": "dinars per person per year",
    "expenditure_annual_dt": "dinars per year",
    "quantity_grams": "grams",
    "head_age": "years",
    "age": "years",
    "scholarship_amount": "dinars per year",
    # Dinars, not millimes. INS's own labels give no unit, and an earlier version of
    # this file guessed millimes. That reading makes a doctor's visit cost 0.04 DT.
    # Checked against the household file, which is definitely in dinars: summed per
    # household, the health module is a median 172 against 1,749 for COICOP function 6
    # -- about 8%, which is what out-of-pocket medical care should be inside a category
    # that also holds hygiene and personal care. On the millimes reading it would be
    # 0.01%.
    "chronic_disease_expenditure": "dinars per year",
    "consultation_expenditure": "dinars per year",
    "medicine_expenditure": "dinars per year",
    "hospital_stay_expenditure": "dinars per year",
    "insurance_reimbursement": "dinars per year",
    "travel_time_to_school_min": "minutes",
    "travel_time_to_water_point_min": "minutes",
    "distance_to_water_point_m": "metres",
    "job_search_duration_months": "months",
    "food_share": "fraction of 1",
    "index": "index, base year = 100",
    "unemployment_rate": "percent",
    "weight_per_100000": "parts per 100,000",
}


def _origin_index() -> dict[str, tuple[str, str, str]]:
    """exported column -> (source .dta, original variable, French label)."""
    index: dict[str, tuple[str, str, str]] = {}
    for block, (key, member) in SOURCE_FILES.items():
        _, meta = pyreadstat.read_dta(str(find(key, member)), metadataonly=True)
        for original, exported in labels.RENAMES[block].items():
            if exported in index:
                continue
            french = (meta.column_names_to_labels.get(original) or "").strip()
            index[exported] = (member, original, french)
    return index


def _value_label_index() -> dict[str, dict]:
    """exported column -> {code: (French label, English label)}."""
    index: dict[str, dict] = {}
    for block, (key, member) in SOURCE_FILES.items():
        _, meta = pyreadstat.read_dta(str(find(key, member)), metadataonly=True)
        for original, exported in labels.RENAMES[block].items():
            set_name = labels.COLUMN_VALUE_SET.get(exported)
            if set_name is None or exported in index:
                continue
            french = value_labels(meta, original)
            english = labels.VALUE_SETS[set_name]
            index[exported] = {
                code: (french.get(code, ""), english.get(code, "— (mapped to missing)"))
                for code in sorted(set(french) | set(english))
            }
    return index


def write(
    name: str,
    df: pd.DataFrame,
    *,
    title: str,
    intro: str,
    out_dir: Path | None = None,
    extension: str = "csv",
) -> Path:
    origins = _origin_index()
    value_index = _value_label_index()
    out_dir = CODEBOOK_DIR if out_dir is None else out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# {title}",
        "",
        f"`data/processed/{name}.{extension}` — {len(df):,} rows × {len(df.columns)} columns",
        "",
        intro.strip(),
        "",
        "## Variables",
        "",
        "| Column | Type | Unit | INS origin | Description |",
        "| --- | --- | --- | --- | --- |",
    ]
    categorical: list[str] = []
    for col in df.columns:
        dtype = "categorical" if str(df[col].dtype) == "category" else str(df[col].dtype)
        unit = UNITS.get(col, "—")
        if col in origins:
            member, original, french = origins[col]
            origin = f"`{member}` → `{original}`"
            description = f"«{french}»" if french else "—"
        else:
            origin = "derived"
            description = DERIVED.get(col, "—")
        if col.startswith("share_"):
            code = col.rsplit("_", 1)[-1]
            description = f"Budget share of COICOP function {code}."
            unit = "fraction of 1"
        if col.startswith("exp_") and col != "exp_total":
            code = col.rsplit("_", 1)[-1]
            description = f"Annual household expenditure on COICOP function {code}."
            unit = "dinars per year"
        lines.append(f"| `{col}` | {dtype} | {unit} | {origin} | {description} |")
        if col in value_index:
            categorical.append(col)

    if categorical:
        lines += ["", "## Categorical codes", "",
                  "Every code INS shipped, its original French label, and the English "
                  "used in the exported file. Codes 9 and 99 mean *non déclaré* "
                  "throughout the EBCNV questionnaire and are exported as missing.", ""]
        for col in categorical:
            lines += [
                f"### `{col}`",
                "",
                "| Code | French (INS) | English (exported) |",
                "| --- | --- | --- |",
            ]
            for code, (french, english) in value_index[col].items():
                lines.append(f"| {code:g} | {french or '—'} | {english} |")
            lines.append("")

    path = out_dir / f"{name}.md"
    path.write_text("\n".join(lines).rstrip() + "\n")
    return path
