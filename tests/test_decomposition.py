"""Checks on the two-geography Ginis and the Theil between/within split.

The decomposition is the one piece of arithmetic here that has an exact answer to be
checked against: Theil-T is additively decomposable, so the between-region and
within-region parts must sum to the total for every indicator and year, not on average and
not to three decimals. That identity is the test the whole module rests on, and it is
worth stating that it catches real mistakes -- a group weight taken as a count rather than
a share, or a relative mean taken against the group mean instead of the grand mean, both
leave every other property of the output intact and break only this.

The rest verify the properties that make the two geographies comparable at all. Aggregating
governorates into regions cannot raise the Gini, because it removes variation and adds
none; a distribution split evenly across regions has no between-region component; and one
where every governorate inside a region is identical has no within-region component. Each
has a closed form, so none of these is a regression test against a previous run.

The pre/post table is checked for the thing it is most likely to get wrong, which is not
the arithmetic but the window: a "pre-revolution mean" over a single printed year would
sail through every numeric check and be meaningless.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from consumptiontn import build_decomposition as D

REGIONS = {"A": ("g1", "g2", "g3"), "B": ("g4", "g5", "g6")}


def _block(values: dict[str, float]) -> pd.DataFrame:
    lookup = {gov: region for region, govs in REGIONS.items() for gov in govs}
    return pd.DataFrame({"governorate": list(values),
                         "region": [lookup[g] for g in values],
                         "comparable": list(values.values())})


@pytest.fixture(scope="module")
def built():
    comparable = pd.read_csv("data/processed/tn_governorate_comparable.csv")
    return D.build(comparable)


# ------------------------------------------------------- verified against closed forms

def test_theil_of_a_flat_distribution_is_zero():
    assert D._theil(np.array([4.0] * 6)) == pytest.approx(0.0, abs=1e-15)


def test_theil_is_scale_invariant():
    """An index measured in dinars and one in counts have to read on the same axis."""
    y = np.array([1.0, 2.0, 5.0, 11.0])
    assert D._theil(y * 1000) == pytest.approx(D._theil(y))


def test_gini_of_two_points():
    assert D._gini(np.array([1.0, 3.0])) == pytest.approx(0.25)


def test_theil_is_undefined_where_a_unit_reports_none():
    """A logarithm has nothing to say about a zero, so the cell is empty, not floored."""
    assert np.isnan(D._theil(np.array([0.0, 1.0, 2.0])))


# --------------------------------------------------------------- the decomposition itself

def test_the_identity_holds_on_a_hand_built_block(monkeypatch):
    monkeypatch.setattr(D, "GOVERNORATE_COUNT", 6)
    values = {"g1": 1.0, "g2": 2.0, "g3": 3.0, "g4": 10.0, "g5": 20.0, "g6": 30.0}
    parts = D.decompose(_block(values))
    total = D._theil(np.array(list(values.values())))
    assert parts["theil_between"] + parts["theil_within"] == pytest.approx(total, abs=1e-15)
    assert parts["identity_gap"] < 1e-15


def test_equal_region_means_leave_nothing_between_them(monkeypatch):
    """Both regions average 4, so all the inequality is inside them."""
    monkeypatch.setattr(D, "GOVERNORATE_COUNT", 6)
    values = {"g1": 1.0, "g2": 4.0, "g3": 7.0, "g4": 2.0, "g5": 4.0, "g6": 6.0}
    parts = D.decompose(_block(values))
    total = D._theil(np.array(list(values.values())))
    assert parts["theil_between"] == pytest.approx(0.0, abs=1e-15)
    assert parts["theil_within"] == pytest.approx(total)


def test_flat_regions_leave_nothing_within_them(monkeypatch):
    """Every governorate in a region identical, so all of it is between regions."""
    monkeypatch.setattr(D, "GOVERNORATE_COUNT", 6)
    values = {"g1": 2.0, "g2": 2.0, "g3": 2.0, "g4": 8.0, "g5": 8.0, "g6": 8.0}
    parts = D.decompose(_block(values))
    total = D._theil(np.array(list(values.values())))
    assert parts["theil_within"] == pytest.approx(0.0, abs=1e-15)
    assert parts["theil_between"] == pytest.approx(total)


def test_the_identity_holds_across_the_whole_corpus(built):
    """The check the module refuses to build without, asserted here as well as there."""
    assert built.identity_gap.notna().any()
    assert built.identity_gap.max() < 1e-9


def test_aggregating_to_regions_nearly_always_lowers_the_gini(built):
    """Nearly always, and the exceptions are the point of the test.

    Aggregating hides the dispersion inside each region, so the region figure is usually
    the smaller. It is not guaranteed to be: the regions hold three or four governorates
    rather than the same number, each counts once here, and a region's total therefore
    carries its size as well as its provision. That makes the aggregation a
    mean-preserving contraction only for equal groups. A handful of cases go the other
    way and the module's own docstring says so; this pins the handful at a handful, so a
    future change to the region map cannot quietly turn it into a pattern.
    """
    pair = built.dropna(subset=["gini_governorate", "gini_region"])
    assert len(pair) > 400
    higher = pair.gini_region > pair.gini_governorate + 1e-9
    assert higher.sum() <= 0.02 * len(pair)
    assert (pair.gini_region / pair.gini_governorate).median() < 0.85


def test_the_between_share_is_a_share(built):
    share = built.between_share.dropna()
    assert len(share) > 400
    assert ((share >= 0) & (share <= 1)).all()


def test_only_complete_years_are_measured(built, ):
    """A Gini over whichever governorates were printed moves when coverage moves."""
    comparable = pd.read_csv("data/processed/tn_governorate_comparable.csv")
    frame = comparable[comparable.basis.eq("share_of_national")
                       & comparable.geography.eq("as_printed")]
    counts = frame.groupby(["indicator", "year"]).size()
    for _, row in built.iterrows():
        assert counts[(row.indicator, row.year)] == D.GOVERNORATE_COUNT


def test_the_period_split_is_at_the_revolution(built):
    assert set(built.period) == {"pre", "post"}
    assert built[built.period.eq("pre")].year.max() < D.REVOLUTION
    assert built[built.period.eq("post")].year.min() >= D.REVOLUTION


# ------------------------------------------------------------------- the pre/post table

def test_short_windows_are_refused(built):
    """`bank_branches` has one pre-revolution year here; a mean over it is not a mean."""
    table = D.pre_post(built, "gini_governorate")
    assert "bank_branches" not in set(table.indicator)
    assert (table.n_pre >= D.MIN_PRE).all()
    assert (table.n_post >= D.MIN_POST).all()


def test_change_is_the_difference_between_the_two_means(built):
    table = D.pre_post(built, "gini_governorate")
    assert np.allclose(table.change, table.post - table.pre, atol=1e-6)


def test_excess_is_what_the_pre_trend_does_not_predict(built):
    table = D.pre_post(built, "between_share")
    assert np.allclose(table.excess, table.change - table.predicted, atol=1e-6)


def test_a_pure_pre_trend_leaves_no_excess():
    """A series that is exactly linear through the cutoff has nothing left over."""
    years = np.arange(2000, 2024)
    frame = pd.DataFrame({
        "indicator": "straight",
        "year": years,
        "period": np.where(years < D.REVOLUTION, "pre", "post"),
        "gini_governorate": 0.2 + 0.01 * (years - 2000),
    })
    table = D.pre_post(frame, "gini_governorate")
    assert table.excess.iat[0] == pytest.approx(0.0, abs=1e-6)
    assert table.pre_trend_per_decade.iat[0] == pytest.approx(0.1, abs=1e-6)


def test_summary_carries_every_measure(built):
    table = D.summary(built)
    assert set(table.measure) == set(D.MEASURES)


# ------------------------------------------------------------------------ reproducibility

def test_no_column_carries_unrounded_float_noise(built):
    """`np.log` is not correctly rounded by IEEE 754, so the last bits are not portable.

    Same rule as the other index modules: every float that passes through a logarithm is
    rounded before it is written, or a rebuild on another machine produces a different
    file and the pipeline's byte-for-byte check fails for no real reason.
    """
    for column in built.select_dtypes("float"):
        values = built[column].dropna()
        assert (values.round(D.DECIMALS) == values).all(), column


def test_the_total_is_not_shipped_twice(built):
    """`theil_governorate` is the decomposed total; a second copy would invite a bogus check."""
    assert "theil_total" not in built.columns
    decomposed = built.dropna(subset=["theil_between"])
    assert np.allclose(decomposed.theil_between + decomposed.theil_within,
                       decomposed.theil_governorate, atol=1e-6)


# ------------------------------------------------------ the fit has to be machine-portable

def test_the_line_fit_matches_the_closed_form():
    """`fit_line` is the textbook least-squares line, verified against a known answer."""
    x = np.array([0.0, 1.0, 2.0, 3.0])
    y = np.array([1.0, 3.0, 5.0, 7.0])
    slope, intercept = D.fit_line(x, y)
    assert slope == pytest.approx(2.0)
    assert intercept == pytest.approx(1.0)


def test_a_vertical_fit_does_not_divide_by_zero():
    slope, intercept = D.fit_line(np.array([5.0, 5.0, 5.0]), np.array([1.0, 2.0, 3.0]))
    assert slope == 0.0
    assert intercept == pytest.approx(2.0)


def test_the_fit_agrees_with_polyfit_to_within_float_noise():
    """Same answer as `np.polyfit`, which is the point: only the last bits differ.

    `fit_line` exists to be *portable*, not to be different. If it ever disagreed with
    numpy's fit by more than accumulated rounding, it would be wrong rather than careful.
    """
    rng = np.random.default_rng(0)
    for _ in range(20):
        x = np.sort(rng.uniform(2000, 2023, size=12))
        y = rng.uniform(0, 1, size=12)
        assert np.allclose(D.fit_line(x, y), np.polyfit(x, y, 1), atol=1e-9)


def test_the_predicted_column_does_not_go_through_lapack(built):
    """The regression this guards is a one-digit diff that only CI could see.

    `np.polyfit` solves a least-squares system through LAPACK, and IEEE 754 says nothing
    about that: the answer's last bits depend on the BLAS the machine was built against.
    `fixed_line_subscribers` predicts exactly 0.0322415 for `theil_region` — a perfect tie
    at six decimals — and two machines rounded it in opposite directions, which the
    pipeline's byte-for-byte check caught and nothing else would have.

    This pins the value. It also pins the property that matters more: the fit is computed
    from `fit_line`, whose operations IEEE 754 requires to be correctly rounded.
    """
    table = D.pre_post(built, "theil_region")
    row = table.set_index("indicator").loc["fixed_line_subscribers"]
    assert row.predicted == pytest.approx(0.032241, abs=5e-7)

    pre = built[built.indicator.eq("fixed_line_subscribers")
                & built.period.eq("pre")].dropna(subset=["theil_region"])
    post = built[built.indicator.eq("fixed_line_subscribers")
                 & built.period.eq("post")].dropna(subset=["theil_region"])
    slope, intercept = D.fit_line(pre.year.to_numpy(dtype=float),
                                  pre.theil_region.to_numpy(dtype=float))
    expected = slope * float(post.year.mean()) + intercept - float(pre.theil_region.mean())
    assert row.predicted == pytest.approx(round(expected, D.DECIMALS), abs=1e-12)
