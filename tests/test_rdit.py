"""Checks on the regression-discontinuity-in-time estimator.

These are closed-form cases: data built so that the right answer is known before the
estimator sees it. An RD estimate is a number nobody can eyeball, and the failure mode
that matters -- a design that reports a tight interval around a quantity it has not
identified -- looks exactly like success, so the properties that rule it out are worth
pinning down rather than trusting.
"""

from __future__ import annotations

import numpy as np
import pytest

from consumptiontn import rdit


@pytest.fixture
def months():
    return np.arange(-60, 60, dtype=float)


def test_a_clean_jump_is_recovered_exactly(months):
    y = 0.03 * months + 2.5 * (months >= 0)
    assert rdit.fit(months, y, 24).tau == pytest.approx(2.5, abs=1e-9)


def test_a_kink_without_a_jump_reads_as_no_jump(months):
    """A slope change at the cutoff is not a discontinuity, and must not report as one."""
    y = 0.03 * months + 0.05 * months * (months >= 0)
    assert rdit.fit(months, y, 24).tau == pytest.approx(0.0, abs=1e-9)


def test_curvature_bias_shrinks_as_the_bandwidth_shrinks(months):
    """The premise of the whole design: get closer and the wrong shape matters less."""
    y = 0.03 * months + 4e-4 * months**2
    wide = abs(rdit.fit(months, y, 36).tau)
    narrow = abs(rdit.fit(months, y, 6).tau)
    assert narrow < wide / 5


def test_the_estimate_is_the_weights_applied_to_the_outcomes(months):
    """tau = w @ y is what the bias bound rests on, so it had better be true."""
    rng = np.random.default_rng(11)
    y = 0.03 * months + 1.5 * (months >= 0) + rng.normal(0, 0.4, months.size)
    estimate = rdit.fit(months, y, 24)
    assert estimate.weights @ y[estimate.used] == pytest.approx(estimate.tau)


def test_a_flat_bias_bound_reproduces_the_conventional_interval(months):
    """With curvature assumed away, the honest interval must be the usual one."""
    rng = np.random.default_rng(3)
    y = 0.03 * months + 1.5 * (months >= 0) + rng.normal(0, 0.4, months.size)
    estimate = rdit.fit(months, y, 24)
    low, high, bias = rdit.honest_interval(estimate, 0.0)
    assert bias == 0.0
    assert low == pytest.approx(estimate.tau - 1.96 * estimate.se, rel=1e-3)
    assert high == pytest.approx(estimate.tau + 1.96 * estimate.se, rel=1e-3)


def test_the_critical_value_grows_with_the_bias_it_has_to_cover():
    assert rdit.honest_critical_value(0.0) == pytest.approx(1.96, abs=5e-3)
    values = [rdit.honest_critical_value(b) for b in (0.0, 0.5, 1.0, 2.0, 4.0)]
    assert values == sorted(values)
    # Once the bias dominates, one tail of |N(b,1)| is negligible and the critical
    # value approaches the one-sided 1.645 rather than the two-sided 1.96.
    assert rdit.honest_critical_value(8.0) == pytest.approx(8.0 + 1.645, abs=0.05)


def test_the_worst_case_bias_grows_with_the_bandwidth(months):
    """This is what separates a local estimate from an extrapolated one."""
    rng = np.random.default_rng(5)
    y = 0.03 * months + rng.normal(0, 0.4, months.size)
    bounds = [rdit.worst_case_bias(rdit.fit(months, y, h), 1e-3) for h in (6, 12, 24, 48)]
    assert bounds == sorted(bounds)
    # The bound is quadratic in distance, so doubling the bandwidth roughly quadruples it.
    assert bounds[-1] / bounds[-2] == pytest.approx(4.0, rel=0.35)


def test_the_smoothness_bound_recovers_a_known_curvature(months):
    """A quadratic with coefficient a has |m''| = 2a everywhere."""
    assert rdit.smoothness_bound(months, 4e-4 * months**2) == pytest.approx(8e-4, rel=0.02)


def test_a_design_with_more_parameters_than_data_is_refused(months):
    """The failure this guards against reported a perfect fit and a zero standard error.

    Eleven month dummies inside a six-month window is more columns than rows; pinv
    answers that with a nonsense coefficient rather than raising, which is how a +234%
    jump in monthly exports once got as far as a rendered figure.
    """
    y = 0.03 * months + 1.5 * (months >= 0)
    seasonal = np.column_stack([((months % 12) == m).astype(float) for m in range(1, 12)])
    with pytest.raises(ValueError, match="rank-deficient|degrees of freedom"):
        rdit.fit(months, y, 6, controls=seasonal)


def test_deseasonalising_removes_month_effects_but_not_the_jump(months):
    season = 0.4 * np.sin(2 * np.pi * (months % 12) / 12)
    y = 0.01 * months + 0.9 * (months >= 0) + season
    adjusted = rdit.deseasonalise(months, y, months % 12)
    assert rdit.fit(months, adjusted, 24).tau == pytest.approx(0.9, abs=0.02)
    # The seasonal swing is gone, so month-of-year no longer predicts the residual.
    residual = adjusted - (0.01 * months + 0.9 * (months >= 0))
    assert residual.std() < 0.02


def test_randomisation_cannot_beat_the_floor_its_window_sets():
    """With few periods no outcome can produce a small p-value. That is the point."""
    running = np.arange(-3, 4, dtype=float)
    # A jump so large the test would reject if it could.
    y = 1000.0 * (running >= 0)
    p, periods, floor = rdit.randomisation_pvalue(running, y, 3)
    assert periods == 7
    # Four periods treated of seven: the complement has three, so it is not among the
    # arrangements and only the observed split attains the extreme.
    assert floor == pytest.approx(1 / 35)
    assert p == pytest.approx(floor)

    # An even split does admit the mirror image, and the floor doubles accordingly.
    even = np.arange(-3, 3, dtype=float)
    _, periods, floor = rdit.randomisation_pvalue(even, 1000.0 * (even >= 0), 3)
    assert periods == 6
    assert floor == pytest.approx(2 / 20)


def test_a_wider_window_lowers_the_floor():
    floors = []
    for half in (1, 2, 3):
        running = np.arange(-half, half + 1, dtype=float)
        floors.append(rdit.randomisation_pvalue(running, 1.0 * (running >= 0), half)[2])
    assert floors == sorted(floors, reverse=True)
    assert floors[0] > 0.05 and floors[-1] < 0.05
