"""Regression discontinuity in time, with the diagnostics the design actually needs.

The January 2011 revolution is a sharp, unanticipated, nationwide break. That rules out
every design needing an untreated unit, but it is exactly the setting regression
discontinuity in time is written for (Hausman and Rapson 2018): the running variable is
the calendar, the cutoff is the event, and nobody can manipulate their position on the
time axis.

Two things separate an RDiT that identifies something from one that is an extrapolated
trend wearing RD notation, and both are implemented here.

**Frequency.** Continuity-based RD leans on shrinking the bandwidth toward the cutoff.
With monthly data that is possible -- a six-month window holds twelve observations. With
annual data it is not, and the estimate is driven by the functional form assumed over a
decade. So the honest bias bound below is not a robustness check bolted on at the end; it
is the thing that tells the two cases apart.

**Bias, not just noise.** A conventional standard error asks how much the estimate would
move under resampling. It says nothing about the local polynomial being the wrong shape,
which is the dominant error at wide bandwidths. Kolesar and Rothe (2018) and Armstrong
and Kolesar (2018) fix this: bound the curvature of the conditional mean by ``M``, take
the worst-case bias over that class, and widen the interval to cover it. As the bandwidth
grows the worst-case bias grows with it, so an interval that stays tight at ``h = 6`` and
explodes at ``h = 60`` is telling you the wide-bandwidth number was never identified.

Everything is numpy so that the pipeline keeps its current dependencies; the estimators
are the standard ones and are checked against closed-form cases in the tests.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Ben Ali left on 14 January 2011. A monthly series is dated to the first of the month,
# so January 2011 is the first period whose outcome could have been affected, and the
# running variable is months from that point.
CUTOFF = 2011 + 0 / 12


def triangular(u: np.ndarray) -> np.ndarray:
    """The kernel RD defaults to: linear down-weighting, zero outside the bandwidth."""
    return np.clip(1.0 - np.abs(u), 0.0, None)


def uniform(u: np.ndarray) -> np.ndarray:
    return (np.abs(u) <= 1.0).astype(float)


KERNELS = {"triangular": triangular, "uniform": uniform}


@dataclass(frozen=True)
class Fit:
    """One local-polynomial RD estimate and everything needed to reason about it."""

    tau: float
    se: float
    weights: np.ndarray       # tau = weights @ y, which is what bounds the bias
    running: np.ndarray       # running variable of the observations actually used
    used: np.ndarray          # boolean mask back into the input arrays
    n_left: int
    n_right: int
    bandwidth: float

    @property
    def n(self) -> int:
        return self.n_left + self.n_right


def _design(running: np.ndarray, degree: int, controls: np.ndarray | None) -> np.ndarray:
    """Intercept, treatment, and a polynomial in time allowed to differ on each side.

    Letting the slope differ across the cutoff is what makes the estimate a jump rather
    than a jump-plus-slope-change, and it is why the estimator is exactly unbiased for
    any piecewise-polynomial mean of this degree -- the fact the bias bound rests on.
    """
    treated = (running >= 0).astype(float)
    columns = [np.ones_like(running), treated]
    for power in range(1, degree + 1):
        columns.append(running**power)
        columns.append(treated * running**power)
    if controls is not None:
        columns.append(controls if controls.ndim == 2 else controls[:, None])
    return np.column_stack([c if c.ndim == 2 else c[:, None] for c in columns])


def _hac(residuals: np.ndarray, design: np.ndarray, bread: np.ndarray,
         weights: np.ndarray, lags: int) -> np.ndarray:
    """Newey-West meat. Monthly series are autocorrelated; ignoring it understates se."""
    scores = design * (residuals * weights)[:, None]
    meat = scores.T @ scores
    for lag in range(1, lags + 1):
        band = 1.0 - lag / (lags + 1.0)
        cross = scores[lag:].T @ scores[:-lag]
        meat += band * (cross + cross.T)
    return bread @ meat @ bread


def fit(running: np.ndarray, y: np.ndarray, bandwidth: float, *, degree: int = 1,
        kernel: str = "triangular", donut: float = 0.0,
        controls: np.ndarray | None = None, hac_lags: int = 12) -> Fit:
    """Local polynomial RD estimate of the jump at zero on the running variable.

    ``donut`` drops observations within that distance of the cutoff. Here it is not about
    manipulation -- time cannot be manipulated -- but about the transition itself: the
    weeks around the uprising are neither the old regime nor the new one, and a month
    that is half of each belongs to neither side of the comparison.
    """
    running = np.asarray(running, dtype=float)
    y = np.asarray(y, dtype=float)
    inside = (np.abs(running) <= bandwidth) & (np.abs(running) >= donut) & np.isfinite(y)
    if inside.sum() < 2 * (degree + 2):
        raise ValueError(f"bandwidth {bandwidth} leaves too few observations to fit")

    r = running[inside]
    outcome = y[inside]
    sub_controls = None if controls is None else np.asarray(controls)[inside]
    kernel_weights = KERNELS[kernel](r / bandwidth)
    if not (kernel_weights > 0).sum() > 2 * (degree + 2):
        raise ValueError(f"bandwidth {bandwidth} leaves too few weighted observations")

    design = _design(r, degree, sub_controls)
    # A narrow window plus eleven month dummies is more parameters than observations,
    # and pinv answers that with a perfect fit, a zero standard error and a nonsense
    # coefficient rather than an error. Refuse it instead.
    effective = int((kernel_weights > 0).sum())
    rank = int(np.linalg.matrix_rank(design[kernel_weights > 0]))
    if rank < design.shape[1]:
        raise ValueError(
            f"bandwidth {bandwidth} leaves the design rank-deficient "
            f"({rank} of {design.shape[1]} columns identified)"
        )
    if effective - rank < 5:
        raise ValueError(
            f"bandwidth {bandwidth} leaves {effective - rank} residual degrees of "
            f"freedom ({effective} observations, {rank} parameters); too few to fit"
        )
    gram = design.T @ (design * kernel_weights[:, None])
    bread = np.linalg.pinv(gram)
    beta = bread @ (design.T @ (outcome * kernel_weights))

    # tau is linear in the outcomes; those coefficients are what the bias bound needs.
    influence = bread @ (design * kernel_weights[:, None]).T
    weight_vector = influence[1]

    residuals = outcome - design @ beta
    order = np.argsort(r)
    variance = _hac(residuals[order], design[order], bread,
                    kernel_weights[order], min(hac_lags, max(len(r) // 4, 1)))
    return Fit(
        tau=float(beta[1]),
        se=float(np.sqrt(max(variance[1, 1], 0.0))),
        weights=weight_vector,
        running=r,
        used=inside,
        n_left=int((r < 0).sum()),
        n_right=int((r >= 0).sum()),
        bandwidth=float(bandwidth),
    )


def deseasonalise(running: np.ndarray, y: np.ndarray, month: np.ndarray,
                  degree: int = 4) -> np.ndarray:
    """Strip month-of-year effects, estimated once on the whole sample.

    Putting month dummies inside the local window couples seasonal adjustment to the
    bandwidth: at six months there are more dummies than observations. Estimating them
    once over the full series decouples the two, and the trend here is allowed to bend
    *and to jump at the cutoff* so that the discontinuity being tested for cannot be
    soaked up into a seasonal factor.
    """
    running = np.asarray(running, dtype=float)
    y = np.asarray(y, dtype=float)
    month = np.asarray(month)
    scale = np.abs(running).max()
    z = running / scale
    treated = (running >= 0).astype(float)

    seasonal = np.column_stack([(month == m).astype(float) for m in np.unique(month)[1:]])
    trend = [np.ones_like(z), treated]
    for power in range(1, degree + 1):
        trend.append(z**power)
        trend.append(treated * z**power)
    design = np.column_stack(trend + [seasonal])
    beta = np.linalg.lstsq(design, y, rcond=None)[0]
    return y - seasonal @ beta[-seasonal.shape[1]:]


def _normal_cdf(x: np.ndarray | float) -> np.ndarray | float:
    """Standard normal CDF via erf, so scipy is not needed."""
    from math import erf
    return np.vectorize(lambda v: 0.5 * (1.0 + erf(v / np.sqrt(2.0))))(x)


def honest_critical_value(bias_ratio: float, alpha: float = 0.05) -> float:
    """The 1-alpha quantile of |N(bias_ratio, 1)|.

    The usual 1.96 is this at bias_ratio = 0. It grows with the worst-case bias, which is
    how the interval pays for the curvature it cannot rule out.
    """
    lo, hi = 0.0, 50.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        covered = _normal_cdf(mid - bias_ratio) - _normal_cdf(-mid - bias_ratio)
        if covered < 1.0 - alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def worst_case_bias(estimate: Fit, smoothness: float) -> float:
    """Largest bias the estimator can have if the mean's curvature is at most ``M``.

    The design is exactly unbiased for piecewise-linear means, so only the part of the
    conditional mean that a line misses can bias it, and on the Taylor class that part is
    at most ``M r^2 / 2`` at distance ``r``.
    """
    return float(smoothness / 2.0 * np.sum(np.abs(estimate.weights) * estimate.running**2))


def honest_interval(estimate: Fit, smoothness: float,
                    alpha: float = 0.05) -> tuple[float, float, float]:
    """Bias-aware confidence interval, and the worst-case bias it had to absorb."""
    bias = worst_case_bias(estimate, smoothness)
    half_width = honest_critical_value(bias / estimate.se, alpha) * estimate.se
    return estimate.tau - half_width, estimate.tau + half_width, bias


def smoothness_bound(running: np.ndarray, y: np.ndarray,
                     controls: np.ndarray | None = None, degree: int = 4) -> float:
    """Calibrate ``M`` from the data: the curvature a global polynomial actually shows.

    Armstrong and Kolesar's point is that ``M`` cannot be estimated from the data at the
    cutoff -- that is the whole difficulty -- so it has to be asserted. Asserting it from
    the curvature the series displays away from the cutoff is the standard compromise,
    and every figure that uses it also shows the answer across a range of ``M``.
    """
    running = np.asarray(running, dtype=float)
    y = np.asarray(y, dtype=float)
    good = np.isfinite(y)
    r, outcome = running[good], y[good]
    scale = np.abs(r).max()
    z = r / scale  # conditioning: raw months to the fourth power overflows the fit
    columns = [np.ones_like(z)] + [z**p for p in range(1, degree + 1)]
    if controls is not None:
        block = np.asarray(controls)[good]
        columns.append(block if block.ndim == 2 else block[:, None])
    design = np.column_stack([c if c.ndim == 2 else c[:, None] for c in columns])
    beta = np.linalg.lstsq(design, outcome, rcond=None)[0]

    grid = np.linspace(z.min(), z.max(), 400)
    second = np.zeros_like(grid)
    for power in range(2, degree + 1):
        second += beta[power] * power * (power - 1) * grid ** (power - 2)
    return float(np.abs(second).max() / scale**2)


def cross_validated_bandwidth(running: np.ndarray, y: np.ndarray, grid: np.ndarray, *,
                              degree: int = 1, controls: np.ndarray | None = None,
                              edge: float = 0.5) -> float:
    """Pick a bandwidth by leave-one-out prediction on each side of the cutoff.

    The MSE-optimal rule assumes the local approximation is good, which is the thing in
    doubt at annual frequency, so this uses out-of-sample prediction instead: for each
    point, fit one side with the point held out and predict it. ``edge`` restricts
    scoring to the half of the data nearest the cutoff, where the fit has to be right.
    """
    running = np.asarray(running, dtype=float)
    y = np.asarray(y, dtype=float)
    span = np.abs(running).max()
    scores = []
    for bandwidth in grid:
        errors = []
        for i, point in enumerate(running):
            if not np.isfinite(y[i]) or np.abs(point) > edge * span:
                continue
            side = (running >= 0) == (point >= 0)
            near = side & (np.abs(running - point) <= bandwidth) & np.isfinite(y)
            near[i] = False
            if near.sum() < degree + 2:
                continue
            local = running[near] - point
            columns = [np.ones_like(local)] + [local**p for p in range(1, degree + 1)]
            if controls is not None:
                block = np.asarray(controls)[near]
                columns.append(block if block.ndim == 2 else block[:, None])
            design = np.column_stack([c if c.ndim == 2 else c[:, None] for c in columns])
            kernel_weights = triangular((running[near] - point) / bandwidth)
            gram = design.T @ (design * kernel_weights[:, None])
            beta = np.linalg.pinv(gram) @ (design.T @ (y[near] * kernel_weights))
            predicted = beta[0]
            if controls is not None:
                block = np.asarray(controls)[i]
                predicted += np.atleast_1d(beta[-np.atleast_1d(block).size:]) @ np.atleast_1d(block)
            errors.append((y[i] - predicted) ** 2)
        scores.append(np.mean(errors) if errors else np.inf)
    return float(grid[int(np.argmin(scores))])


def randomisation_pvalue(running: np.ndarray, y: np.ndarray, window: float, *,
                         controls: np.ndarray | None = None,
                         draws: int = 20000, seed: int = 20110114
                         ) -> tuple[float, int, float]:
    """Local randomisation test: difference in means, inference by permutation.

    Inside a narrow enough window the continuity assumption can be replaced by treating
    the periods as if the cutoff had been placed at random among them. That is a stronger
    assumption but it gives finite-sample-exact inference, which matters when the running
    variable has few distinct values.

    Returns the two-sided p-value, the number of periods in the window, and the smallest
    p-value the window could possibly have produced -- because with few periods that
    floor can sit above 0.05, and then the test cannot reject whatever the data say.
    """
    from math import comb

    running = np.asarray(running, dtype=float)
    y = np.asarray(y, dtype=float)
    inside = (np.abs(running) <= window) & np.isfinite(y)
    r, outcome = running[inside], y[inside]
    if controls is not None:
        block = np.asarray(controls)[inside]
        block = block if block.ndim == 2 else block[:, None]
        design = np.column_stack([np.ones_like(r), block])
        outcome = outcome - design @ np.linalg.lstsq(design, outcome, rcond=None)[0]
        outcome = outcome + outcome.mean()

    periods = np.unique(r)
    treated_periods = int((periods >= 0).sum())
    n_periods = len(periods)
    by_period = np.array([outcome[r == p].mean() for p in periods])
    observed = by_period[periods >= 0].mean() - by_period[periods < 0].mean()

    # The smallest p the window can return is the share of arrangements that tie with
    # the most extreme one. Generically that is a single arrangement. Only when the
    # window splits exactly in half is the complement also in the enumeration, giving
    # the mirror-image statistic and a second tie.
    total = comb(n_periods, treated_periods)
    floor = (2.0 if 2 * treated_periods == n_periods else 1.0) / total
    rng = np.random.default_rng(seed)
    extreme = 0
    if total <= draws:
        from itertools import combinations
        arrangements = list(combinations(range(n_periods), treated_periods))
        for picked in arrangements:
            mask = np.zeros(n_periods, dtype=bool)
            mask[list(picked)] = True
            statistic = by_period[mask].mean() - by_period[~mask].mean()
            extreme += abs(statistic) >= abs(observed) - 1e-12
        return extreme / len(arrangements), n_periods, min(floor, 1.0)

    for _ in range(draws):
        mask = np.zeros(n_periods, dtype=bool)
        mask[rng.choice(n_periods, treated_periods, replace=False)] = True
        statistic = by_period[mask].mean() - by_period[~mask].mean()
        extreme += abs(statistic) >= abs(observed) - 1e-12
    return (extreme + 1) / (draws + 1), n_periods, min(floor, 1.0)
