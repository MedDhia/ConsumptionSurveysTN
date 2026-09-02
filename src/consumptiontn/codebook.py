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
    "edition": "Which yearbook edition the value was taken from.",
    "chapter": "Yearbook chapter number.",
    "table_number": "Table number as printed. NOT stable across editions -- match on title.",
    "table_title": "Table title as printed, Latin characters only.",
    "title_fr": "Normalised French title. The stable key across editions.",
    "row_label": "The row's French label, as printed.",
    "row_kind": "`data`, or `aggregate` for totals, subtotals and `dont` sub-rows.",
    "column_label": (
        "The column this value sat under: the year itself where columns are years, "
        "otherwise the classification category (an age band, an indicator code)."
    ),
    "provisional": "INS marked this figure provisional with an asterisk.",
    "label_inferred": (
        "The row label was read from a neighbouring line rather than printed beside the "
        "numbers. Weaker evidence than the rest; filter these out if that matters."
    ),
    "n_editions": "How many editions printed this cell. More than one means corroborated.",
    "agreement": (
        "`confirmed` (editions agree), `revised` (they differ slightly; newest used), "
        "or `single source` (nothing corroborates it)."
    ),
    "page": "Page of the edition the value was read from.",
    "editions": "How many editions this table appears in.",
    "values_read": "Cells parsed from this table before reconciliation.",
    "values_kept": "Cells that survived reconciliation and appear in the series.",
    "values_in_conflict": "Cells dropped because editions disagreed by more than 10%.",
    "status": "Whether this table was extracted, extracted with conflicts, or not at all.",
    "period": "`pre` for years before 2011, `post` for 2011 onward. A label, not a design.",
    # Regional inequality at two geographies, and the Theil decomposition beneath it.
    "gini_governorate": "Gini across the 24 governorates, each counting once.",
    "gini_region": (
        "The same Gini across the 7 grandes régions, computed on the same quantity "
        "aggregated: a region's share of the national total is the sum of its "
        "governorates' shares. Nearly always the smaller of the two, because seven units "
        "cannot show the dispersion inside them."
    ),
    "theil_governorate": (
        "Theil-T across the 24 governorates: the quantity that is decomposed. Empty "
        "where any governorate reports none of the thing, because a logarithm has "
        "nothing to say about a zero."
    ),
    "theil_region": "Theil-T across the 7 grandes régions.",
    "theil_between": (
        "The part of `theil_governorate` that lies between the seven regions: "
        "Σ (n_g/n)(μ_g/μ) ln(μ_g/μ). This is the coastal/interior component."
    ),
    "theil_within": (
        "The part of `theil_governorate` that lies inside regions: Σ (n_g/n)(μ_g/μ) T_g."
    ),
    "identity_gap": (
        "abs(between + within − total). Published rather than asserted: it is at machine "
        "precision, and the builder refuses to write the file if it exceeds 1e-9."
    ),
    "between_share": (
        "`theil_between / theil_governorate`. The number a structural change would move: "
        "means inequality shifted *between* regions even where the total held still."
    ),
    "measure": "Which column of `tn_gini_decomposition` this row summarises.",
    "first_year": "First year of the window this row rests on.",
    "last_year": "Last year of the window this row rests on. The windows differ by row.",
    "n_pre": "Years before 2011 behind the `pre` mean.",
    "n_post": "Years from 2011 onward behind the `post` mean.",
    "pre": "Mean of `measure` over the pre-2011 years.",
    "post": "Mean of `measure` over the post-2011 years.",
    "change": "`post − pre`. A difference between two periods, not an effect.",
    "pre_trend_per_decade": (
        "Slope of a line fitted to the pre-2011 years alone, per decade."
    ),
    "predicted": (
        "What that pre-2011 line, extrapolated across the post-2011 years, would give for "
        "`change` on its own."
    ),
    "excess": (
        "`change − predicted`: the part the pre-2011 trend does not already account for. "
        "Read this rather than `change`, or a decade of drift gets dated to the revolution."
    ),
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
