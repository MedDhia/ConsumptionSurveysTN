"""Reproduce INS's published figures from the microdata.

If any of these fail, the pipeline is weighting or aggregating something wrong and
nothing downstream should be trusted. Published values come from
``EBCNV2021_note_synthese.pdf`` (February 2023) and the survey landing page; each
assertion names its table.

The suite needs the raw archives fetched (``make fetch``). It builds the household and
function files once per session -- the product file is 3.3M rows, so the fixtures are
session-scoped.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from consumptiontn import build_expenditure, build_household, build_panel

# Every test in this module reads a Stata file out of data/raw. Run `make fetch` first,
# or select against it with `pytest -m "not needs_raw"`.
pytestmark = pytest.mark.needs_raw

TOLERANCE_DT = 1.0  # published expenditure figures are rounded to whole dinars
TOLERANCE_PCT = 0.06  # published rates are rounded to one decimal


@pytest.fixture(scope="session")
def household() -> pd.DataFrame:
    return build_household.build()


@pytest.fixture(scope="session")
def by_function() -> pd.DataFrame:
    return build_expenditure.build_by_function()


def wmean(frame: pd.DataFrame, column: str, weight: str = "weight_pop") -> float:
    return float(np.average(frame[column], weights=frame[weight]))


def test_sample_size(household):
    """EBCNV 2021 sampled 21,600 households in design; 17,394 are in the released file."""
    assert len(household) == 17394
    assert household["hh_id"].is_unique


def test_population_total(household):
    """The individual weights sum to Tunisia's resident population, ~11.76 million."""
    assert 11_500_000 < household["weight_pop"].sum() < 12_000_000


def test_individual_weight_is_household_weight_times_size(household):
    """`v701 == v700 * hh_size`. Getting this backwards is the easiest way to go wrong."""
    implied = household["weight_hh"] * household["hh_size"]
    assert (household["weight_pop"] - implied).abs().max() < 0.001


@pytest.mark.parametrize(
    ("milieu", "expected"),
    [(None, 5468), ("urban", 6141), ("rural", 4041)],
    ids=["national", "urban", "rural"],
)
def test_mean_per_capita_expenditure(household, milieu, expected):
    """Note de synthèse, Tableau 1."""
    frame = household if milieu is None else household[household["milieu"] == milieu]
    assert wmean(frame, "expenditure_pc") == pytest.approx(expected, abs=TOLERANCE_DT)


@pytest.mark.parametrize(
    ("milieu", "expected"),
    [(None, 20328), ("urban", 22152), ("rural", 16065)],
    ids=["national", "urban", "rural"],
)
def test_mean_household_expenditure(household, milieu, expected):
    """Note de synthèse, Tableau 1. Household-unit figure, so weighted by `weight_hh`."""
    frame = household if milieu is None else household[household["milieu"] == milieu]
    actual = wmean(frame, "expenditure_total", "weight_hh")
    assert actual == pytest.approx(expected, abs=TOLERANCE_DT)


@pytest.mark.parametrize(
    ("region", "expected"),
    [
        ("Grand Tunis", 6874),
        ("North East", 5057),
        ("North West", 4493),
        ("Centre East", 6130),
        ("Centre West", 3614),
        ("South East", 4675),
        ("South West", 4847),
    ],
)
def test_mean_per_capita_expenditure_by_region(household, region, expected):
    """Note de synthèse, Tableau 2."""
    frame = household[household["region"] == region]
    assert wmean(frame, "expenditure_pc") == pytest.approx(expected, abs=TOLERANCE_DT)


def test_poverty_rate(household):
    """Note de synthèse, Tableau 6: 16.6% poor, 2.9% extremely poor."""
    poor = 100 * wmean(household.assign(x=household["poor"].eq("poor")), "x")
    extreme = 100 * wmean(household.assign(x=household["extreme_poor"].eq("extremely poor")), "x")
    assert poor == pytest.approx(16.6, abs=TOLERANCE_PCT)
    assert extreme == pytest.approx(2.9, abs=TOLERANCE_PCT)


def test_poor_population_counts(household):
    """Landing page: 1,950,000 poor and 337,141 extremely poor persons."""
    poor = float((household["poor"].eq("poor") * household["weight_pop"]).sum())
    is_extreme = household["extreme_poor"].eq("extremely poor")
    extreme = float((is_extreme * household["weight_pop"]).sum())
    assert poor == pytest.approx(1_950_000, rel=0.005)
    assert extreme == pytest.approx(337_141, rel=0.005)


@pytest.mark.parametrize(
    ("region", "expected"),
    [
        ("Grand Tunis", 4.7),
        ("North East", 15.2),
        ("North West", 22.5),
        ("Centre East", 13.2),
        ("Centre West", 37.0),
        ("South East", 23.2),
        ("South West", 18.1),
    ],
)
def test_poverty_rate_by_region(household, region, expected):
    """Note de synthèse, Tableau 7."""
    frame = household[household["region"] == region]
    rate = 100 * wmean(frame.assign(x=frame["poor"].eq("poor")), "x")
    assert rate == pytest.approx(expected, abs=TOLERANCE_PCT)


@pytest.mark.parametrize(
    ("milieu", "expected_poverty", "expected_extreme"),
    [("urban", 2683, 1529), ("rural", 2224, 1347)],
)
def test_poverty_lines(household, milieu, expected_poverty, expected_extreme):
    """Note de synthèse, Tableau 5: one poverty line per milieu, not one national line."""
    frame = household[household["milieu"] == milieu]
    assert frame["poverty_line"].round(0).unique().tolist() == [expected_poverty]
    assert frame["extreme_poverty_line"].round(0).unique().tolist() == [expected_extreme]


def test_national_gini(household):
    """Note de synthèse, Tableau 10: 35.3 in 2021."""
    value = build_panel.gini(household["expenditure_pc"], household["weight_pop"])
    assert value == pytest.approx(35.3, abs=0.1)


PUBLISHED_FUNCTION_DPA = {
    1: 1645, 2: 183, 3: 635, 4: 1307, 5: 191, 6: 609,
    7: 375, 8: 224, 9: 46, 10: 81, 11: 164, 12: 8,
}


@pytest.mark.parametrize(("code", "expected"), sorted(PUBLISHED_FUNCTION_DPA.items()))
def test_expenditure_by_function(household, by_function, code, expected):
    """Note de synthèse, Tableau 4. All twelve functions, no exceptions.

    Function 1 and function 11 only match once the nine 111xx ready-to-eat products INS
    counts as food are reassigned -- see `labels.PRODUCT_FUNCTION_OVERRIDES`.
    """
    merged = household[["hh_id", "hh_size", "weight_pop"]].merge(by_function, on="hh_id")
    suffix = f"_{code:02d}"
    column = next(
        c for c in by_function.columns if c.startswith("exp_") and c.endswith(suffix)
    )
    dpa = float(np.average(merged[column] / merged["hh_size"], weights=merged["weight_pop"]))
    assert dpa == pytest.approx(expected, abs=TOLERANCE_DT)


def test_function_totals_sum_to_household_total(household, by_function):
    """The twelve functions must exhaust household expenditure, not approximate it."""
    merged = household[["hh_id", "expenditure_total"]].merge(
        by_function[["hh_id", "exp_total"]], on="hh_id"
    )
    assert (merged["exp_total"] - merged["expenditure_total"]).abs().max() < 0.1


def test_every_product_has_a_function():
    products = build_expenditure.build_products()
    assert products["consumption_function_code"].between(1, 12).all()
    assert products["consumption_function"].notna().all()
    assert products["product_code"].is_unique
