"""Between-governorate dispersion, the analysis-ready form of the governorate panel.

``tn_governorate_panel`` carries counts: schools, teachers, libraries, road deaths, job
offers. A count is not comparable across governorates -- Tunis has roughly nine times
Tozeur's people, so ranking governorates on a count mostly ranks them by population -- and
a *dispersion* of counts is worse, because it moves when the population distribution moves.
This module produces the two normalisations that are defensible, and the dispersion of
each.

**Two bases, because they trade off against each other.**

* ``per_head`` divides by population. It is the quantity anyone actually means by
  provision, and it is the one to report. It exists only from 2005, because no yearbook in
  the corpus prints population by governorate earlier, which leaves **six pre-2011 years**.
* ``share_of_national`` is a governorate's share of the national total. It needs no
  denominator, so it runs the full span of each series. It is not a welfare quantity: a
  governorate's share reflects its size. But a *change* in share is redistribution, which
  is the question, and population shares move slowly enough that the two bases can be read
  against each other.

Crossed with the two geographies below, ``share_of_national`` on the constant geography is
what reaches **sixteen pre-2011 years** -- marriages, job offers, job placements and three
library series -- against six on ``per_head``. On the as-printed geography the same basis
stops at 2000, because Manouba does not exist before then and a complete year needs every
unit present. The long pre-period is a product of both choices, not of the basis alone.

Reporting both is the point. Where they agree, the finding does not rest on the
denominator; where they disagree, the disagreement is the finding.

**Two geographies, because the map changed.** ``as_printed`` is the 24 governorates as
INS prints them. ``constant`` adds Manouba back into Ariana -- summing the count *and* the
population, so the pair is one fixed area whatever the boundary did inside it -- giving 23
units on a single geography from 1994. That is the difference between asserting parallel
trends and testing them, so both are built and the analysis can show the finding holds on
either.

**The trap this module exists to avoid.** A dispersion measure computed over whatever
governorates happen to be present moves when *coverage* moves. Kasserine dropping out of
one edition would register as inequality falling. So a dispersion value is produced only
for a year observed in every unit its geography expects -- 24 or 23 -- and the count is
carried on every row so a reader can check rather than trust. Incomplete years keep their
row and lose only their dispersion columns, so what is excluded stays visible.

**Weighted, not unweighted.** Unweighted dispersion across governorates treats Tozeur and
Tunis as one observation each, which answers a question about administrative units rather
than about people. The population-weighted figures are primary. The unweighted ones are
carried beside them because the choice changes the answer and should be visible: a reader
who wants the unit-level question has it, and one who does not can see what it would have
said.

**Three exposure variables**, for the differential design the data can support. The
revolution is simultaneous and national, so there is no untreated governorate and no
average effect to recover; what is identified is how governorates differing in
pre-determined characteristics diverged afterwards. Two of the three are INS's own or the
data's own, and only one is a coding choice of mine:

* ``region`` -- the seven grandes régions, INS's grouping, not an invention of this repo.
* ``baseline`` -- the governorate's own mean per head over 2005-2010, entirely
  pre-revolution. Data-driven, so it requires no geographic judgement at all, and it is
  what a convergence test needs.
* ``littoral`` -- the coastal/interior split. This one **is** a coding decision, spelled
  out in ``LITTORAL`` below rather than buried, because it is contestable and someone may
  well want to revise it. Zaghouan and Manouba are the awkward cases.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# The denominator itself. Population per head is 1, which is not an outcome.
DENOMINATOR = "population"

# Nominal dinars. Comparing 2003 with 2023 without deflating measures the currency, so
# this one is carried to constant 2015 dinars before anything else happens to it.
NOMINAL = {"money_orders_from_abroad"}
DEFLATOR_BASE = 2015

# A coding choice, and the only one here. The standard Tunisian littoral/interior divide,
# written out so it can be argued with. Manouba is inland but administratively Grand Tunis
# and is counted coastal with it; Zaghouan is inland despite its Nord-Est grouping.
LITTORAL = frozenset({
    "Tunis", "Ariana", "Ben Arous", "Manouba", "Nabeul", "Bizerte",
    "Sousse", "Monastir", "Mahdia", "Sfax", "Gabès", "Médenine",
})

# `theil_weighted` is computed through a logarithm, and `np.log` is not required by IEEE
# 754 to be correctly rounded, so two libm versions can disagree in the last bit and fail
# the byte-for-byte build gate. Ordinary arithmetic is safe -- the standard does require
# correctly-rounded +, -, * and / -- so only the log-derived column needs this, but the
# whole row is rounded together so no reader has to know which is which.
#
# This is the same defect that reached CI twice: once as `atkinson_1` in the inequality
# indices and once as `log_value` in the monthly series. Here it had not yet fired, which
# is luck rather than safety.
MEASURE_DECIMALS = 6

# The panel is complete at 24 from 2002; a dispersion value needs all of them.
GOVERNORATE_COUNT = 24

# Manouba was created in 2000 out of Ariana, so a 24-unit series cannot reach earlier than
# that however the arithmetic is arranged -- requiring all 24 caps the pre-revolution window
# at eleven years. Adding the two back together gives 23 units on one geography for the
# full 1995-2023, which is sixteen pre-revolution years instead. That is the difference
# between asserting parallel trends and testing them, so both geographies are built.
SPLIT_PARENT, SPLIT_CHILD = "Ariana", "Manouba"
CONSTANT_COUNT = GOVERNORATE_COUNT - 1

# Wholly pre-revolution, and the years for which a denominator exists.
BASELINE_YEARS = (2005, 2010)
REVOLUTION = 2011

# Theil is a log measure and a governorate with none of something has an undefined one.
# The zero is real -- Tozeur genuinely has no cinema screens in some years -- so the row
# survives and only that column is empty.
ZERO_FLOOR = 0.0


def _deflator(cpi: pd.DataFrame) -> pd.Series:
    """Year -> price index on base 2015 = 100, from the eight bases INS prints."""
    base = cpi[cpi.base_year.eq(DEFLATOR_BASE)]
    if base.empty:
        raise RuntimeError(f"tn_cpi_annual carries no base {DEFLATOR_BASE}")
    index = base.set_index("year")["index"]
    if not np.isclose(index.loc[DEFLATOR_BASE], 100.0):
        raise RuntimeError(f"base {DEFLATOR_BASE} does not read 100 in its own year")
    return index


def real_values(panel: pd.DataFrame, cpi: pd.DataFrame) -> pd.DataFrame:
    """Carry the nominal series to constant dinars, leaving counts alone."""
    frame = panel.copy()
    index = _deflator(cpi)
    nominal = frame.indicator.isin(NOMINAL)
    if not nominal.any():
        return frame

    missing = set(frame.loc[nominal, "year"]) - set(index.index)
    if missing:
        raise RuntimeError(f"no {DEFLATOR_BASE}-base CPI for {sorted(missing)}")
    factor = frame.loc[nominal, "year"].map(index) / 100.0
    frame.loc[nominal, "value"] = frame.loc[nominal, "value"] / factor
    frame.loc[nominal, "unit"] = f"dinars, constant {DEFLATOR_BASE}"
    return frame


def constant_geography(panel: pd.DataFrame) -> pd.DataFrame:
    """Ariana absorbing Manouba, so one geography spans 1995-2023.

    Both the count and the population are summed, which is the whole point: the pair is a
    fixed area whatever the boundary did inside it. Years where only the parent is present
    -- everything before 2000 -- pass through unchanged and are already on this geography.
    """
    frame = panel.copy()
    frame["governorate"] = frame.governorate.replace({SPLIT_CHILD: SPLIT_PARENT})
    keys = ["governorate", "year", "indicator", "unit"]
    # A population that is missing on either side must not be summed to a half-total, so
    # min_count keeps it absent rather than quietly reading as the parent's alone.
    agg = frame.groupby(keys, as_index=False).agg(
        value=("value", "sum"),
        population_thousands=("population_thousands", lambda s: s.sum(min_count=len(s))),
    )
    return agg


def normalise(panel: pd.DataFrame) -> pd.DataFrame:
    """One row per governorate, year, indicator and basis, with the comparable value."""
    frame = panel[panel.indicator.ne(DENOMINATOR)].copy()

    per_head = frame[frame.population_thousands.notna()].copy()
    per_head["basis"] = "per_head"
    # Population is in thousands, so this is already per 1,000 people.
    per_head["comparable"] = per_head.value / per_head.population_thousands

    share = frame.copy()
    total = share.groupby(["indicator", "year"]).value.transform("sum")
    share["basis"] = "share_of_national"
    # A year whose national total is zero carries no shares rather than dividing by it.
    share["comparable"] = np.where(total > 0, share.value / total, np.nan)
    share = share[share.comparable.notna()]

    keep = ["governorate", "year", "indicator", "unit", "basis", "value",
            "population_thousands", "comparable"]
    return pd.concat([per_head[keep], share[keep]], ignore_index=True)


def comparable_panel(plain: pd.DataFrame) -> pd.DataFrame:
    """Both normalisations on both geographies, in one long frame."""
    parts = []
    for name, frame in (("as_printed", plain),
                        ("constant", constant_geography(plain))):
        block = normalise(frame)
        block["geography"] = name
        parts.append(block)
    return pd.concat(parts, ignore_index=True)


def _weighted_theil(y: np.ndarray, w: np.ndarray) -> float:
    """Population-weighted Theil-T. Undefined if any governorate has none of it."""
    if (y <= ZERO_FLOOR).any():
        return np.nan
    share = w / w.sum()
    mean = float((share * y).sum())
    if mean <= 0:
        return np.nan
    ratio = y / mean
    return float((share * ratio * np.log(ratio)).sum())


def _weighted_cv(y: np.ndarray, w: np.ndarray) -> float:
    share = w / w.sum()
    mean = float((share * y).sum())
    if mean <= 0:
        return np.nan
    variance = float((share * (y - mean) ** 2).sum())
    return float(np.sqrt(variance) / mean)


def _tail_ratio(y: np.ndarray, k: int = 3) -> float:
    """Mean of the top k over the mean of the bottom k. No distributional assumption."""
    ordered = np.sort(y)
    bottom = ordered[:k].mean()
    if bottom <= 0:
        return np.nan
    return float(ordered[-k:].mean() / bottom)


def dispersion(normalised: pd.DataFrame) -> pd.DataFrame:
    """Between-governorate dispersion per indicator, year and basis.

    Only complete years get a value. A measure computed over whichever governorates
    happened to be printed would move with coverage rather than with inequality, and that
    artefact is indistinguishable from the finding once it is in a chart.
    """
    rows = []
    expected = {"as_printed": GOVERNORATE_COUNT, "constant": CONSTANT_COUNT}
    grouped = normalised.groupby(["indicator", "basis", "geography", "year"], sort=True)
    for (indicator, basis, geography, year), block in grouped:
        weights = block.population_thousands.to_numpy(dtype=float)
        weighted = np.isfinite(weights).all() and weights.sum() > 0
        y = block.comparable.to_numpy(dtype=float)
        rows.append({
            "indicator": indicator,
            "basis": basis,
            "geography": geography,
            "year": int(year),
            "governorates": len(block),
            "complete": len(block) == expected[geography],
            "period": "post" if year >= REVOLUTION else "pre",
            "mean": float(y.mean()),
            "theil_weighted": _weighted_theil(y, weights) if weighted else np.nan,
            "cv_weighted": _weighted_cv(y, weights) if weighted else np.nan,
            "cv_unweighted": float(y.std(ddof=0) / y.mean()) if y.mean() > 0 else np.nan,
            "tail_ratio": _tail_ratio(y),
        })

    frame = pd.DataFrame(rows)
    # Published, not silently dropped: an incomplete year is a page worth re-reading, and
    # a reader filtering on `complete` should be able to see what they are excluding.
    measures = ["mean", "theil_weighted", "cv_weighted", "cv_unweighted", "tail_ratio"]
    for column in measures[1:]:
        frame.loc[~frame.complete, column] = np.nan
    frame[measures] = frame[measures].round(MEASURE_DECIMALS)
    return frame.sort_values(["indicator", "basis", "geography", "year"],
                             ignore_index=True)


def exposure(normalised: pd.DataFrame, regions: dict[str, tuple[str, ...]]) -> pd.DataFrame:
    """The pre-determined governorate characteristics a differential design needs."""
    lookup = {gov: region for region, govs in regions.items() for gov in govs}

    lo, hi = BASELINE_YEARS
    pre = normalised[normalised.basis.eq("per_head")
                     & normalised.geography.eq("as_printed")
                     & normalised.year.between(lo, hi)]
    baseline = (pre.groupby(["indicator", "governorate"]).comparable.mean()
                .rename("baseline_per_head").reset_index())

    baseline["region"] = baseline.governorate.map(lookup)
    if baseline.region.isna().any():
        unmapped = sorted(set(baseline.loc[baseline.region.isna(), "governorate"]))
        raise RuntimeError(f"governorates outside the seven regions: {unmapped}")
    baseline["littoral"] = baseline.governorate.isin(LITTORAL)
    # Within each indicator, where does this governorate start? A convergence test needs
    # the rank, not just the level, because the levels are in different units per series.
    baseline["baseline_rank"] = (baseline.groupby("indicator").baseline_per_head
                                .rank(method="min", ascending=False).astype(int))
    return baseline.sort_values(["indicator", "baseline_rank"], ignore_index=True)


def build(panel: pd.DataFrame | None = None,
          cpi: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """The comparable panel, its dispersion, and the pre-revolution exposure variables."""
    from consumptiontn.build_yearbook import GRANDES_REGIONS

    if panel is None:
        panel = pd.read_csv("data/processed/tn_governorate_panel.csv",
                            dtype={"breakdown": "string", "boundary": "string"})
    if cpi is None:
        cpi = pd.read_csv("data/processed/tn_cpi_annual.csv")

    panel = panel.copy()
    panel["breakdown"] = panel.breakdown.fillna("")
    # Population by age carries a breakdown and is a different shape; the thirty plain
    # governorate-by-year series are what this module normalises.
    plain = panel[panel.breakdown.eq("")]
    if plain.empty:
        raise RuntimeError("no breakdown-free rows in tn_governorate_panel")

    comparable = comparable_panel(real_values(plain, cpi))
    return comparable, dispersion(comparable), exposure(comparable, GRANDES_REGIONS)
