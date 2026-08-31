"""Checks on the between-governorate dispersion datasets.

This module invents no numbers either — it normalises and summarises `tn_governorate_panel`.
What it can get wrong is the *comparison*: a dispersion measure that moves because coverage
moved, a per-head figure that silently reintroduces a denominator limit, a geography that
changes under the reader's feet. Those are the failures that look like findings, so they are
what these tests are about.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from consumptiontn import build_regional_inequality as R


@pytest.fixture(scope="module")
def built():
    panel = pd.read_csv("data/processed/tn_governorate_panel.csv",
                        dtype={"breakdown": "string", "boundary": "string"})
    cpi = pd.read_csv("data/processed/tn_cpi_annual.csv")
    return R.build(panel=panel, cpi=cpi)


# ------------------------------------------------------------------ the coverage trap

def test_an_incomplete_year_gets_no_dispersion_value(built):
    """The failure this module exists to prevent.

    A measure computed over whichever governorates happened to be printed moves when
    coverage moves: Kasserine dropping out of one edition would read as inequality
    falling, and nothing downstream could tell that from the finding.
    """
    _, disp, _ = built
    partial = disp[~disp.complete]
    assert not partial.empty, "no incomplete years at all is suspicious, not reassuring"
    for column in ("theil_weighted", "cv_weighted", "cv_unweighted", "tail_ratio"):
        assert partial[column].isna().all(), column


def test_a_complete_year_means_every_unit_its_geography_expects(built):
    _, disp, _ = built
    complete = disp[disp.complete]
    expected = complete.geography.map(
        {"as_printed": R.GOVERNORATE_COUNT, "constant": R.CONSTANT_COUNT})
    assert (complete.governorates == expected).all()


def test_the_excluded_years_stay_visible(built):
    """Dropping them outright would make the coverage limit invisible to a reader."""
    _, disp, _ = built
    assert {"complete", "governorates"} <= set(disp.columns)
    assert disp.governorates.min() < R.CONSTANT_COUNT


# ------------------------------------------------------------------------- the bases

def test_the_shares_sum_to_one(built):
    comparable, _, _ = built
    share = comparable[comparable.basis.eq("share_of_national")]
    totals = share.groupby(["indicator", "geography", "year"]).comparable.sum()
    assert np.allclose(totals, 1.0)


def test_the_denominator_is_not_also_an_outcome(built):
    """Population per head is 1, which is not a finding about anything."""
    comparable, disp, _ = built
    assert R.DENOMINATOR not in set(comparable.indicator)
    assert R.DENOMINATOR not in set(disp.indicator)


def test_per_head_is_the_count_over_population(built):
    comparable, _, _ = built
    per_head = comparable[comparable.basis.eq("per_head")]
    assert np.allclose(per_head.comparable,
                       per_head.value / per_head.population_thousands)
    assert per_head.year.min() == 2005, "the corpus has no earlier denominator"


def test_the_share_basis_reaches_further_back_than_per_head(built):
    """The whole reason for carrying two bases."""
    comparable, _, _ = built
    share = comparable[comparable.basis.eq("share_of_national")]
    assert share.year.min() < comparable[comparable.basis.eq("per_head")].year.min()


# -------------------------------------------------------------------- the geographies

def test_the_constant_geography_has_no_manouba_and_a_bigger_ariana(built):
    comparable, _, _ = built
    constant = comparable[comparable.geography.eq("constant")]
    assert R.SPLIT_CHILD not in set(constant.governorate)
    assert constant.governorate.nunique() == R.CONSTANT_COUNT

    printed = comparable[comparable.geography.eq("as_printed")
                         & comparable.basis.eq("share_of_national")]
    pair = printed[printed.governorate.isin([R.SPLIT_PARENT, R.SPLIT_CHILD])]
    summed = pair.groupby(["indicator", "year"]).value.sum()
    merged = constant[constant.basis.eq("share_of_national")
                      & constant.governorate.eq(R.SPLIT_PARENT)]
    merged = merged.set_index(["indicator", "year"]).value
    shared = summed.index.intersection(merged.index)
    assert len(shared) > 100
    assert np.allclose(summed.loc[shared], merged.loc[shared])


def test_the_constant_geography_spans_the_whole_corpus(built):
    """This is what buys the pre-revolution window: 24 units cannot reach before 2000."""
    _, disp, _ = built
    share = disp[disp.complete & disp.basis.eq("share_of_national")]
    printed = share[share.geography.eq("as_printed")]
    constant = share[share.geography.eq("constant")]
    assert printed.year.min() == 2000, "Manouba does not exist earlier"
    assert constant.year.min() < 2000
    pre = lambda f: f[f.year.lt(R.REVOLUTION)].year.nunique()  # noqa: E731
    assert pre(constant) >= 16 and pre(constant) > pre(printed)


def test_merging_does_not_invent_a_population():
    """Summing a present population onto a missing one would read as the parent's alone.

    Exercised on a constructed frame rather than the corpus, where the two governorates'
    populations are always missing or present together, so the guard would never fire.
    """
    frame = pd.DataFrame({
        "governorate": [R.SPLIT_PARENT, R.SPLIT_CHILD, R.SPLIT_PARENT, R.SPLIT_CHILD],
        "year": [2005, 2005, 2006, 2006],
        "indicator": ["primary_schools"] * 4,
        "unit": ["schools"] * 4,
        "value": [10.0, 4.0, 11.0, 5.0],
        # 2006 has the child's population missing: the pair's is then unknown, not 600.
        "population_thousands": [600.0, 400.0, 620.0, None],
    })
    merged = R.constant_geography(frame).set_index("year")
    assert merged.loc[2005, "value"] == 14.0
    assert merged.loc[2005, "population_thousands"] == 1_000.0
    assert merged.loc[2006, "value"] == 16.0
    assert pd.isna(merged.loc[2006, "population_thousands"])


# ------------------------------------------------------------------------ the measures

def test_population_weighting_costs_the_long_pre_period(built):
    """A constraint worth asserting so it cannot be forgotten.

    The weighted measures are the defensible ones — unweighted dispersion treats Tozeur
    and Tunis as one observation each — but they need a population, so they inherit the
    2005 limit even on the basis that would otherwise reach 1994. Testing pre-trends over
    a long window therefore means accepting the unit-level question.
    """
    _, disp, _ = built
    weighted = disp[disp.theil_weighted.notna() | disp.cv_weighted.notna()]
    unweighted = disp[disp.cv_unweighted.notna()]
    assert weighted.year.min() == 2005
    assert unweighted.year.min() < 2000


def test_theil_is_absent_rather_than_floored_where_something_is_zero(built):
    comparable, disp, _ = built
    zeroed = comparable[comparable.basis.eq("per_head")
                        & comparable.geography.eq("as_printed")]
    has_zero = (zeroed.groupby(["indicator", "year"]).comparable.min() <= 0)
    hit = has_zero[has_zero].index
    assert len(hit) > 0, "no zeros anywhere would make this test vacuous"
    rows = disp[disp.basis.eq("per_head") & disp.geography.eq("as_printed")
                & disp.complete].set_index(["indicator", "year"])
    shared = rows.index.intersection(hit)
    assert rows.loc[shared, "theil_weighted"].isna().all()
    # The unweighted CV has no logarithm in it and survives.
    assert rows.loc[shared, "cv_unweighted"].notna().any()


def test_the_measures_agree_with_their_definitions():
    y = np.array([1.0, 2.0, 3.0, 4.0])
    w = np.array([1.0, 1.0, 1.0, 1.0])
    assert R._weighted_cv(y, w) == pytest.approx(y.std(ddof=0) / y.mean())
    # Equal everywhere is zero inequality, whatever the measure.
    flat = np.array([5.0, 5.0, 5.0])
    assert R._weighted_theil(flat, np.ones(3)) == pytest.approx(0.0)
    assert R._weighted_cv(flat, np.ones(3)) == pytest.approx(0.0)
    assert R._tail_ratio(np.array([1.0, 1.0, 1.0, 2.0, 2.0, 2.0]), k=3) == pytest.approx(2.0)
    # A zero makes the log measure undefined, not enormous.
    assert np.isnan(R._weighted_theil(np.array([0.0, 1.0, 2.0]), np.ones(3)))


def test_dispersion_ignores_the_unit_a_series_is_measured_in(built):
    """Scaling every governorate by the same factor is not a change in inequality.

    This is what makes the share basis and the per-head basis comparable as *measures*
    even though their levels are not.
    """
    y = np.array([2.0, 5.0, 9.0, 14.0])
    w = np.array([100.0, 200.0, 50.0, 400.0])
    for factor in (0.001, 1_000.0):
        assert R._weighted_cv(y * factor, w) == pytest.approx(R._weighted_cv(y, w))
        assert R._weighted_theil(y * factor, w) == pytest.approx(R._weighted_theil(y, w))
        assert R._tail_ratio(y * factor) == pytest.approx(R._tail_ratio(y))


# ----------------------------------------------------------------------- the deflation

def test_the_money_series_is_carried_to_constant_dinars(built):
    """It is the one series denominated in money. Comparing 2003 with 2023 in nominal
    dinars measures the currency, not the remittances."""
    comparable, _, _ = built
    money = comparable[comparable.indicator.isin(R.NOMINAL)]
    assert not money.empty
    assert (money.unit == f"dinars, constant {R.DEFLATOR_BASE}").all()


def test_the_deflator_leaves_its_own_base_year_alone(built):
    panel = pd.read_csv("data/processed/tn_governorate_panel.csv",
                        dtype={"breakdown": "string", "boundary": "string"})
    cpi = pd.read_csv("data/processed/tn_cpi_annual.csv")
    plain = panel[panel.breakdown.fillna("").eq("")]
    real = R.real_values(plain, cpi)
    for frame in (plain, real):
        base = frame[frame.indicator.isin(R.NOMINAL) & frame.year.eq(R.DEFLATOR_BASE)]
        assert not base.empty
    before = plain[plain.indicator.isin(R.NOMINAL) & plain.year.eq(R.DEFLATOR_BASE)]
    after = real[real.indicator.isin(R.NOMINAL) & real.year.eq(R.DEFLATOR_BASE)]
    assert np.allclose(sorted(before.value), sorted(after.value))
    # And an earlier year is revised upward, since prices were lower then.
    early = plain[plain.indicator.isin(R.NOMINAL) & plain.year.eq(2005)].value.sum()
    early_real = real[real.indicator.isin(R.NOMINAL) & real.year.eq(2005)].value.sum()
    assert early_real > early


# ------------------------------------------------------------------------ the exposure

def test_the_baseline_window_is_entirely_pre_revolution(built):
    """An exposure variable contaminated by post-treatment years identifies nothing."""
    assert R.BASELINE_YEARS[1] < R.REVOLUTION


def test_every_governorate_has_a_region_and_a_rank(built):
    _, _, baseline = built
    assert baseline.region.notna().all()
    assert baseline.region.nunique() == 7
    assert baseline.governorate.nunique() == R.GOVERNORATE_COUNT
    # Ranks run 1..24 within each indicator, with no gaps beyond ties.
    for _, block in baseline.groupby("indicator"):
        assert block.baseline_rank.min() == 1
        assert block.baseline_rank.max() <= len(block)


def test_the_coastal_coding_is_the_documented_one(built):
    """A contestable coding decision, so it is pinned rather than left to drift."""
    _, _, baseline = built
    coastal = set(baseline[baseline.littoral].governorate)
    assert coastal == set(R.LITTORAL)
    assert len(R.LITTORAL) == 12
    assert "Kasserine" not in R.LITTORAL and "Sidi Bouzid" not in R.LITTORAL
    assert R.SPLIT_CHILD in R.LITTORAL, "Manouba is counted with Grand Tunis"


def test_the_baseline_separates_the_governorates_it_is_meant_to(built):
    """If the baseline were noise, an interior/coastal design would have nothing to bite on.

    Averaged over indicators, coastal governorates rank better than interior ones. This is
    a statement about the data being informative, not yet a finding about the revolution.
    """
    _, _, baseline = built
    mean_rank = baseline.groupby("littoral").baseline_rank.mean()
    assert mean_rank[True] < mean_rank[False]
