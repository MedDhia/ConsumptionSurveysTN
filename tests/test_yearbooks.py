"""Checks on what was read out of the statistical yearbook PDFs.

Parsing a bilingual PDF is the least trustworthy step in this pipeline: a column offset
produces numbers that are the right shape, the right magnitude and completely wrong.
Every test here is a way of catching that without a human re-reading the page.

The strongest of them is the overlap test. Each edition carries about five years, so
2015 appears in two editions and 2019 in two. If the parser took the wrong column from
either volume, the shared years stop agreeing.
"""

from __future__ import annotations

import pandas as pd
import pytest

from consumptiontn import build_labour, build_prices

pytestmark = pytest.mark.needs_raw


@pytest.fixture(scope="module")
def prices():
    return build_prices.build()


@pytest.fixture(scope="module")
def labour():
    return build_labour.build()


# ----------------------------------------------------------------------------- prices

def test_cpi_covers_the_survey_waves(prices):
    annual, _ = prices
    years = set(annual.year)
    assert {2005, 2010, 2015, 2021} <= years
    assert annual.year.min() == 1999 and annual.year.max() == 2023


def test_every_base_year_reads_100_in_its_own_year(prices):
    """The cheapest check that the eight columns were not transposed."""
    annual, _ = prices
    for base in sorted(annual.base_year.unique()):
        own = annual[(annual.base_year == base) & (annual.year == base)]
        if own.empty:
            continue
        assert round(float(own["index"].iloc[0]), 1) == 100.0, base


def test_cpi_rises_monotonically_on_every_base(prices):
    """Tunisia had no deflation in any of these years. A dip means a misread row."""
    annual, _ = prices
    for base, block in annual.groupby("base_year"):
        series = block.sort_values("year")["index"]
        assert series.is_monotonic_increasing, f"base {base} dips"


def test_division_weights_sum_to_100000(prices):
    _, divisions = prices
    weights = divisions[divisions.function_code != 0].drop_duplicates("function_code")
    assert int(weights.weight_per_100000.sum()) == 100_000


def test_all_twelve_functions_present_plus_the_total(prices):
    _, divisions = prices
    assert set(divisions.function_code.unique()) == set(range(13))


def test_general_index_agrees_between_the_two_tables(prices):
    """13.6 and 13.7 are published separately and must tell the same story."""
    annual, divisions = prices
    for year in (2021, 2022, 2023):
        left = annual[(annual.year == year) & (annual.base_year == 2015)]["index"].iloc[0]
        right = divisions[(divisions.year == year) & (divisions.function_code == 0)]["index"]
        assert round(float(left), 1) == round(float(right.iloc[0]), 1), year


def test_cpi_reproduces_published_landmarks(prices):
    """Values read off the printed page by eye, as a guard against a plausible misparse."""
    annual, _ = prices
    s = annual[annual.base_year == 2015].set_index("year")["index"]
    for year, expected in {1999: 55.3, 2005: 64.7, 2010: 79.0,
                           2015: 100.0, 2021: 139.6, 2023: 165.2}.items():
        assert round(float(s[year]), 1) == expected, year


def test_thousands_separator_and_doubled_glyphs_were_repaired(prices):
    """Two documented rendering faults, each of which fails silently if unhandled.

    ``1 013.5`` is one number split by a space; the bold base-2010 column prints every
    glyph twice, so 70.0 arrives as ``7700..00``. If either slipped through, the value
    would be absent or off by orders of magnitude.
    """
    annual, _ = prices
    assert round(float(annual[(annual.base_year == 1970) & (annual.year == 2013)]
                       ["index"].iloc[0]), 1) == 1013.5
    assert round(float(annual[(annual.base_year == 2010) & (annual.year == 1999)]
                       ["index"].iloc[0]), 1) == 70.0


# ----------------------------------------------------------------------------- labour

def test_labour_spans_2011_to_2023(labour):
    assert labour.year.min() == 2011
    assert labour.year.max() == 2023


def test_labour_series_does_not_reach_before_the_revolution(labour):
    """Guards the claim figure 19 makes about itself. If a future edition ever adds
    pre-2011 years this fails, and the figure's framing has to be revisited."""
    assert labour.year.min() >= 2011


def test_editions_agree_on_every_overlapping_year():
    """The splice check. Each edition carries five years, so some are read twice."""
    frames = [build_labour.read_edition(e) for e in build_labour.EDITIONS]
    everything = pd.concat(frames, ignore_index=True)
    spread = everything.groupby(["year", "breakdown", "group"])["unemployment_rate"]
    shared = spread.agg(["min", "max", "size"])
    assert (shared["size"] > 1).any(), "no year is read twice; the splice is unverified"
    disagree = shared[(shared["max"] - shared["min"]).round(6) > 0]
    assert disagree.empty, f"editions disagree:\n{disagree}"


def test_education_and_sex_tables_share_the_same_totals(labour):
    """Both tables carry INS's own `Total` row. They describe one population, so a
    mismatch means one of the two was read from the wrong table."""
    wide = labour.pivot_table(index="year", columns=["breakdown", "group"],
                              values="unemployment_rate")
    pd.testing.assert_series_equal(
        wide[("education", "all")], wide[("sex", "all")], check_names=False
    )


def test_unemployment_rises_with_education_in_every_year(labour):
    """The claim figure 19 is built on. Asserted rather than eyeballed once."""
    wide = labour[labour.breakdown == "education"].pivot_table(
        index="year", columns="group", values="unemployment_rate"
    )
    ladder = ["none", "primary", "secondary", "higher"]
    for year, row in wide[ladder].iterrows():
        assert list(row) == sorted(row), f"{year}: {row.to_dict()}"


def test_rates_are_percentages(labour):
    assert labour.unemployment_rate.between(0, 100).all()
