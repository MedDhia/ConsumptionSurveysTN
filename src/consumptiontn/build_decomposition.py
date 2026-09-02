"""Regional inequality at two geographies, and the structure underneath it.

The question this repository kept trying to answer with a discontinuity is better asked
descriptively, because the annual data cannot support the discontinuity and can support
this. Three things, in order of how much they say:

**The same inequality measured at two geographies.** The 24 governorates nest inside INS's
seven grandes régions, so every indicator has a Gini across governorates and a Gini across
regions. The second is nearly always smaller -- aggregating hides the dispersion inside
each region -- and how much smaller is itself the finding: a service whose two Ginis are
close is one whose inequality is *between* regions, and a service where they diverge is one
where the gap is inside them. Across the corpus the region figure runs at a median 77% of
the governorate figure.

"Nearly", because it is not a theorem and four indicator-years out of 533 go the other way.
Each region counts once here and the regions hold three or four governorates rather than
the same number, so a region's total carries its size as well as its provision, and the
aggregation is a mean-preserving contraction only when the groups are equal. These are
close to equal, which is why the exceptions are few and small, and not equal, which is why
they exist.

**A pre and post comparison rather than a discontinuity.** Means either side of 2011, which
is what the data will carry. This is a difference between two periods, not an effect: 2011
is one of several things that happened between 2000 and 2023, and the figures say so.
``pre_post`` also reports what a line fitted to the pre-2011 years alone would have
predicted, because that turns out to be most of it.

**The decomposition, which is the structural part.** Theil is additively decomposable, so
``theil_governorate`` splits exactly into a between-region component and a within-region
one:

    T = Σ_g (n_g/n)(μ_g/μ) ln(μ_g/μ)  +  Σ_g (n_g/n)(μ_g/μ) T_g

The identity holds here to 2e-16, which is the check that the arithmetic is right rather
than merely plausible. What it buys is the question the Tunisian literature actually asks:
the coastal/interior divide is a *between-region* story, so if the revolution changed
anything structural it should show up as a shift in the between share.

It shifts, and the shift is not the revolution's. The between-region share of secondary
schooling rises 0.152 across 2011, the largest structural move in the corpus -- and it had
been rising 0.150 per decade since 2000, straight through the cutoff, with no visible
break. For eight of the sixteen services with a long enough window, and seven of the ten
outside the noisy library family, the pre-2011 trend alone predicts at least as much
movement as actually occurred. That is why ``pre_post`` carries ``predicted`` and
``excess`` beside ``change``: read alone, ``change`` dates to the revolution things that
were already happening.

**Unweighted, and that is a choice with a reason.** Population weights need a governorate
population, which the corpus does not print before 2005, and a decomposition that starts in
2005 has three pre-revolution years. Each governorate counts once here, so this is
inequality across administrative units rather than across Tunisians.
``tn_governorate_inequality`` carries the population-weighted index family from 2005 for
anyone who needs the other question answered; nothing here is weighted.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

REVOLUTION = 2011
GOVERNORATE_COUNT = 24

# Same rounding rule as the other index modules: these go through a logarithm, and `np.log`
# is not correctly rounded by IEEE 754, so the last bits are not portable across machines.
DECIMALS = 6

# A pre-period mean over one or two printed years is not a period mean, and a trend fitted
# to it is worse. `bank_branches` has a single pre-revolution year in this frame, which
# would otherwise report a "pre-revolution level" from 2010 alone.
MIN_PRE, MIN_POST = 7, 8


def fit_line(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Least-squares line through (x, y), in closed form rather than through LAPACK.

    ``np.polyfit`` would be the obvious call and is the wrong one here. It solves a
    least-squares system through LAPACK, which IEEE 754 says nothing about: the result
    depends on the BLAS the machine was built against, and the last bits move. That is
    invisible until a value lands on a rounding boundary, and one here does --
    ``fixed_line_subscribers`` predicts exactly 0.0322415, a perfect tie at six decimals,
    which two machines rounded in opposite directions and the pipeline's byte-for-byte
    check caught.

    The closed form for a degree-1 fit uses only addition, subtraction, multiplication and
    division, which IEEE 754 *does* require to be correctly rounded. Given identical
    inputs -- and the inputs here are already rounded to six decimals before they reach
    this function -- every machine now computes the same float and rounds it the same way.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    x_mean, y_mean = float(x.mean()), float(y.mean())
    dx = x - x_mean
    denominator = float((dx * dx).sum())
    if denominator == 0:
        return 0.0, y_mean
    slope = float((dx * (y - y_mean)).sum()) / denominator
    return slope, y_mean - slope * x_mean


def _theil(y: np.ndarray, weights: np.ndarray | None = None) -> float:
    """Theil-T. Undefined where any unit reports none of the thing."""
    y = np.asarray(y, dtype=float)
    if len(y) < 2 or (y <= 0).any() or not np.isfinite(y).all():
        return np.nan
    share = (np.full(len(y), 1.0 / len(y)) if weights is None
             else np.asarray(weights, float) / np.sum(weights))
    mean = float((share * y).sum())
    if mean <= 0:
        return np.nan
    ratio = y / mean
    return float((share * ratio * np.log(ratio)).sum())


def _gini(y: np.ndarray) -> float:
    y = np.asarray(y, dtype=float)
    if len(y) < 2 or not np.isfinite(y).all():
        return np.nan
    mean = float(y.mean())
    if mean <= 0:
        return np.nan
    return float(np.abs(y[:, None] - y[None, :]).sum() / (2 * len(y) ** 2 * mean))


def decompose(block: pd.DataFrame) -> dict | None:
    """Split one indicator-year's Theil into its between- and within-region parts."""
    y = block.comparable.to_numpy(dtype=float)
    if len(y) != GOVERNORATE_COUNT or (y <= 0).any() or not np.isfinite(y).all():
        return None
    total = _theil(y)
    if not np.isfinite(total):
        return None

    mean = float(y.mean())
    between = within = 0.0
    for _, group in block.groupby("region"):
        values = group.comparable.to_numpy(dtype=float)
        weight = len(values) / len(y)
        relative = float(values.mean()) / mean
        between += weight * relative * np.log(relative)
        inner = _theil(values)
        within += weight * relative * (0.0 if np.isnan(inner) else inner)
    # `total` is not returned: it is `theil_governorate`, computed identically by the
    # caller, and shipping the same number under two names invites a reader to check one
    # against the other and learn nothing.
    return {"theil_between": between, "theil_within": within,
            "identity_gap": abs(between + within - total)}


def build(comparable: pd.DataFrame | None = None,
          regions: dict[str, tuple[str, ...]] | None = None) -> pd.DataFrame:
    """One row per indicator and year: both geographies, and the decomposition."""
    from consumptiontn.build_yearbook import GRANDES_REGIONS

    if comparable is None:
        comparable = pd.read_csv("data/processed/tn_governorate_comparable.csv")
    regions = regions or GRANDES_REGIONS
    lookup = {gov: region for region, govs in regions.items() for gov in govs}

    frame = comparable[comparable.basis.eq("share_of_national")
                       & comparable.geography.eq("as_printed")].copy()
    frame["region"] = frame.governorate.map(lookup)
    if frame.region.isna().any():
        missing = sorted(set(frame.loc[frame.region.isna(), "governorate"]))
        raise RuntimeError(f"governorates outside the seven regions: {missing}")

    rows = []
    for (indicator, year), block in frame.groupby(["indicator", "year"], sort=True):
        if len(block) != GOVERNORATE_COUNT:
            continue
        governorate = block.comparable.to_numpy(dtype=float)
        # The region-level series is the same quantity aggregated: each region's share of
        # the national total is the sum of its governorates' shares.
        region = block.groupby("region").comparable.sum().to_numpy(dtype=float)
        row = {
            "indicator": indicator, "year": int(year),
            "period": "post" if year >= REVOLUTION else "pre",
            "gini_governorate": _gini(governorate),
            "gini_region": _gini(region),
            "theil_governorate": _theil(governorate),
            "theil_region": _theil(region),
        }
        parts = decompose(block)
        if parts is not None:
            row.update(parts)
            row["between_share"] = (parts["theil_between"] / row["theil_governorate"]
                                    if row["theil_governorate"] > 0 else np.nan)
        rows.append(row)

    result = pd.DataFrame(rows)
    if result.empty:
        raise RuntimeError("no indicator-year could be decomposed")
    # The identity is the check that the arithmetic is right rather than merely plausible.
    # `.max()` over an all-NaN column is NaN, and `NaN > 1e-9` is False, so the check would
    # pass by saying nothing if nothing decomposed. Require that something did.
    if not result.identity_gap.notna().any():
        raise RuntimeError("no indicator-year decomposed; the identity was never tested")
    worst = result.identity_gap.max()
    if worst > 1e-9:
        raise RuntimeError(f"Theil decomposition does not add up; worst gap {worst:g}")

    numeric = [c for c in result.columns if result[c].dtype.kind == "f"]
    result[numeric] = result[numeric].round(DECIMALS)
    return result.sort_values(["indicator", "year"], ignore_index=True)


def pre_post(frame: pd.DataFrame, column: str, *,
             min_pre: int = MIN_PRE, min_post: int = MIN_POST) -> pd.DataFrame:
    """Means either side of the revolution, and what the pre-2011 trend already predicted.

    ``change`` is the raw difference between the two period means. ``predicted`` is the
    difference a line fitted to the pre-revolution years alone, extrapolated over the
    post-revolution years, would have produced on its own -- and ``excess`` is what is left
    when that is taken out.

    The distinction is the whole reason this table is worth building. Several indicators
    show a large post-2011 shift that a decade of pre-2011 drift already accounts for:
    the between-region share of secondary schooling rises 0.15 across the cutoff, and it
    was rising at 0.15 per decade from 2000 with no visible break at 2011. Reading
    ``change`` alone dates that to the revolution. ``excess`` says how much of it needs
    the revolution to explain.

    Neither column is a causal estimate -- a fitted pre-trend is not a counterfactual, and
    nothing here rules out the trend itself having turned for reasons of its own.

    Indicators with short windows are dropped rather than shown, because a "pre-period
    mean" over one or two printed years is not a period mean, and a trend fitted to it is
    worse.
    """
    rows = []
    for indicator, block in frame.dropna(subset=[column]).groupby("indicator", sort=True):
        pre = block[block.period.eq("pre")]
        post = block[block.period.eq("post")]
        if len(pre) < min_pre or len(post) < min_post:
            continue
        slope, intercept = fit_line(pre.year.to_numpy(dtype=float),
                                    pre[column].to_numpy(dtype=float))
        pre_mean = float(pre[column].mean())
        post_mean = float(post[column].mean())
        # The mean of a straight line over a set of points is the line evaluated at their
        # mean, so this is two operations rather than a summation over the post years.
        trend_mean = slope * float(post.year.mean()) + intercept
        rows.append({
            "indicator": indicator, "measure": column,
            "n_pre": len(pre), "n_post": len(post),
            "first_year": int(block.year.min()), "last_year": int(block.year.max()),
            "pre": pre_mean, "post": post_mean,
            "change": post_mean - pre_mean,
            "pre_trend_per_decade": float(slope) * 10,
            "predicted": trend_mean - pre_mean,
            "excess": (post_mean - pre_mean) - (trend_mean - pre_mean),
        })
    table = pd.DataFrame(rows)
    if table.empty:
        return table
    numeric = [c for c in table.columns if table[c].dtype.kind == "f"]
    table[numeric] = table[numeric].round(DECIMALS)
    return table.sort_values("change", ignore_index=True)


MEASURES = ("gini_governorate", "gini_region", "theil_governorate", "theil_region",
            "theil_between", "theil_within", "between_share")


def summary(frame: pd.DataFrame) -> pd.DataFrame:
    """The pre/post table for every measure at once, stacked long."""
    parts = [pre_post(frame, measure) for measure in MEASURES]
    parts = [part for part in parts if not part.empty]
    if not parts:
        raise RuntimeError("no measure had an indicator with a long enough window")
    return pd.concat(parts, ignore_index=True).sort_values(
        ["measure", "change"], ignore_index=True)
