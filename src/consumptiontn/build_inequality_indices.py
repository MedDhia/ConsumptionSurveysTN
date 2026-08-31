"""Conventional inequality indices for the governorate distribution, year by year.

The rest of this repository deliberately avoided these, showing observed quantities and
ratios between them instead. That constraint has been lifted for this analysis: the
question is how regional inequality *evolved*, and a longitudinal answer needs one
comparable number per year. So this module computes the standard family, and computes
several rather than one, because the choice of index is a choice about which part of the
distribution matters and reporting a single one hides that choice.

**What each index is sensitive to**, which is the reason for carrying all of them:

* ``gini`` -- the whole distribution, most sensitive around the middle. The default, and
  the one to lead with, but it is close to blind to the extreme tails.
* ``theil_t`` -- weights the top. A governorate pulling far above the mean moves it most.
* ``theil_l`` (mean log deviation) -- weights the bottom. The mirror of ``theil_t``, and
  the pair together says *where* in the distribution a change happened. If they diverge,
  that is the finding.
* ``atkinson_05``, ``atkinson_1``, ``atkinson_2`` -- the same distribution read with
  increasing aversion to inequality at the bottom. ε=2 is dominated by the worst-off
  governorate.
* ``cv`` -- the coefficient of variation, sensitive to the squared distance from the mean,
  so it is the most volatile of the set and the most moved by one outlier.
* ``p90_p10``, ``p80_p20`` -- ratios between positions in the distribution rather than
  summaries of all of it. Immune to what happens in the tails beyond the cut points, which
  is exactly why they are worth reporting beside indices that are not.

**All of them are computed twice**, population-weighted and unweighted, and the two answer
different questions. Weighted treats the distribution as one over *people*: a Tunisian
picked at random. Unweighted treats it as one over *governorates*: an administrative unit
picked at random. Weighted is the one to report for a claim about inequality between
Tunisians; unweighted is the one that matches how a governorate-level regression treats its
observations. They can move in opposite directions, and when they do it means a change
concentrated in small governorates.

**The 2005 constraint applies to the weighted family only.** Weighting needs a population
and the corpus has no governorate population before 2005, so the weighted indices start
there while the unweighted ones run from 1994. This is the same trade recorded in
``build_regional_inequality`` and it is not fixable from inside this corpus.

**Zeros and the log measures.** Theil-L and Atkinson with ε≥1 are undefined when any unit
has zero, and unlike a floor or an epsilon that would quietly invent a number, those cells
are left empty. A governorate with no cinema screens is a real observation; the index
simply has nothing to say about it. ``gini``, ``cv`` and the ratios survive zeros and are
what to read on those series.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Aversion parameters for Atkinson, mapped to their column names explicitly. 0.5 is mild,
# 1 is the log case, 2 is strongly bottom-weighted; naming them in the column keeps the
# choice visible to a reader rather than buried in a default.
ATKINSON_EPSILONS = {0.5: "atkinson_05", 1.0: "atkinson_1", 2.0: "atkinson_2"}

# Percentile pairs, read on the population-weighted distribution when weights exist.
PERCENTILE_PAIRS = ((90, 10), (80, 20))

REVOLUTION = 2011

# Every index is rounded before it is written, matching GINI_DECIMALS in
# build_regional_products. This is not cosmetic: `atkinson_1` sums logarithms, and the
# order numpy reduces a sum in varies with the CPU and build, so two machines computing
# the same index disagreed in the last bit -- 0.0654996901199798 here against
# 0.06549969011997958 in CI. That is invisible to any reading of the number and fatal to a
# repository whose contract is that a fresh build reproduces the committed files byte for
# byte. Six decimals is a hundred million times coarser than the disagreement and far finer
# than anything these indices are interpreted at.
INDEX_DECIMALS = 6


def _shares(weights: np.ndarray | None, n: int) -> np.ndarray:
    if weights is None:
        return np.full(n, 1.0 / n)
    total = weights.sum()
    if total <= 0:
        raise ValueError("weights sum to zero")
    return weights / total


def gini(y: np.ndarray, weights: np.ndarray | None = None) -> float:
    """Weighted Gini by the mean-absolute-difference definition.

    Written as the double sum rather than the sorted-cumulative shortcut because with 24
    units it costs nothing and the formula is the definition, so it cannot be wrong in the
    way an off-by-one in the ranking version silently is.
    """
    if len(y) < 2 or np.any(~np.isfinite(y)):
        return np.nan
    p = _shares(weights, len(y))
    mean = float((p * y).sum())
    if mean <= 0:
        return np.nan
    diff = np.abs(y[:, None] - y[None, :])
    return float((p[:, None] * p[None, :] * diff).sum() / (2.0 * mean))


def theil_t(y: np.ndarray, weights: np.ndarray | None = None) -> float:
    """Theil-T. Top-sensitive. Undefined if anything is zero."""
    if len(y) < 2 or np.any(y <= 0) or np.any(~np.isfinite(y)):
        return np.nan
    p = _shares(weights, len(y))
    mean = float((p * y).sum())
    if mean <= 0:
        return np.nan
    ratio = y / mean
    return float((p * ratio * np.log(ratio)).sum())


def theil_l(y: np.ndarray, weights: np.ndarray | None = None) -> float:
    """Mean log deviation. Bottom-sensitive: the mirror of Theil-T."""
    if len(y) < 2 or np.any(y <= 0) or np.any(~np.isfinite(y)):
        return np.nan
    p = _shares(weights, len(y))
    mean = float((p * y).sum())
    if mean <= 0:
        return np.nan
    return float((p * np.log(mean / y)).sum())


def atkinson(y: np.ndarray, epsilon: float, weights: np.ndarray | None = None) -> float:
    """Atkinson index at the given aversion parameter.

    Bounded in [0, 1) and read as the share of total provision society would be willing to
    give up for an equal distribution.
    """
    if len(y) < 2 or np.any(y <= 0) or np.any(~np.isfinite(y)):
        return np.nan
    p = _shares(weights, len(y))
    mean = float((p * y).sum())
    if mean <= 0:
        return np.nan
    if np.isclose(epsilon, 1.0):
        equivalent = float(np.exp((p * np.log(y)).sum()))
    else:
        power = float((p * y ** (1.0 - epsilon)).sum())
        if power <= 0:
            return np.nan
        equivalent = power ** (1.0 / (1.0 - epsilon))
    return float(1.0 - equivalent / mean)


def coefficient_of_variation(y: np.ndarray, weights: np.ndarray | None = None) -> float:
    if len(y) < 2 or np.any(~np.isfinite(y)):
        return np.nan
    p = _shares(weights, len(y))
    mean = float((p * y).sum())
    if mean <= 0:
        return np.nan
    variance = float((p * (y - mean) ** 2).sum())
    return float(np.sqrt(variance) / mean)


def weighted_percentile(y: np.ndarray, q: float,
                        weights: np.ndarray | None = None) -> float:
    """The value at percentile ``q`` of the distribution over people.

    With 24 units and population weights, a percentile is a step function; this takes the
    value of the unit in which the cumulative population share crosses ``q``, which is the
    conventional reading and needs no interpolation between governorates that would invent
    a value nothing observed.
    """
    if len(y) == 0 or np.any(~np.isfinite(y)):
        return np.nan
    p = _shares(weights, len(y))
    order = np.argsort(y)
    cumulative = np.cumsum(p[order])
    position = np.searchsorted(cumulative, q / 100.0, side="left")
    position = min(position, len(y) - 1)
    return float(y[order][position])


def percentile_ratio(y: np.ndarray, high: float, low: float,
                     weights: np.ndarray | None = None) -> float:
    bottom = weighted_percentile(y, low, weights)
    top = weighted_percentile(y, high, weights)
    if not np.isfinite(bottom) or bottom <= 0:
        return np.nan
    return float(top / bottom)


def _index_row(y: np.ndarray, weights: np.ndarray | None) -> dict[str, float]:
    row = {
        "gini": gini(y, weights),
        "theil_t": theil_t(y, weights),
        "theil_l": theil_l(y, weights),
        "cv": coefficient_of_variation(y, weights),
    }
    for epsilon, label in ATKINSON_EPSILONS.items():
        row[label] = atkinson(y, epsilon, weights)
    for high, low in PERCENTILE_PAIRS:
        row[f"p{high}_p{low}"] = percentile_ratio(y, high, low, weights)
    return {key: round(value, INDEX_DECIMALS) for key, value in row.items()}


def indices(comparable: pd.DataFrame, expected: dict[str, int]) -> pd.DataFrame:
    """One row per indicator, basis, geography, year and weighting.

    Only complete years are measured, for the same reason the dispersion dataset does it:
    an index computed over whichever governorates were printed moves when coverage moves,
    and that artefact is indistinguishable from a trend once it is plotted.
    """
    rows = []
    grouped = comparable.groupby(["indicator", "basis", "geography", "year"], sort=True)
    for (indicator, basis, geography, year), block in grouped:
        if len(block) != expected[geography]:
            continue
        y = block.comparable.to_numpy(dtype=float)
        population = block.population_thousands.to_numpy(dtype=float)
        weighted_ok = np.isfinite(population).all() and population.sum() > 0

        for weighting, weights in (("population", population if weighted_ok else None),
                                   ("unweighted", None)):
            if weighting == "population" and not weighted_ok:
                continue
            rows.append({
                "indicator": indicator,
                "basis": basis,
                "geography": geography,
                "year": int(year),
                "weighting": weighting,
                "period": "post" if year >= REVOLUTION else "pre",
                "governorates": len(block),
                "mean": round(float(y.mean()), INDEX_DECIMALS),
                **_index_row(y, weights),
            })

    frame = pd.DataFrame(rows)
    return frame.sort_values(["indicator", "basis", "geography", "weighting", "year"],
                            ignore_index=True)


def trends(frame: pd.DataFrame, measure: str = "gini",
           min_pre: int = 8, min_post: int = 8) -> pd.DataFrame:
    """Pre- and post-2011 level and slope of one index, per series.

    A slope either side of the cutoff is a description, not an estimate of anything: it
    says the trend changed, not that the revolution changed it. It is here because a
    reader looking at thirty indicators needs a way to find which ones moved.
    """
    rows = []
    keys = ["indicator", "basis", "geography", "weighting"]
    for key, block in frame.groupby(keys, sort=True):
        series = block.set_index("year")[measure].dropna()
        pre = series[series.index < REVOLUTION]
        post = series[series.index >= REVOLUTION]
        if len(pre) < min_pre or len(post) < min_post:
            continue
        pre_slope = float(np.polyfit(pre.index, pre.to_numpy(), 1)[0])
        post_slope = float(np.polyfit(post.index, post.to_numpy(), 1)[0])
        rows.append({
            **dict(zip(keys, key, strict=True)),
            "measure": measure,
            "n_pre": len(pre), "n_post": len(post),
            "pre_level": float(pre.mean()), "post_level": float(post.mean()),
            "pre_slope_decade": pre_slope * 10.0,
            "post_slope_decade": post_slope * 10.0,
            "slope_break_decade": (post_slope - pre_slope) * 10.0,
        })
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return frame.sort_values("slope_break_decade", ignore_index=True)


def build(comparable: pd.DataFrame | None = None) -> pd.DataFrame:
    """The index series for every governorate indicator the corpus can measure."""
    from consumptiontn.build_regional_inequality import (
        CONSTANT_COUNT,
        GOVERNORATE_COUNT,
    )

    if comparable is None:
        comparable = pd.read_csv("data/processed/tn_governorate_comparable.csv")
    expected = {"as_printed": GOVERNORATE_COUNT, "constant": CONSTANT_COUNT}
    frame = indices(comparable, expected)
    if frame.empty:
        raise RuntimeError("no complete indicator-years; has tn_governorate_comparable moved?")
    return frame
