"""Individual-level file: roster demographics + education + health.

The three modules do not cover the same people. The roster and the education module
each hold 65,524 individuals; the health module holds 54,041, because its questions
were not put to the youngest children. The merge is a left join on the roster, so
health columns are missing for anyone outside the health module's scope -- that is a
coverage fact about the survey, not an extraction failure.
"""

from __future__ import annotations

import pandas as pd

from . import labels
from .extract import find, read_dta

KEYS = ["hh_id", "person_id"]


def _module(key: str, member: str, rename_key: str) -> pd.DataFrame:
    df, _ = read_dta(find(key, member))
    df = df.rename(columns=labels.RENAMES[rename_key])
    keep = [c for c in labels.RENAMES[rename_key].values() if c in df.columns]
    df = df[keep].copy()
    for key_col in KEYS:
        if key_col in df.columns:
            df[key_col] = df[key_col].astype("int64")
    return df


def build() -> pd.DataFrame:
    roster = _module("ebcnv2021_depenses", "donnindiv2021.dta", "donnindiv2021")
    education = _module("ebcnv2021_educsante", "Education2021.dta", "Education2021")
    health = _module("ebcnv2021_educsante", "Sante2021.dta", "Sante2021")

    # ``age`` and ``sex`` arrive from both the roster and the education module; keep the
    # roster's grouped age plus the education module's exact age, and drop the duplicate
    # sex column rather than letting the merge suffix it.
    education = education.drop(columns=[c for c in ["sex"] if c in education.columns])
    health = health.drop(columns=[c for c in ["age"] if c in health.columns])

    df = roster.merge(education, on=KEYS, how="left").merge(health, on=KEYS, how="left")
    df["survey_year"] = 2021

    # Carry household weights and geography so the file stands on its own.
    hh, _ = read_dta(find("ebcnv2021_depenses", "pov_2021.dta"))
    hh = hh.rename(columns=labels.RENAMES["pov_2021"])
    df = df.merge(
        hh[
            [
                "hh_id",
                "region",
                "milieu",
                "weight_hh",
                "weight_pop",
                "hh_size",
                "poor",
                "extreme_poor",
            ]
        ],
        on="hh_id",
        how="left",
    )
    # The individual weight for a person is the household weight; ``weight_pop`` is the
    # household's contribution to the population total, so per-person statistics on this
    # file use ``weight_hh``.
    df = df.rename(columns={"weight_hh": "weight"})
    df = df.drop(columns=["weight_pop"])

    for numeric in ["age", "hh_size"]:
        if numeric in df.columns:
            df[numeric] = pd.to_numeric(df[numeric], errors="coerce").astype("Int64")

    df = labels.decode_frame(df)
    lead = [
        "hh_id",
        "person_id",
        "survey_year",
        "region",
        "milieu",
        "weight",
        "hh_size",
        "poor",
        "extreme_poor",
    ]
    return df[lead + [c for c in df.columns if c not in lead]]
