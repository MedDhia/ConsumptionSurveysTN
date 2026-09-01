"""RDiT estimates at January 2011, across every outcome the corpus can support.

This is the design question the repository has been circling: did the revolution change
anything measurable, and can the change be attributed to it rather than merely dated to it.
The answer differs by *frequency*, and separating the two cases is the whole point of
running both here.

**Monthly outcomes can be estimated.** Five count series and two price indices run at
monthly frequency through January 2011, with between 24 and 192 pre-cutoff months. A
six-month bandwidth holds six observations either side, so the estimate is local in the
sense continuity-based RD requires, and the Armstrong-Kolesar honest interval stays finite
and interpretable.

**Annual outcomes cannot.** The governorate inequality indices have at most 17 pre-cutoff
years and 13 after. Shrinking the bandwidth to anything deserving the name "local" leaves
too few points to fit, and at the bandwidths that do fit, the worst-case bias exceeds the
estimate. They are still reported, because "this design cannot answer the question" is a
result the reader needs stated in the same units as the ones that can, rather than left
as an absence.

**Every estimate carries four things**, and the fourth is what stops the first being
oversold:

* ``tau`` -- the jump at the cutoff, in logs for the monthly counts, so it reads as a
  proportional change.
* ``se`` -- HAC, because monthly series are autocorrelated and a conventional standard
  error would be too small.
* ``honest_lo/hi`` -- the bias-aware interval. As the bandwidth widens the worst-case bias
  grows with it, so an interval that stays tight at six months and explodes at sixty is
  telling you the wide-bandwidth number was never identified.
``method`` separates the two kinds of row, and is not cosmetic: the randomisation windows
are 6 and 12, which are also bandwidths, so without it a permutation row and a continuity
estimate for the same outcome are indistinguishable.

* ``randomisation_p`` and ``randomisation_floor`` -- permutation inference inside the
  window, and the smallest p-value that window could possibly produce. With few periods
  the floor sits above 0.05, and then the test cannot reject whatever the data say. A
  p-value of 0.12 against a floor of 0.11 is not weak evidence of no effect; it is no
  evidence either way.

**January 2011 is treated and also dropped.** Ben Ali left on the 14th, so the month is
half of each regime. Every monthly outcome is estimated twice, with and without a
one-month donut, and both are reported: if they disagree the estimate is picking up the
transition rather than a step to a new level.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from consumptiontn import rdit

# Six months is the narrowest window that fits a local linear with room to spare; sixty is
# wide enough that the honest interval should visibly deteriorate if the design is weak.
MONTHLY_BANDWIDTHS = (6, 12, 24, 36, 60)

# In years, for the annual outcomes. Even the widest holds fewer points than the narrowest
# monthly window.
ANNUAL_BANDWIDTHS = (5, 8, 12)

# Windows for the local randomisation test, in months and years respectively.
MONTHLY_RANDOMISATION = (6, 12)
ANNUAL_RANDOMISATION = (4, 6)

REVOLUTION = 2011

# A permutation test needs periods on both sides of the cutoff inside the window. With
# none on one side the difference in means is NaN, every comparison against it is False,
# and the p-value comes back as exactly 0.0 -- which reads as overwhelming significance
# and is an artefact. Two a side is the minimum worth reporting.
MIN_PERIODS_PER_SIDE = 2


def _randomisation(running: np.ndarray, y: np.ndarray, window: float,
                   label: dict) -> dict:
    """The permutation test, or a refusal where the window cannot support one."""
    good = np.isfinite(y)
    inside = (np.abs(running) <= window) & good
    left = len(np.unique(running[inside & (running < 0)]))
    right = len(np.unique(running[inside & (running >= 0)]))
    row = {**label, "method": "randomisation",
           "bandwidth": window, "donut": 0, "tau": np.nan, "se": np.nan,
           "n_left": left, "n_right": right, "honest_lo": np.nan, "honest_hi": np.nan,
           "worst_case_bias": np.nan}
    if min(left, right) < MIN_PERIODS_PER_SIDE:
        return {**row, "randomisation_p": np.nan, "randomisation_floor": np.nan,
                "refused": f"only {left} periods before and {right} after in the window"}
    p, periods, floor = rdit.randomisation_pvalue(running, y, window)
    return {**row, "randomisation_p": p, "randomisation_floor": floor, "refused": ""}


def _estimate(running: np.ndarray, y: np.ndarray, bandwidth: float, *,
              donut: float, smoothness: float, label: dict) -> dict | None:
    """One fit with its honest interval, or None where the bandwidth cannot support one."""
    try:
        fit = rdit.fit(running, y, bandwidth, donut=donut)
    except ValueError as exc:
        return {**label, "method": "continuity", "bandwidth": bandwidth, "donut": donut,
                "tau": np.nan, "se": np.nan, "n_left": 0, "n_right": 0,
                "honest_lo": np.nan, "honest_hi": np.nan, "worst_case_bias": np.nan,
                "refused": str(exc)}
    lo, hi, bias = rdit.honest_interval(fit, smoothness)
    return {
        **label, "method": "continuity", "bandwidth": bandwidth, "donut": donut,
        "tau": fit.tau, "se": fit.se, "n_left": fit.n_left, "n_right": fit.n_right,
        "honest_lo": lo, "honest_hi": hi, "worst_case_bias": bias, "refused": "",
    }


def monthly_estimates(monthly: pd.DataFrame) -> pd.DataFrame:
    """RDiT on each monthly series, deseasonalised log level, at every bandwidth."""
    rows = []
    for name, block in monthly.groupby("series", sort=True):
        block = block.sort_values("running")
        running = block.running.to_numpy(dtype=float)
        month = block.month.to_numpy(dtype=int)
        y = block.log_value.to_numpy(dtype=float)
        good = np.isfinite(y)
        if good.sum() < 60:
            continue
        # Seasonality is stripped once over the whole series rather than inside the
        # window: at six months there are more month dummies than observations.
        adjusted = rdit.deseasonalise(running[good], y[good], month[good])
        r = running[good]
        smoothness = rdit.smoothness_bound(r, adjusted)

        label = {"outcome": name, "frequency": "monthly", "scale": "log",
                 "smoothness": smoothness}
        for bandwidth in MONTHLY_BANDWIDTHS:
            for donut in (0, 1):
                rows.append(_estimate(r, adjusted, bandwidth, donut=donut,
                                      smoothness=smoothness, label=label))
        for window in MONTHLY_RANDOMISATION:
            rows.append(_randomisation(r, adjusted, window, label))
    return pd.DataFrame(rows)


def price_estimates(prices: pd.DataFrame) -> pd.DataFrame:
    """RDiT on each monthly price index, separately on each base it is printed on.

    Deliberately not run on a spliced series. One base spans January 2011 on each index --
    CPI 2005 and IPI 2000 -- so the estimate never needs a chain, and running the two bases
    apart makes them independent measurements of the same discontinuity rather than one
    measurement of a series whose join was assumed.
    """
    rows = []
    keys = ["series", "group", "base_year"]
    for (name, group, base), block in prices.groupby(keys, sort=True):
        block = block.sort_values("running")
        y = block.log_value.to_numpy(dtype=float)
        good = np.isfinite(y)
        r = block.running.to_numpy(dtype=float)[good]
        # Both sides of the cutoff, or there is no discontinuity to estimate.
        if (r < 0).sum() < 12 or (r >= 0).sum() < 12:
            continue
        adjusted = rdit.deseasonalise(r, y[good], block.month.to_numpy(dtype=int)[good])
        smoothness = rdit.smoothness_bound(r, adjusted)
        outcome = name if group in ("all items",) else f"{name}: {group}"
        label = {"outcome": f"{outcome} (base {int(base)})", "frequency": "monthly",
                 "scale": "log", "smoothness": smoothness}
        for bandwidth in MONTHLY_BANDWIDTHS:
            if bandwidth > max(abs(r).max(), 1):
                continue
            for donut in (0, 1):
                rows.append(_estimate(r, adjusted, bandwidth, donut=donut,
                                      smoothness=smoothness, label=label))
        for window in MONTHLY_RANDOMISATION:
            rows.append(_randomisation(r, adjusted, window, label))
    return pd.DataFrame(rows)


def annual_estimates(indices: pd.DataFrame, measure: str = "gini") -> pd.DataFrame:
    """The same design on the annual inequality indices, where it has far less to work with.

    Reported so that the contrast with the monthly outcomes is visible in one table rather
    than argued for in prose.
    """
    rows = []
    long = indices[indices.basis.eq("share_of_national")
                   & indices.geography.eq("constant")
                   & indices.weighting.eq("unweighted")]
    for name, block in long.groupby("indicator", sort=True):
        block = block.dropna(subset=[measure]).sort_values("year")
        if len(block) < 20:
            continue
        running = (block.year.to_numpy(dtype=float) - REVOLUTION)
        y = block[measure].to_numpy(dtype=float)
        smoothness = rdit.smoothness_bound(running, y)
        label = {"outcome": name, "frequency": "annual", "scale": measure,
                 "smoothness": smoothness}
        for bandwidth in ANNUAL_BANDWIDTHS:
            rows.append(_estimate(running, y, bandwidth, donut=0,
                                  smoothness=smoothness, label=label))
        for window in ANNUAL_RANDOMISATION:
            rows.append(_randomisation(running, y, window, label))
    return pd.DataFrame(rows)


def build(monthly: pd.DataFrame | None = None,
          indices: pd.DataFrame | None = None,
          prices: pd.DataFrame | None = None) -> pd.DataFrame:
    """Every RDiT estimate at the January 2011 cutoff, monthly and annual."""
    if monthly is None:
        monthly = pd.read_csv("data/processed/tn_monthly_series.csv")
    if indices is None:
        indices = pd.read_csv("data/processed/tn_governorate_inequality.csv")
    if prices is None:
        prices = pd.read_csv("data/processed/tn_monthly_prices.csv")

    frame = pd.concat([monthly_estimates(monthly), price_estimates(prices),
                       annual_estimates(indices)], ignore_index=True)
    if frame.empty:
        raise RuntimeError("no RDiT estimate could be produced")

    for column in ("randomisation_p", "randomisation_floor"):
        if column not in frame:
            frame[column] = np.nan

    # An estimate whose honest interval covers zero cannot distinguish a jump from none,
    # and one whose worst-case bias exceeds its own point estimate is not identified at
    # that bandwidth whatever the interval says. Both are carried rather than filtered,
    # because which bandwidths fail is the finding.
    frame["honest_excludes_zero"] = (
        frame.honest_lo.notna() & ((frame.honest_lo > 0) | (frame.honest_hi < 0)))
    frame["bias_exceeds_estimate"] = (
        frame.worst_case_bias.notna() & (frame.worst_case_bias > frame.tau.abs()))

    # Same reproducibility rule as the inequality indices: these are sums of products of
    # floats and their last bits are not portable across machines.
    #
    # `randomisation_floor` is deliberately excluded. It is 1/C(n, k) from exact integer
    # arithmetic, so it is portable already -- and for a 192-month window it is far below
    # 1e-6, which six decimals would flatten to 0.0 and misreport as "no floor at all"
    # exactly where the floor is most reassuring.
    numeric = ["tau", "se", "honest_lo", "honest_hi", "worst_case_bias", "smoothness",
               "randomisation_p"]
    frame[numeric] = frame[numeric].round(6)
    columns = ["outcome", "frequency", "scale", "method", "bandwidth", "donut",
               "n_left", "n_right",
               "tau", "se", "honest_lo", "honest_hi", "worst_case_bias",
               "honest_excludes_zero", "bias_exceeds_estimate",
               "randomisation_p", "randomisation_floor", "smoothness", "refused"]
    return frame[columns].sort_values(
        ["frequency", "outcome", "method", "bandwidth", "donut"], ignore_index=True)
