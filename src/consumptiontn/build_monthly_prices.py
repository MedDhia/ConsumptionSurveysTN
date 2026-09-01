"""Monthly price indices, the outcome least contaminated by the tourism collapse.

The monthly series already extracted are counts -- arrivals, road casualties, money orders
-- and the strongest of them, tourism, is compromised twice over: INS did not print the
2011 peak season, and a tourist arrival responds to the Bardo and Sousse attacks and the
Libyan war as much as to the uprising. Prices are the channel where that is least true, and
they are also the one the uprising was about: Bouazizi was a fruit seller, and food prices
were the grievance under the grievance.

Two indices come out of the corpus at monthly frequency.

**The consumer price index**, table 13.6, headline ``Indice d'ensemble`` only. It is printed
one page per year with the months down the side and the product groups across, and the
corpus fuses the year into each column heading, so the general index is picked out by name
rather than by position. 2002 to 2012.

**The industrial selling price index**, table 13.2/13.3, eight sectors. 1998 to 2023.

**Neither is chained, and the reason is measured rather than assumed.** Both were rebased
during the period -- the CPI from 2000=100 to 2005=100, the IPI from 2000=100 to 2010=100 --
and the repository already knows how to chain across a rebasing when the two bases overlap
(see ``build_prices.chained_divisions``). Here that would be wrong. The IPI tables overlap
in 2010-2012, and the ratio between them is not constant within a sector: chemicals runs
from 0.607 to 0.774 across thirty-six months, a 27% spread, where a pure rebasing would give
one number. INS re-weighted the basket as well as moving the base, so no single factor
carries one series onto the other and the two are published as what they are.

That costs nothing for the design this feeds. **A regression discontinuity at January 2011
does not need a chain**, because one base spans the cutoff on each index: CPI base 2005
covers 2009-2012, twenty-four months either side, and IPI base 2000 covers 1998-2012, one
hundred and fifty-six months before and twenty-four after. Running the estimate separately
on each base is better than running it once on a spliced series, because the two are then
independent measurements of the same discontinuity.

**The base is verified, not read off a label and trusted.** Where a column heading states
one it is used; the assignment is then checked against ``tn_cpi_annual``, which was built
from a different table and verified separately -- the twelve months of a year have to average
to the annual index printed for that base. They do, to between 0.01 and 0.37 index points on
values around 120, which is under three tenths of a percent. A year that fails is refused
rather than shipped, because a monthly series on the wrong base would slot into an RD
perfectly well and be wrong.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from consumptiontn.build_monthly import MONTH_NUMBER, MONTHS, VALUE_DECIMALS

CUTOFF_YEAR, CUTOFF_MONTH = 2011, 1

# Table 13.6 across the editions that print it. The headline column is picked out by name
# because the corpus fuses the year into every column heading on this table.
CPI_TITLES = (
    "indice général des prix à la consommation 6",
    "indice general des prix 6",
)
CPI_GENERAL = "ensemble"

# Table 13.2/13.3, one row per sector and month. The sector names differ by a comma or a
# full stop between editions -- "Textiles, habillement" against "Textiles. habillement" --
# which would otherwise split one sector into two series.
IPI_TITLES = {
    "evolution mensuelle 3": 2000,
    "evolution mensuelle de l indice des prix de vente industriels 2": 2010,
}

# The monthly mean has to reproduce the annual index printed for the same base. Three
# tenths of a percent is loose enough for a table of one-decimal figures and tight enough
# to catch a year assigned to the wrong base, which would be out by tens of percent.
ANNUAL_TOLERANCE = 0.005


def _normalise_sector(label: pd.Series) -> pd.Series:
    return label.str.replace(".", ",", regex=False).str.strip()


def consumer_prices(series: pd.DataFrame) -> pd.DataFrame:
    """Headline CPI by month, with the base year each figure is expressed on."""
    rows = series[series.title_fr.isin(CPI_TITLES) & series.row_label.isin(MONTHS)
                  & series.row_kind.eq("data")].copy()
    label = rows.column_label.astype("string").fillna("")
    rows = rows[label.str.contains(CPI_GENERAL, case=False, regex=False)]
    if rows.empty:
        raise RuntimeError("no headline CPI column found; has table 13.6 moved?")

    rows["base_year"] = (rows.column_label.astype("string")
                         .str.extract(r"Base\s*\((\d{4})\s*=\s*100\)")[0])
    # Editions overlap and a base is not always restated in the heading. A year whose base
    # is stated anywhere is taken to be on that base throughout -- and the annual check
    # below is what makes that safe rather than merely convenient.
    stated = rows.dropna(subset=["base_year"]).groupby("year").base_year.agg(
        lambda s: s.mode().iat[0])
    rows["base_year"] = rows.year.map(stated)
    rows = rows.dropna(subset=["base_year"])
    rows["base_year"] = rows.base_year.astype(int)

    flat = rows.groupby(["base_year", "year", "row_label"], as_index=False).value.mean()
    flat["month"] = flat.row_label.map(MONTH_NUMBER)
    flat["series"] = "cpi_general"
    flat["group"] = "all items"
    return flat.drop(columns="row_label")


def industrial_prices(series: pd.DataFrame) -> pd.DataFrame:
    """Industrial selling price index by sector and month, on each printed base."""
    frames = []
    for title, base in IPI_TITLES.items():
        rows = series[series.title_fr.eq(title) & series.row_kind.eq("data")].copy()
        parts = rows.row_label.str.rsplit(" / ", n=1)
        rows["group"] = _normalise_sector(parts.str[0])
        rows["month_name"] = parts.str[-1]
        rows = rows[rows.month_name.isin(MONTHS)]
        if rows.empty:
            raise RuntimeError(f"no monthly rows for {title!r}")
        flat = rows.groupby(["group", "year", "month_name"], as_index=False).value.mean()
        flat["month"] = flat.month_name.map(MONTH_NUMBER)
        flat["base_year"] = base
        flat["series"] = "industrial_prices"
        frames.append(flat.drop(columns="month_name"))
    return pd.concat(frames, ignore_index=True)


def against_annual(cpi: pd.DataFrame, annual: pd.DataFrame) -> pd.DataFrame:
    """The twelve months of a year against the annual index printed for the same base.

    ``tn_cpi_annual`` comes from a different table and was verified on its own, so this is
    an outside check rather than the series agreeing with itself.
    """
    monthly = (cpi.groupby(["base_year", "year"])
               .value.agg(monthly_mean="mean", months="size").reset_index())
    printed = annual.rename(columns={"index": "printed"})[["base_year", "year", "printed"]]
    check = monthly.merge(printed, on=["base_year", "year"], how="left")
    gap = (check.monthly_mean - check.printed).abs()
    check["gap"] = gap
    check["agrees"] = check.printed.notna() & check.months.eq(len(MONTHS)) & (
        gap <= check.printed.abs() * ANNUAL_TOLERANCE)
    check["check"] = "the twelve months average to the printed annual index"
    return check


def rebasing_factors(ipi: pd.DataFrame) -> pd.DataFrame:
    """The ratio between the two IPI bases where they overlap, month by month.

    Published because it is the evidence for *not* chaining. A pure rebasing would give one
    constant per sector; these vary, so the basket changed too.
    """
    wide = ipi.pivot_table(index=["group", "year", "month"], columns="base_year",
                           values="value").dropna()
    if wide.empty or len(wide.columns) < 2:
        return pd.DataFrame(columns=["group", "year", "month", "ratio"])
    old, new = sorted(wide.columns)
    out = wide.reset_index()[["group", "year", "month"]]
    out["old_base"], out["new_base"] = old, new
    out["ratio"] = (wide[new] / wide[old]).to_numpy()
    return out


def build(series: pd.DataFrame | None = None,
          annual: pd.DataFrame | None = None
          ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Monthly prices, the checks behind them, and the measured rebasing factors."""
    if series is None:
        series = pd.read_csv("data/processed/tn_yearbook_series.csv",
                             dtype={"panel": "string"})
    if annual is None:
        annual = pd.read_csv("data/processed/tn_cpi_annual.csv")

    cpi = consumer_prices(series)
    ipi = industrial_prices(series)
    check = against_annual(cpi, annual)

    # A year whose months do not average to the annual index printed for its base is on the
    # wrong base or misread, and either way it would sit in an RD looking perfectly normal.
    refused = check[~check.agrees]
    bad = set(zip(refused.base_year, refused.year, strict=True))
    keep = pd.Series([pair not in bad for pair in zip(cpi.base_year, cpi.year, strict=True)],
                     index=cpi.index)
    cpi = cpi[keep]

    frame = pd.concat([cpi, ipi], ignore_index=True)
    frame["t"] = (frame.year + (frame.month - 1) / 12.0).round(VALUE_DECIMALS)
    frame["running"] = ((frame.year - CUTOFF_YEAR) * 12
                        + (frame.month - CUTOFF_MONTH)).astype(int)
    frame["treated"] = frame.running >= 0
    # An index is a level, so the log is what makes a jump read as a proportional change.
    # Rounded because `np.log` is not correctly rounded by IEEE 754 and the last bit is not
    # portable -- the same rule as `build_monthly.log_value`.
    frame["log_value"] = np.where(frame.value > 0,
                                  np.log(frame.value).round(VALUE_DECIMALS), np.nan)

    columns = ["series", "group", "base_year", "year", "month", "t", "running", "treated",
               "value", "log_value"]
    frame = frame[columns].sort_values(["series", "group", "base_year", "running"],
                                       ignore_index=True)
    return frame, check, rebasing_factors(ipi)
