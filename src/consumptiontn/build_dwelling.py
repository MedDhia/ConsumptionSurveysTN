"""Household dwelling, amenities and durable-goods ownership.

``microdonnees_condvie.dta`` is a household-level file (17,394 rows, one per household
in ``pov_2021.dta``), not an individual one, despite sitting alongside the individual
education and health modules on the INS page.
"""

from __future__ import annotations

import pandas as pd

from . import labels
from .extract import find, read_dta


def build() -> pd.DataFrame:
    df, _ = read_dta(find("ebcnv2021_condvie", "microdonnees_condvie.dta"))
    df = df.rename(columns=labels.RENAMES["microdonnees_condvie"])
    df = df[[c for c in labels.RENAMES["microdonnees_condvie"].values() if c in df.columns]]
    df["hh_id"] = df["hh_id"].astype("int64")
    df["survey_year"] = 2021

    hh, _ = read_dta(find("ebcnv2021_depenses", "pov_2021.dta"))
    hh = hh.rename(columns=labels.RENAMES["pov_2021"])
    df = df.merge(
        hh[["hh_id", "region", "milieu", "weight_hh", "weight_pop", "hh_size", "poor"]],
        on="hh_id",
        how="left",
    )

    df["hh_size"] = pd.to_numeric(df["hh_size"], errors="coerce").astype("Int64")

    df = labels.decode_frame(df)
    lead = ["hh_id", "survey_year", "region", "milieu", "weight_hh", "weight_pop", "hh_size", "poor"]
    return df[lead + [c for c in df.columns if c not in lead]]
