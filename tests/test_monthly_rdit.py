"""Checks on the monthly series and the RDiT estimates built from them.

The monthly dataset exists to make one design possible, so what can go wrong with it is not
arithmetic but identity: a series that is silently the wrong table produces a confident
causal estimate about the wrong thing. One candidate here was exactly that, and the tests
below pin both the rejection and the checks that caught it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from consumptiontn import build_monthly as M
from consumptiontn import build_rdit_estimates as R


@pytest.fixture(scope="module")
def series() -> pd.DataFrame:
    return pd.read_csv("data/processed/tn_yearbook_series.csv", dtype={"panel": "string"})


@pytest.fixture(scope="module")
def built(series):
    return M.build(series)


# ------------------------------------------------------------------ identity, not arithmetic

def test_the_job_applications_series_stayed_out(built):
    """The rejection that matters most, because it looked like the best outcome here.

    Rows labelled with the twelve months sit under a job-applications title, and
    unemployment was the proximate grievance of the uprising. Table 6.1.6 is by governorate
    and prints no monthly panel; the rows come to about 5,800 a year against the 391,927
    printed for 2023. An RDiT on them would have been clean, publishable and wrong.
    """
    frame, _ = built
    assert "job_applications" not in set(frame.series)
    title = "evolution du nombre des demandes d emploi par gouvernorat enregistrées 6"
    assert title in M.EXCLUDED
    assert "not job applications" in M.EXCLUDED[title]
    assert not any(title in titles for titles, _, _ in M.SERIES.values())


def test_the_months_come_to_the_printed_total(built):
    """The check that is available, over the years it is available for."""
    _, check = built
    totals = check[check.check.str.startswith("the twelve months")]
    assert len(totals) >= 80
    assert totals.agrees.all(), totals[~totals.agrees].to_dict("records")


def test_the_tourist_modes_come_to_the_combined_figure(built):
    """The only arithmetic check departures has, since no edition prints a total."""
    _, check = built
    parts = check[check.check.str.startswith("air, land and sea")]
    assert len(parts) > 400
    assert parts.agrees.mean() > 0.95
    assert set(parts.series) == set(M.COMPONENTS)


def test_a_check_that_matched_nothing_raises_even_if_the_other_matched(series):
    """The first version filtered to `row_kind == "data"` before looking for the printed
    `Total`, which is an `aggregate` row, so that check compared nothing and reported no
    disagreements — indistinguishable from everything agreeing.

    Guarding only that the *combined* frame was non-empty was not enough either: the
    component check still matched, and masked it. Each kind has to have matched something.
    """
    with pytest.raises(RuntimeError, match="twelve months come to the printed total"):
        M.build(series[series.row_kind.eq("data")])


def test_a_failing_month_does_not_take_its_year(built):
    """A month-level refusal must remove that month, not the other eleven."""
    frame, check = built
    failed = check[~check.agrees & check.month.notna()]
    assert not failed.empty
    for row in failed.to_dict("records"):
        year = frame[frame.series.eq(row["series"]) & frame.year.eq(row["year"])]
        assert row["month"] not in set(year.month)
        assert len(year) >= 5, "the rest of the year should survive"


# ------------------------------------------------------------- the missingness that matters

def test_the_2011_tourism_gap_is_visible_in_the_data(built):
    """INS printed an ellipsis, not a number, for six months of 2011.

    They are the summer peak straight after the uprising, so the missingness is correlated
    with the treatment. A reader must be able to see that without reading the source.
    """
    frame, _ = built
    year = frame[frame.year.eq(2011)]
    tourism = year[year.series.str.startswith("tourist_")]
    assert (tourism.published_share == 0.5).all()
    for name in ("road_injuries", "road_deaths", "money_orders"):
        complete = year[year.series.eq(name)]
        assert len(complete) == 12, name
        assert (complete.published_share == 1.0).all()


def test_the_running_variable_puts_the_cutoff_on_a_sample_point(built):
    frame, _ = built
    assert (frame.running == frame.running.round()).all()
    january = frame[frame.year.eq(2011) & frame.month.eq(1)]
    assert (january.running == 0).all()
    assert january.treated.all(), "January 2011 is treated; the donut is what removes it"


# ------------------------------------------------------------------------ the estimates

@pytest.fixture(scope="module")
def estimates(built):
    frame, _ = built
    indices = pd.read_csv("data/processed/tn_governorate_inequality.csv")
    return R.build(frame, indices)


def test_the_annual_design_reports_that_it_cannot_answer(estimates):
    """The point of running the annual case at all.

    With at most 17 pre-cutoff years the worst-case bias exceeds the estimate almost
    everywhere, which is "not identified" rather than "no effect" — a distinction the
    dataset has to make in numbers rather than in prose.
    """
    annual = estimates[estimates.frequency.eq("annual") & estimates.refused.eq("")
                       & estimates.tau.notna()]
    assert not annual.empty
    assert annual.bias_exceeds_estimate.mean() > 0.8
    widest = annual[annual.bandwidth.eq(max(R.ANNUAL_BANDWIDTHS))]
    assert widest.bias_exceeds_estimate.all()


def test_the_worst_case_bias_grows_with_the_bandwidth(estimates):
    """The mechanism the whole design rests on.

    Not the interval *width*: that is bias against sampling noise, and the standard error
    falls as the window grows. For road injuries the noise term shrinks faster than the
    bias grows, so the interval is narrower at sixty months than at six while being far
    less trustworthy. The bias itself is what rises monotonically, and it is what says a
    wide-bandwidth estimate was never identified.
    """
    monthly = estimates[estimates.frequency.eq("monthly") & estimates.donut.eq(1)
                        & estimates.method.eq("continuity")
                        & estimates.worst_case_bias.notna()]
    for name, block in monthly.groupby("outcome"):
        block = block.sort_values("bandwidth")
        bias = block.worst_case_bias.to_numpy()
        assert (np.diff(bias) >= -1e-9).all(), name
        assert bias[-1] > bias[0], name


def test_a_window_with_nothing_on_one_side_is_refused_not_scored(estimates):
    """The artefact this guard exists for.

    With no pre-cutoff periods inside the window the difference in means is NaN, every
    permutation comparison against it is False, and the p-value comes back as exactly
    0.0 — which reads as overwhelming significance. Two annual outcomes hit it.
    """
    windows = estimates[estimates.method.eq("randomisation")
                        & estimates.frequency.eq("annual")]
    scored = windows[windows.randomisation_p.notna()]
    assert not scored.empty
    assert (scored.randomisation_p > 0).all(), "a permutation p of exactly zero is the bug"
    assert (scored.n_left >= R.MIN_PERIODS_PER_SIDE).all()
    assert (scored.n_right >= R.MIN_PERIODS_PER_SIDE).all()
    refused = windows[windows.randomisation_p.isna()]
    assert refused.refused.str.contains("periods before").all()


def test_the_randomisation_rows_are_distinguishable_from_the_estimates(estimates):
    """Windows 6 and 12 are also bandwidths, so without `method` a permutation row and a
    continuity estimate for the same outcome cannot be told apart."""
    assert set(estimates.method) == {"continuity", "randomisation"}
    assert estimates[estimates.method.eq("randomisation")].tau.isna().all()
    assert estimates[estimates.method.eq("continuity")].randomisation_p.isna().all()


def test_the_randomisation_floor_is_reported_beside_its_p_value(estimates):
    """With few periods the smallest achievable p-value can sit above 0.05, and then a
    non-rejection carries no information at all."""
    tests = estimates[estimates.randomisation_p.notna()]
    assert not tests.empty
    assert tests.randomisation_floor.notna().all()
    assert (tests.randomisation_floor > 0).all()


def test_every_monthly_outcome_is_estimated_with_and_without_the_donut(estimates):
    """January 2011 is half of each regime, so both readings are published."""
    monthly = estimates[estimates.frequency.eq("monthly")
                        & estimates.method.eq("continuity")]
    for (name, bandwidth), block in monthly.groupby(["outcome", "bandwidth"]):
        # Both are always *attempted*; one may be refused, and then it carries a reason
        # rather than being absent, so a reader can see the window was tried.
        assert set(block.donut) == {0, 1}, (name, bandwidth)
        assert (block.tau.notna() | block.refused.ne("")).all(), (name, bandwidth)


def test_the_estimates_are_rounded_for_reproducibility(estimates):
    """Same rule as the inequality indices: these are sums of products of floats."""
    for column in ("tau", "se", "honest_lo", "honest_hi", "worst_case_bias"):
        values = estimates[column].dropna()
        assert np.allclose(values, values.round(6))
