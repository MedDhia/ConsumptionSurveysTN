"""Checks on the conventional inequality indices.

An index is a formula, so it can be verified against values known in closed form rather
than against itself — which is what most of these do. The Gini of {1, 3} is 0.25 whatever
implementation computes it, and a distribution where one unit holds everything has Gini
(n-1)/n exactly. Those are the tests that would catch a transposed weight or an off-by-one
in a cumulative sum, the two ways this kind of code usually goes wrong quietly.

The rest guard the properties that make an index comparable at all: scale invariance, so a
series measured in dinars and one in counts can be read on the same axis; and zero
inequality for a flat distribution, so a trend cannot be an artefact of the formula.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from consumptiontn import build_inequality_indices as I


@pytest.fixture(scope="module")
def built():
    comparable = pd.read_csv("data/processed/tn_governorate_comparable.csv")
    return I.build(comparable)


# ------------------------------------------------------- verified against closed forms

def test_the_gini_of_a_two_point_distribution():
    """Half at 1 and half at 3 is 0.25. Arithmetic, not a regression test."""
    assert I.gini(np.array([1.0, 3.0])) == pytest.approx(0.25)


def test_one_unit_holding_everything():
    """With n units and all of it in one, Gini is exactly (n-1)/n."""
    for n in (5, 10, 24):
        y = np.array([0.0] * (n - 1) + [1.0])
        assert I.gini(y) == pytest.approx((n - 1) / n)


def test_a_flat_distribution_is_zero_on_every_index():
    y = np.full(6, 5.0)
    assert I.gini(y) == pytest.approx(0.0, abs=1e-12)
    assert I.theil_t(y) == pytest.approx(0.0, abs=1e-12)
    assert I.theil_l(y) == pytest.approx(0.0, abs=1e-12)
    assert I.coefficient_of_variation(y) == pytest.approx(0.0, abs=1e-12)
    for epsilon in I.ATKINSON_EPSILONS:
        assert I.atkinson(y, epsilon) == pytest.approx(0.0, abs=1e-12)


def test_atkinson_at_epsilon_one_is_the_log_case():
    """A(1) = 1 - geometric mean / arithmetic mean, which is checkable by hand."""
    y = np.array([1.0, 2.0, 4.0, 8.0])
    expected = 1.0 - float(np.exp(np.mean(np.log(y)))) / float(y.mean())
    assert I.atkinson(y, 1.0) == pytest.approx(expected)


def test_atkinson_rises_with_aversion():
    """More weight on the worst-off cannot make an unequal distribution look better."""
    y = np.array([1.0, 3.0, 9.0, 27.0])
    values = [I.atkinson(y, e) for e in (0.5, 1.0, 2.0)]
    assert values == sorted(values)
    assert all(0.0 < v < 1.0 for v in values)


def test_the_weights_actually_weight():
    """Moving population onto the poorest unit must change the answer.

    A Gini that ignored its weights would pass every other test in this file.
    """
    y = np.array([1.0, 10.0])
    to_the_poor = I.gini(y, np.array([9.0, 1.0]))
    to_the_rich = I.gini(y, np.array([1.0, 9.0]))
    even = I.gini(y, np.array([1.0, 1.0]))
    assert to_the_poor != pytest.approx(even)
    assert to_the_rich != pytest.approx(even)
    # Concentrating people where the value is low leaves most of them far below the mean.
    assert to_the_poor > to_the_rich


# ------------------------------------------------------------- properties an index needs

def test_every_index_ignores_the_unit_of_measurement():
    """Scale invariance. Without it, deflating a series would change its inequality."""
    y = np.array([2.0, 5.0, 9.0, 14.0])
    w = np.array([100.0, 200.0, 50.0, 400.0])
    for factor in (1e-3, 1e3):
        assert I.gini(y * factor, w) == pytest.approx(I.gini(y, w))
        assert I.theil_t(y * factor, w) == pytest.approx(I.theil_t(y, w))
        assert I.theil_l(y * factor, w) == pytest.approx(I.theil_l(y, w))
        assert I.coefficient_of_variation(y * factor, w) == pytest.approx(
            I.coefficient_of_variation(y, w))
        for epsilon in I.ATKINSON_EPSILONS:
            assert I.atkinson(y * factor, epsilon, w) == pytest.approx(
                I.atkinson(y, epsilon, w))
        assert I.percentile_ratio(y * factor, 90, 10, w) == pytest.approx(
            I.percentile_ratio(y, 90, 10, w))


def test_the_log_measures_decline_to_say_anything_about_a_zero():
    """A governorate with none of something is a real observation, not a small number.

    Flooring it, or adding an epsilon, would produce a number that moves with the floor.
    """
    y = np.array([0.0, 1.0, 2.0])
    assert np.isnan(I.theil_t(y))
    assert np.isnan(I.theil_l(y))
    assert np.isnan(I.atkinson(y, 1.0))
    # These survive it, and are what to read on such a series.
    assert np.isfinite(I.gini(y))
    assert np.isfinite(I.coefficient_of_variation(y))


def test_a_percentile_is_a_value_something_actually_had():
    """No interpolation between governorates, which would invent an unobserved figure."""
    y = np.array([1.0, 2.0, 3.0, 4.0])
    for q in (10, 25, 50, 75, 90):
        assert I.weighted_percentile(y, q) in set(y.tolist())


# ------------------------------------------------------------------- the built dataset

def test_the_indices_stay_in_their_bounds(built):
    assert built.gini.dropna().between(0, 1).all()
    for column in ("atkinson_05", "atkinson_1", "atkinson_2"):
        assert built[column].dropna().between(0, 1).all()
    assert (built.theil_t.dropna() >= -1e-9).all()
    assert (built.theil_l.dropna() >= -1e-9).all()
    assert (built.p90_p10.dropna() >= 1).all()


def test_both_weightings_are_present_and_differ(built):
    assert set(built.weighting) == {"population", "unweighted"}
    key = ["indicator", "basis", "geography", "year"]
    wide = built.pivot_table(index=key, columns="weighting", values="gini").dropna()
    assert len(wide) > 500
    # If the weights were being ignored the two columns would be identical.
    assert not np.allclose(wide.population, wide.unweighted)


def test_population_weighting_costs_the_long_pre_period(built):
    """The same constraint the dispersion dataset carries, asserted here too."""
    assert built[built.weighting.eq("population")].year.min() == 2005
    assert built[built.weighting.eq("unweighted")].year.min() < 2000


def test_the_long_window_reaches_seventeen_pre_revolution_years(built):
    """What the share basis on the constant geography buys, and why both exist."""
    long = built[built.weighting.eq("unweighted") & built.basis.eq("share_of_national")
                 & built.geography.eq("constant")]
    pre = long[long.year.lt(I.REVOLUTION)].year.nunique()
    assert pre >= 17


def test_only_complete_years_are_measured(built):
    """An index over whichever governorates were printed moves with coverage."""
    assert set(built.governorates) <= {23, 24}
    for geography, expected in (("as_printed", 24), ("constant", 23)):
        block = built[built.geography.eq(geography)]
        assert (block.governorates == expected).all()


def test_the_trend_table_finds_the_series_that_moved(built):
    long = built[built.weighting.eq("unweighted") & built.basis.eq("share_of_national")
                 & built.geography.eq("constant")]
    table = I.trends(long, "gini", min_pre=10, min_post=8)
    assert not table.empty
    assert {"pre_slope_decade", "post_slope_decade", "slope_break_decade"} <= set(table.columns)
    # Sorted ascending, so the largest positive break is last.
    assert table.slope_break_decade.is_monotonic_increasing
    assert table.iloc[-1].indicator == "job_offers"


def test_the_job_offers_break_is_mostly_the_pandemic(built):
    """The correction this dataset forced, pinned so it cannot quietly come back.

    Fitting a post-2011 slope through 2020-23 reports a break several times the one
    measured without those years. The pandemic years are real data and stay in the
    dataset; what is wrong is reading a linear post-2011 trend through them and calling
    the result a revolution effect.
    """
    long = built[built.weighting.eq("unweighted") & built.basis.eq("share_of_national")
                 & built.geography.eq("constant") & built.indicator.eq("job_offers")]
    series = long.set_index("year").gini.dropna()

    def break_through(last_year: int) -> float:
        s = series[series.index <= last_year]
        pre, post = s[s.index < I.REVOLUTION], s[s.index >= I.REVOLUTION]
        return (float(np.polyfit(post.index, post.to_numpy(), 1)[0])
                - float(np.polyfit(pre.index, pre.to_numpy(), 1)[0]))

    with_covid = break_through(2023)
    without = break_through(2019)
    assert with_covid > 3 * without, (with_covid, without)


def test_2011_is_not_the_largest_annual_move(built):
    """The claim figure 40 makes. If 2011 topped this ranking, that figure would be wrong."""
    long = built[built.weighting.eq("unweighted") & built.basis.eq("share_of_national")
                 & built.geography.eq("constant")]
    wide = long.pivot_table(index="year", columns="indicator", values="gini")
    change = wide.diff()
    breadth = ((change > 0).sum(axis=1) / change.notna().sum(axis=1)).dropna()
    assert breadth.rank(ascending=False).loc[I.REVOLUTION] > 3
    # It is a real positive move, though, and the figure says so rather than dismissing it.
    assert change.mean(axis=1).loc[I.REVOLUTION] > 0
