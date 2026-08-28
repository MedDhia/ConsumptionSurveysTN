"""The long indicator panel, 1985-2021.

Two kinds of row live here and the ``basis`` column tells them apart:

``recomputed``  calculated from the 2021 microdata by this pipeline
``published``   transcribed from an INS document (see ``panel_sources``)

The 2021 rows exist in both forms on purpose. The recomputed ones are what the test
suite checks against the published ones; keeping both in the panel lets a reader see
that the reproduction holds rather than take it on trust.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import labels, panel_sources
from .build_expenditure import build_by_function
from .build_household import build as build_household

COLUMNS = [
    "wave",
    "geography_level",
    "geography",
    "milieu",
    "subgroup_type",
    "subgroup",
    "indicator",
    "value",
    "unit",
    "basis",
    "methodology",
    "source_key",
    "source_table",
]


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    return float(np.average(values, weights=weights))


def gini(values: pd.Series, weights: pd.Series) -> float:
    """Weighted Gini coefficient, expressed on INS's 0-100 scale.

    Uses the covariance form on the weighted-rank cumulative population, which is the
    standard estimator for grouped survey data with frequency weights.
    """
    order = np.argsort(values.to_numpy())
    x = values.to_numpy()[order]
    w = weights.to_numpy()[order]
    cum_w = np.cumsum(w)
    total_w = cum_w[-1]
    # Midpoint of each unit's share of the weighted population.
    rank = (cum_w - 0.5 * w) / total_w
    mean = np.average(x, weights=w)
    return float(100 * 2 * np.average((x - mean) * (rank - 0.5), weights=w) / mean)


def _row(**kwargs) -> dict:
    row = dict.fromkeys(COLUMNS)
    row.update(
        basis="recomputed",
        methodology="revised (2011)",
        source_key="ebcnv2021_depenses",
        source_table="pov_2021.dta",
    )
    row.update(kwargs)
    return row


def recomputed_rows(
    household: pd.DataFrame | None = None,
    by_function: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """2021 indicators recalculated from the microdata.

    All per-person statistics use ``weight_pop``, the individual extrapolation factor.
    """
    hh = build_household() if household is None else household
    rows: list[dict] = []

    def emit(frame: pd.DataFrame, **where) -> None:
        w = frame["weight_pop"]
        poor = frame["poor"].eq("poor")
        extreme = frame["extreme_poor"].eq("extremely poor")
        measures = [
            ("expenditure_pc_mean", "DT per year", weighted_mean(frame["expenditure_pc"], w)),
            ("consumption_pc_mean", "DT per year", weighted_mean(frame["consumption_pc"], w)),
            # The household-unit figure takes the household weight, not the individual one.
            (
                "expenditure_hh_mean",
                "DT per year",
                weighted_mean(frame["expenditure_total"], frame["weight_hh"]),
            ),
            ("poverty_rate", "percent", 100 * weighted_mean(poor, w)),
            ("extreme_poverty_rate", "percent", 100 * weighted_mean(extreme, w)),
            ("gini", "index (0-100)", gini(frame["expenditure_pc"], w)),
            ("population_share", "percent", 100 * w.sum() / hh["weight_pop"].sum()),
            ("poor_population", "persons", float((poor * w).sum())),
        ]
        for indicator, unit, value in measures:
            rows.append(_row(wave=2021, indicator=indicator, unit=unit, value=value, **where))

    emit(hh, geography_level="national", geography="Tunisia")
    for milieu, frame in hh.groupby("milieu", observed=True):
        emit(frame, geography_level="national", geography="Tunisia", milieu=str(milieu))
    for region, frame in hh.groupby("region", observed=True):
        emit(frame, geography_level="region", geography=str(region))
        for milieu, sub in frame.groupby("milieu", observed=True):
            emit(sub, geography_level="region", geography=str(region), milieu=str(milieu))
    subgroups = [
        ("head education", "head_education"),
        ("head socio-professional category", "head_csp"),
    ]
    for name, column in subgroups:
        for value, frame in hh.groupby(column, observed=True):
            emit(
                frame,
                geography_level="national",
                geography="Tunisia",
                subgroup_type=name,
                subgroup=str(value),
            )

    # Expenditure structure by COICOP function, from the product file.
    fn = build_by_function() if by_function is None else by_function
    merged = hh[["hh_id", "hh_size", "weight_pop"]].merge(fn, on="hh_id")
    total = 0.0
    per_function = {}
    for code in sorted(labels.CONSUMPTION_FUNCTIONS):
        column = next(c for c in fn.columns if c.startswith("exp_") and c.endswith(f"_{code:02d}"))
        dpa = weighted_mean(merged[column] / merged["hh_size"], merged["weight_pop"])
        per_function[code] = dpa
        total += dpa
    for code, dpa in per_function.items():
        common = dict(
            wave=2021,
            geography_level="national",
            geography="Tunisia",
            subgroup_type="COICOP function",
            subgroup=str(code),
            source_key="ebcnv2021_depenses",
            source_table="produit2021_plus.dta",
        )
        rows.append(
            _row(indicator="expenditure_pc_by_function", unit="DT per year", value=dpa, **common)
        )
        rows.append(
            _row(indicator="budget_share", unit="percent", value=100 * dpa / total, **common)
        )

    return pd.DataFrame.from_records(rows)[COLUMNS]


def build(
    household: pd.DataFrame | None = None,
    by_function: pd.DataFrame | None = None,
) -> pd.DataFrame:
    published = panel_sources.published_rows()
    panel = pd.concat([recomputed_rows(household, by_function), published], ignore_index=True)
    panel["milieu"] = panel["milieu"].fillna("all")
    panel["geography"] = panel["geography"].fillna("Tunisia")
    panel["geography_level"] = panel["geography_level"].fillna("national")
    return panel.sort_values(
        [
            "indicator",
            "wave",
            "geography_level",
            "geography",
            "milieu",
            "subgroup_type",
            "subgroup",
            "basis",
        ],
        na_position="first",
    ).reset_index(drop=True)[COLUMNS]
