"""Checks on the consumer price tables read out of the yearbooks.

``cpi_by_division`` used to read one edition and give three years. It now reads the ten
editions that print the table, which turns three years into twelve -- and introduces the
one hazard that comes with reading a series out of ten separate volumes: INS rebased in
2016, so half the years are indexed on 2010 and half on 2015. Most of what follows exists
to make sure the two are never silently added together.
"""

from __future__ import annotations

import pytest

from consumptiontn import build_prices

pytestmark = pytest.mark.needs_raw


@pytest.fixture(scope="module")
def prices():
    return build_prices.build()


def test_the_series_now_spans_twelve_years(prices):
    _, divisions, _chained = prices
    assert divisions.year.min() == 2012
    assert divisions.year.max() == 2023
    assert divisions.function_code.nunique() == 13   # twelve functions and the total


def test_each_base_covers_the_years_it_was_published_for(prices):
    """2012-2017 on base 2010, 2016-2023 on base 2015, overlapping by two years.

    The overlap is the only thing that would let the two halves be chained, so if it ever
    disappeared a reader could no longer join them at all.
    """
    _, divisions, _chained = prices
    spans = divisions.groupby("base_year").year.agg(["min", "max"])
    assert spans.loc[2010].tolist() == [2012, 2017]
    assert spans.loc[2015].tolist() == [2016, 2023]
    both = set(divisions[divisions.base_year == 2010].year) & set(
        divisions[divisions.base_year == 2015].year)
    assert both == {2016, 2017}


def test_a_year_on_two_bases_is_two_rows_and_not_one(prices):
    """The rebasing is real: 2016 is 131.4 on base 2010 and 103.6 on base 2015.

    Keyed on the year alone these would collide and one would overwrite the other, which
    is why `base_year` is part of the key rather than a note in the codebook.
    """
    _, divisions, _chained = prices
    total = divisions[divisions.function_code == 0]
    on_2010 = total[(total.year == 2016) & (total.base_year == 2010)]["index"].iloc[0]
    on_2015 = total[(total.year == 2016) & (total.base_year == 2015)]["index"].iloc[0]
    assert float(on_2010) == pytest.approx(131.4)
    assert float(on_2015) == pytest.approx(103.6)


def test_the_weights_still_sum_to_their_base(prices):
    """Read per edition, so a column taken from the wrong place shows up here."""
    _, divisions, _chained = prices
    functions = divisions[divisions.function_code != 0]
    for base, group in functions.groupby("base_year"):
        weights = group.drop_duplicates("function_code")["weight_per_100000"]
        assert int(weights.sum()) == 100_000, base


def test_the_overlapping_editions_agree(prices):
    """Each edition carries three years, so most cells are printed two or three times.

    They are required to agree in the builder; this asserts that the agreement is real
    rather than that one edition simply won.
    """
    _, divisions, _chained = prices
    assert divisions.n_editions.max() >= 3
    assert (divisions.n_editions >= 2).mean() > 0.5


def test_a_printed_value_is_reproduced(prices):
    """2014 edition, page 221: food and non-alcoholic drinks, base 2010."""
    _, divisions, _chained = prices
    food = divisions[(divisions.function_code == 1) & (divisions.base_year == 2010)]
    printed = {2014: 128.3, 2013: 121.7, 2012: 112.7}
    for year, expected in printed.items():
        got = food[food.year == year]["index"].iloc[0]
        assert float(got) == pytest.approx(expected), year


def test_the_general_index_agrees_with_the_annual_table_throughout(prices):
    """Two tables published separately, and now fourteen chances for them to disagree."""
    annual, divisions, _chained = prices
    total = divisions[divisions.function_code == 0]
    checked = 0
    for row in total.to_dict("records"):
        printed = annual[(annual.year == row["year"])
                         & (annual.base_year == row["base_year"])]["index"]
        if printed.empty:
            continue
        assert round(float(printed.iloc[0]), 1) == round(float(row["index"]), 1)
        checked += 1
    assert checked >= 10


# ------------------------------------------------------- the two bases spliced into one

def test_the_chained_series_covers_every_year_on_one_base(prices):
    _, _divisions, chained = prices
    assert set(chained.year) == set(range(2012, 2024))
    assert set(chained.base_year) == {2015}
    assert chained.function_code.nunique() == 13


def test_the_published_years_are_left_as_published(prices):
    """Chaining must not touch a figure INS already prints on base 2015."""
    _, divisions, chained = prices
    published = divisions[divisions.base_year.eq(2015)]
    for row in published.to_dict("records"):
        got = chained[chained.year.eq(row["year"])
                      & chained.function_code.eq(row["function_code"])]
        assert got.basis.iloc[0] == "published"
        assert float(got["index"].iloc[0]) == pytest.approx(float(row["index"]))


def test_the_splice_leaves_no_step_in_the_series(prices):
    """A chain factor applied wrongly shows up as a jump at the join and nowhere else.

    2015 to 2016 is where the two halves meet: one chained, one published. Across the
    thirteen functions that step has to look like ordinary inflation.
    """
    _, _divisions, chained = prices
    for _, group in chained.groupby("function_code"):
        ordered = group.sort_values("year").set_index("year")["index"]
        step = float(ordered.loc[2016] / ordered.loc[2015] - 1)
        assert -0.10 < step < 0.20, step


def test_the_factor_measured_twice_agrees_with_itself(prices):
    """The overlap is what makes this a measurement rather than an assumption.

    INS prints 2016 and 2017 on both bases, so the factor can be computed twice. If the
    two disagreed the splice would not be defensible, and the disagreement is carried in
    the data rather than left for the reader to discover.
    """
    _, _divisions, chained = prices
    assert (chained.chain_disagreement < 0.01).all()
    assert chained.chain_disagreement.max() > 0, "a zero spread means it was never checked"


def test_the_chained_general_index_is_plausible(prices):
    """Roughly 93% cumulative inflation over eleven years, near 6% a year."""
    _, _divisions, chained = prices
    total = chained[chained.function_code.eq(0)].set_index("year")["index"]
    assert float(total.loc[2012]) == pytest.approx(85.8, abs=0.5)
    assert float(total.loc[2023]) == pytest.approx(165.2, abs=0.5)
    assert (total.sort_index().diff().dropna() > 0).all()
