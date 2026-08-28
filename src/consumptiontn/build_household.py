"""Household core: expenditure, poverty status, head characteristics, composition.

Units. ``pov_2021.dta`` stores expenditure in **millimes** (1 dinar = 1,000 millimes)
and stores it *per capita* despite the French variable label reading "depense annuelle
menage". Both are verified against the published figures: weighting ``dep_an_pc`` by the
individual weight ``v701`` gives 5,468 DT, INS's headline national figure.

Weights. ``weight_pop`` (``v701``) is the individual extrapolation factor and equals
``weight_hh * hh_size``. Use ``weight_pop`` for per-person statistics -- mean per-capita
expenditure, poverty headcount -- and ``weight_hh`` for statistics whose unit is the
household. Weighting per-capita expenditure by ``weight_hh`` gives 6,164 DT, which is a
different (and unpublished) quantity: the mean across households rather than persons.
"""

from __future__ import annotations

import pandas as pd

from . import labels
from .build_expenditure import build_by_function
from .extract import find, read_dta

MILLIMES_PER_DINAR = 1000
_MONETARY = [
    "expenditure_pc",
    "consumption_pc",
    "poverty_line",
    "extreme_poverty_line",
]


def household_composition() -> pd.DataFrame:
    """Counts of children, working-age adults and elderly per household."""
    df, _ = read_dta(find("ebcnv2021_depenses", "donnindiv2021.dta"))
    df = df.rename(columns=labels.RENAMES["donnindiv2021"])
    counts = (
        df.assign(
            n_children_0_14=df["age_group"].isin([1, 2]),
            n_working_age_15_59=df["age_group"].eq(3),
            n_elderly_60_plus=df["age_group"].eq(4),
            n_female=df["sex"].eq(2),
        )
        .groupby("hh_id")[
            ["n_children_0_14", "n_working_age_15_59", "n_elderly_60_plus", "n_female"]
        ]
        .sum()
        .astype("int64")
    )
    return counts.reset_index()


def build(by_function: pd.DataFrame | None = None) -> pd.DataFrame:
    df, _ = read_dta(find("ebcnv2021_depenses", "pov_2021.dta"))
    df = df.rename(columns=labels.RENAMES["pov_2021"])

    for col in _MONETARY:
        df[col] = df[col] / MILLIMES_PER_DINAR
    df["expenditure_total"] = df["expenditure_pc"] * df["hh_size"]
    df["consumption_total"] = df["consumption_pc"] * df["hh_size"]

    df["hh_id"] = df["hh_id"].astype("int64")
    df["hh_size"] = df["hh_size"].astype("int64")
    # readstat hands back `age_chef` as object because of its missing values.
    df["head_age"] = pd.to_numeric(df["head_age"], errors="coerce").astype("Int64")
    df = df.merge(household_composition(), on="hh_id", how="left")

    shares = build_by_function() if by_function is None else by_function
    share_cols = ["hh_id"] + [c for c in shares.columns if c.startswith("share_")]
    df = df.merge(shares[share_cols], on="hh_id", how="left")
    df = df.rename(columns={"share_food_01": "food_share"})

    df["survey_year"] = 2021
    df = labels.decode_frame(df)

    ordered = [
        "hh_id",
        "survey_year",
        "region",
        "milieu",
        "weight_hh",
        "weight_pop",
        "hh_size",
        "hh_size_class",
        "n_children_0_14",
        "n_working_age_15_59",
        "n_elderly_60_plus",
        "n_female",
        "head_sex",
        "head_age",
        "head_marital_status",
        "head_education",
        "head_csp",
        "expenditure_pc",
        "expenditure_total",
        "consumption_pc",
        "consumption_total",
        "expenditure_bracket",
        "quintile",
        "decile",
        "poverty_line",
        "extreme_poverty_line",
        "poor",
        "extreme_poor",
        "food_share",
    ]
    rest = [c for c in df.columns if c.startswith("share_")]
    return df[ordered + rest]
