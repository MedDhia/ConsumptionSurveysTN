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
def estimates(built, series):
    from consumptiontn import build_monthly_prices as P

    frame, _ = built
    indices = pd.read_csv("data/processed/tn_governorate_inequality.csv")
    prices, _, _ = P.build(series, pd.read_csv("data/processed/tn_cpi_annual.csv"))
    return R.build(frame, indices, prices)


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


def test_every_column_computed_through_a_logarithm_is_rounded():
    """The defect that reached CI three times, pinned across all of its homes.

    IEEE 754 requires `+ - * /` to be correctly rounded, so ordinary arithmetic is
    portable and most float columns in this repository carry full precision safely. It
    says nothing about `log`, `exp` or `**`, and two libm versions genuinely disagree in
    the last bit: `atkinson_1` differed at the seventeenth decimal, then `log_value` on
    `log(455.7)`. Both failed the byte-for-byte build gate.

    So the rule is narrow rather than repository-wide — only columns computed through a
    transcendental function need it — and this test names them, so a fourth instance has
    to be added here deliberately rather than discovered by CI.
    """
    import numpy as np

    from consumptiontn import build_inequality_indices as I
    from consumptiontn import build_regional_inequality as G

    log_derived = {
        "data/processed/tn_governorate_inequality.csv": (
            ["theil_t", "theil_l", *I.ATKINSON_EPSILONS.values()], I.INDEX_DECIMALS),
        "data/processed/tn_governorate_dispersion.csv": (
            ["theil_weighted"], G.MEASURE_DECIMALS),
        "data/processed/tn_monthly_series.csv": (["log_value"], M.VALUE_DECIMALS),
    }
    for path, (columns, decimals) in log_derived.items():
        frame = pd.read_csv(path)
        for column in columns:
            values = frame[column].dropna()
            assert not values.empty, f"{path}:{column}"
            assert np.allclose(values, values.round(decimals)), f"{path}:{column}"


# ------------------------------------------------------------------------ monthly prices

@pytest.fixture(scope="module")
def priced(series):
    from consumptiontn import build_monthly_prices as P

    annual = pd.read_csv("data/processed/tn_cpi_annual.csv")
    return P.build(series, annual)


def test_the_monthly_cpi_reproduces_the_annual_index(priced):
    """The check with an outside referee.

    `tn_cpi_annual` is built from a different table and was verified separately, so a
    monthly series whose twelve months average to it is not agreeing with itself. A year
    assigned to the wrong base would be out by tens of percent and pass nothing.
    """
    _, check, _ = priced
    assert len(check) >= 8
    assert check.agrees.all(), check[~check.agrees].to_dict("records")
    assert (check.months == 12).all()
    # And the agreement is tight, not merely inside the tolerance.
    assert (check.gap / check.printed).max() < 0.004


def test_a_year_failing_the_annual_check_does_not_ship(priced):
    frame, check, _ = priced
    cpi = frame[frame.series.eq("cpi_general")]
    shipped = set(zip(cpi.base_year, cpi.year, strict=True))
    for row in check[~check.agrees].to_dict("records"):
        assert (row["base_year"], row["year"]) not in shipped


def test_the_two_industrial_bases_are_not_a_rescaling_of_each_other(priced):
    """The measured reason the two bases are published apart rather than chained.

    A rebasing rescales, so the ratio between bases would be one constant per sector.
    These are not: the basket was re-weighted too, unevenly across sectors.
    """
    _, _, factors = priced
    assert not factors.empty
    spread = factors.groupby("group").ratio.agg(lambda s: s.max() / s.min())
    assert spread.max() > 1.2, "no sector varies enough to justify refusing to chain"
    assert spread.min() < 1.05, "and at least one is nearly constant, so it is not noise"


def test_one_base_spans_the_cutoff_on_each_index(priced):
    """What makes chaining unnecessary for the design this feeds."""
    frame, _, _ = priced
    for name, base in (("cpi_general", 2005), ("industrial_prices", 2000)):
        block = frame[frame.series.eq(name) & frame.base_year.eq(base)]
        assert (block.running < 0).sum() >= 12, name
        assert (block.running >= 0).sum() >= 12, name


def test_the_price_log_is_rounded_like_every_other_logarithm(priced):
    from consumptiontn.build_monthly import VALUE_DECIMALS

    frame, _, _ = priced
    values = frame.log_value.dropna()
    assert not values.empty
    assert np.allclose(values, values.round(VALUE_DECIMALS))
