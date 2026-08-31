"""Monthly national series, the only frequency at which this corpus can support an RDD.

Regression discontinuity in time leans on shrinking the bandwidth toward the cutoff. With
annual data there is nothing to shrink -- a five-year window holds five points either side
and the estimate is whatever the assumed polynomial does over a decade. With monthly data
a six-month window holds six, and the honest bias bound in ``rdit`` stays interpretable.
The corpus turns out to carry seven such series spanning January 2011, and this module is
what gets them out.

**Every series here is verified twice before it is published**, because a monthly series
that is silently the wrong table would produce a confident causal estimate about the wrong
thing:

* *Against the printed total.* Most of these tables print the twelve months and then a
  ``Total`` beside them, so the twelve have to sum to it. 82 year-panels can be checked
  that way and all 82 agree. The coverage is uneven and the dataset says so rather than
  implying otherwise: road injuries are checked in 29 years of 29, money orders in 20,
  tourist arrivals in only 5 of 26, and tourist departures in none, because no edition
  prints a total beside them.
* *Against their own components.* The tourist tables are printed once for all modes and
  again split by air, land and sea, so the three have to come to the combined figure. That
  is the only arithmetic check departures has, and it is what keeps them in.
* *Against the world, where the world knows.* Non-resident entries come to 6,903 thousand
  in 2010, against a published figure of roughly 6.9 million.

**One candidate was rejected on the first check, and it matters that it was.** The corpus
carries rows labelled with the twelve months under
``evolution du nombre des demandes d emploi par gouvernorat enregistrées``, which reads
like a monthly series of job applications -- the single most revolution-relevant outcome in
the yearbooks, unemployment having been the proximate grievance of the uprising. It is
not one. Table 6.1.6 is by governorate and prints no monthly panel; the rows sum to about
5,800 a year against the 391,927 that table 6.1.5 prints for 2023, a factor of 67. Where
they come from is not settled here. They are excluded and named in the refusals, because
an RDiT run on them would have produced a clean, publishable, wrong result about the
Tunisian labour market.

**INS did not publish the 2011 peak season for tourism, and that is a fact about the
treatment rather than about the parser.** The 2015 edition is the only one printing monthly
2011 arrivals, and against May, June, July, August, September and December it prints an
ellipsis -- ``…`` -- where a number would go. Six of the twelve months are simply absent
from the source, and they are the summer peak immediately after the uprising: precisely the
months in which any effect would be largest. So the missingness is correlated with the
treatment, which is the one kind that cannot be assumed away.

The consequence is that ``tourist_entries`` and ``tourist_departures`` support a much
weaker design than their sample size suggests, and a discontinuity estimated on them is
computed from the months INS chose to print. ``published_share`` carries the fraction of
each year that is actually printed so this cannot be missed downstream. The road and money
series are complete through 2011 -- twelve months each -- and are the outcomes on which
the estimates here can be read straight.

**The running variable is months from January 2011**, matching ``rdit.CUTOFF``. January
2011 itself is month zero and counts as treated: Ben Ali left on the 14th, so the month
straddles the event, which is what ``donut=1`` in the estimation is for.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

MONTHS = ("Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
          "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre")
MONTH_NUMBER = {name: i + 1 for i, name in enumerate(MONTHS)}

CUTOFF_YEAR, CUTOFF_MONTH = 2011, 1

# Canonical name -> the corpus titles carrying it, its unit, and what it counts. Titles
# are truncated and merged differently across editions, so several map to one series; each
# was read off the printed page rather than guessed from the string.
SERIES = {
    "tourist_entries": (
        ("entrées des voyageurs non résidents par nationalité et par mois 2",),
        "thousands", "Non-resident arrivals, all transport modes (table 10.2)"),
    "tourist_departures": (
        ("sorties des voyageurs non résidents par nationalité et par mois 7",),
        "thousands", "Non-resident departures, all transport modes"),
    "road_injuries": (
        ("evolution du nombre des blessés par gouvernorat et par mois 7",),
        "injuries", "Road traffic injuries (table 11.7, monthly panel)"),
    "road_deaths": (
        ("evolution du nombre des tués par gouvernorat et par mois 8",),
        "deaths", "Road traffic deaths (table 11.8, monthly panel)"),
    "money_orders": (
        ("montant des mandats émis par l étranger et payés en tunisie par 7",
         "poste: montant des mandats emis a l etranger et payes en tunisie par",
         "poste: montant des mandats emis : 10",
         "domaine de la poste: montant des mandats : 13"),
        "thousand dinars", "Money orders sent from abroad and paid in Tunisia (12.2.8)"),
}

# Excluded, with the reason, because a silent omission is indistinguishable from an
# oversight and this one is worth being loud about.
EXCLUDED = {
    "evolution du nombre des demandes d emploi par gouvernorat enregistrées 6":
        "rows labelled with months appear under a table (6.1.6) that is by governorate and "
        "prints no monthly panel; they sum to roughly 5,800 a year against the 391,927 "
        "printed for 2023, so they are not job applications",
}

# The twelve must come to the printed Total. A fifth of a percent is generous for a table
# of integers and catches a month read from the wrong column.
TOTAL_TOLERANCE = 0.005

# The tourist tables are printed once for all modes and again by mode, so the modes are an
# independent check on the combined figure -- and the only one departures has.
COMPONENTS = {
    "tourist_entries": (
        "entrées des voyageurs non résidents par nationalité et par mois 3",
        "entrées des voyageurs non résidents par nationalité et par mois 4",
        "entrées des voyageurs non résidents par nationalité et par mois 5"),
    "tourist_departures": (
        "sorties des voyageurs non residents par nationalite et par mois ( voie aerienne)",
        "sorties des voyageurs non residents par nationalite et par mois ( voie terrestre)",
        "sorties des voyageurs non résidents par nationalité et par mois 10"),
}


def _tidy(series: pd.DataFrame, titles: tuple[str, ...]) -> pd.DataFrame:
    rows = series[series.title_fr.isin(titles) & series.row_label.isin(MONTHS)
                  & series.row_kind.eq("data")]
    if rows.empty:
        raise RuntimeError(f"no monthly rows for {titles[0]!r}; has the corpus moved?")
    # Editions overlap, so one month-year is printed several times. They are reconciled
    # already in tn_yearbook_series; the mean collapses the remaining duplicates and is
    # exact wherever the editions agree, which the reconciliation has made them.
    flat = rows.groupby(["year", "row_label"], as_index=False).value.mean()
    flat["month"] = flat.row_label.map(MONTH_NUMBER)
    return flat.drop(columns="row_label").sort_values(["year", "month"])


def printed_totals(series: pd.DataFrame, titles: tuple[str, ...]) -> pd.DataFrame:
    """The twelve months against the Total printed beside them, year by year."""
    rows = series[series.title_fr.isin(titles)]
    months = (rows[rows.row_label.isin(MONTHS)].groupby("year").value
              .agg(["sum", "size"]).rename(columns={"sum": "summed", "size": "months"}))
    total = rows[rows.row_label.eq("Total")].groupby("year").value.mean().rename("printed")
    check = months.join(total, how="inner").reset_index()
    check = check[check.months.eq(len(MONTHS))]
    gap = (check.summed - check.printed).abs()
    check["agrees"] = gap <= (check.printed.abs() * TOTAL_TOLERANCE)
    return check


def component_totals(series: pd.DataFrame, name: str) -> pd.DataFrame:
    """The combined tourist figure against its air, land and sea parts, month by month."""
    titles = COMPONENTS[name]
    parts = series[series.title_fr.isin(titles) & series.row_label.isin(MONTHS)
                   & series.row_kind.eq("data")]
    whole = _tidy(series, SERIES[name][0])
    summed = (parts.groupby(["year", "row_label"], as_index=False)
              .agg(parts_sum=("value", "sum"), modes=("title_fr", "nunique")))
    summed["month"] = summed.row_label.map(MONTH_NUMBER)
    check = whole.merge(summed.drop(columns="row_label"), on=["year", "month"])
    check = check[check.modes.eq(len(titles))]
    gap = (check.parts_sum - check.value).abs()
    check["agrees"] = gap <= (check.value.abs() * TOTAL_TOLERANCE)
    check.insert(0, "series", name)
    return check


def build(series: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """One row per series and month, plus the year-level reconciliation against the total.

    Raises if the reconciliation comes back empty: every series here prints a Total, so
    nothing to compare means the comparison broke rather than that everything agreed.
    """
    if series is None:
        series = pd.read_csv("data/processed/tn_yearbook_series.csv",
                             dtype={"panel": "string"})
    # NOT filtered to row_kind == "data" here. The printed Total this module checks
    # against is an `aggregate` row, so filtering first left `printed_totals` matching
    # nothing and reporting no disagreements because it had compared nothing at all --
    # a validator that silently passes is worse than none. `_tidy` does its own filtering.
    frames, checks = [], []
    for name, (titles, unit, description) in SERIES.items():
        flat = _tidy(series, titles)
        flat["series"] = name
        flat["unit"] = unit
        flat["description"] = description
        frames.append(flat)

        check = printed_totals(series, titles)
        check.insert(0, "series", name)
        checks.append(check)

    for name in COMPONENTS:
        part = component_totals(series, name)
        checks.append(pd.DataFrame({
            "series": part.series, "year": part.year, "month": part.month,
            "summed": part.parts_sum, "printed": part.value, "agrees": part.agrees,
            "check": "air, land and sea come to the combined figure"}))

    frame = pd.concat(frames, ignore_index=True)
    reconciliation = pd.concat(checks, ignore_index=True)
    reconciliation["check"] = reconciliation["check"].fillna(
        "the twelve months come to the printed total")
    # Each *kind* of check must have matched something. Testing only that the combined
    # frame is non-empty let the component check mask a total check that had silently
    # matched nothing, which is the failure this guard exists to prevent.
    for kind, matched in reconciliation.groupby("check").size().reindex(
            ["the twelve months come to the printed total",
             "air, land and sea come to the combined figure"]).items():
        if not matched or pd.isna(matched):
            raise RuntimeError(
                f"no monthly panel could be checked by {kind!r}; that check is part of "
                "what stands between this dataset and a misread table")

    # A year whose months contradict the total printed beside them has a cell read wrong
    # and the sum cannot say which, so the whole year goes -- the same rule the governorate
    # panel applies, for the same reason.
    refused = reconciliation[~reconciliation.agrees]
    # A failing *year* takes its twelve months; a failing *month* takes only itself. The
    # governorate panel learned this the hard way -- matching a cell-level refusal on the
    # year deleted the other twenty-three governorates with it.
    bad_years = set(zip(refused[refused.month.isna()].series,
                        refused[refused.month.isna()].year, strict=True))
    months = refused[refused.month.notna()]
    bad_months = set(zip(months.series, months.year, months.month, strict=True))
    # Both sides wrapped in a Series: `list & Series` is a TypeError in pandas 2.
    year_ok = pd.Series([pair not in bad_years for pair in
                         zip(frame.series, frame.year, strict=True)], index=frame.index)
    month_ok = pd.Series([key not in bad_months for key in
                          zip(frame.series, frame.year, frame.month, strict=True)],
                         index=frame.index)
    frame = frame[year_ok & month_ok].copy()

    frame["t"] = frame.year + (frame.month - 1) / 12.0
    # Months from January 2011. Integer by construction, so the cutoff sits exactly on a
    # sample point rather than between two.
    frame["running"] = ((frame.year - CUTOFF_YEAR) * 12
                        + (frame.month - CUTOFF_MONTH)).astype(int)
    frame["treated"] = frame.running >= 0
    frame["log_value"] = np.where(frame.value > 0, np.log(frame.value), np.nan)

    # How much of each year actually reached print. Twelve months everywhere except the
    # 2011 tourism peak season, where INS printed an ellipsis; carried on every row so a
    # reader cannot use a series without seeing where it is thin.
    published = frame.groupby(["series", "year"]).month.transform("size") / len(MONTHS)
    frame["published_share"] = published.round(4)

    columns = ["series", "description", "unit", "year", "month", "t", "running",
               "treated", "value", "log_value", "published_share"]
    frame = frame[columns].sort_values(["series", "running"], ignore_index=True)
    return frame, reconciliation.sort_values(["series", "year"], ignore_index=True)
