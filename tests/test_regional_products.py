"""Checks on the product-by-region tables read out of the four survey volumes.

The failure mode here is specific and silent: these are right-to-left tables, so a
column mapping taken from the header would attach real numbers to the wrong regions and
nothing downstream would look wrong. Most of what follows exists to make that
impossible rather than unlikely.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from consumptiontn import build_regional_products as brp

pytestmark = pytest.mark.needs_raw


@pytest.fixture(scope="module")
def corpus():
    return brp.build()


# ------------------------------------------------------------------- row parsing

def test_a_row_yields_eight_values_and_its_arabic_label():
    line = "  763489   726636   742529   558460   839968   612940   721146   921218      التغذية"
    label, values = brp.split_row(line)
    assert label == "التغذية"
    assert values == [763489, 726636, 742529, 558460, 839968, 612940, 721146, 921218]


def test_a_row_short_of_a_column_is_refused_rather_than_padded():
    """Padding a short row would shift every region by one, which is the whole danger."""
    assert brp.split_row("  1  2  3  4  5  6  7   التغذية") is None


def test_an_of_which_row_is_not_data():
    assert brp.split_row("  1 2 3 4 5 6 7 8   منها :") is None


def test_a_row_with_no_arabic_label_is_refused():
    assert brp.split_row("  1  2  3  4  5  6  7  8   total") is None


# --------------------------------------------------------------- column identity

def test_columns_are_identified_from_the_published_regional_means():
    """2010's grand total, matched against what the volume publishes separately."""
    source = next(s for s in brp.PDF_SOURCES if s.wave == 2010)
    total = [2600782, 2064015, 2464116, 1622455, 3080651, 1753596, 2240881, 3498272]
    assert brp.column_order(source, total) == [
        "National", "South West", "South East", "Centre West",
        "Centre East", "North West", "North East", "Grand Tunis",
    ]


def test_a_total_row_that_matches_nothing_is_refused():
    source = next(s for s in brp.PDF_SOURCES if s.wave == 2010)
    with pytest.raises(RuntimeError, match="not identified"):
        brp.column_order(source, [1, 2, 3, 4, 5, 6, 7, 8])


def test_the_two_centre_regions_swap_between_waves():
    """The reason the mapping is derived per wave instead of written down once.

    2005 prints Centre East before Centre West; 2010 prints them the other way round.
    A single hardcoded order would have swapped two regions for one whole wave.
    """
    older = next(s for s in brp.PDF_SOURCES if s.wave == 2005)
    newer = next(s for s in brp.PDF_SOURCES if s.wave == 2010)
    order_2005 = brp.column_order(
        older, [1820555, 1465816, 1825737, 2083909, 1137711, 1416607, 1613342, 2389756])
    order_2010 = brp.column_order(
        newer, [2600782, 2064015, 2464116, 1622455, 3080651, 1753596, 2240881, 3498272])
    assert order_2005[3:5] == ["Centre East", "Centre West"]
    assert order_2010[3:5] == ["Centre West", "Centre East"]
    assert order_2005 != order_2010


# ------------------------------------------------------------------- the corpus

def test_every_wave_is_present(corpus):
    long, gini, _ = corpus
    assert sorted(gini.wave.unique()) == [2005, 2010, 2015, 2021]
    assert set(long.region) == set(brp.COLUMNS)


def test_a_printed_value_is_reproduced(corpus):
    """Table page of the 2010 volume: food, Grand Tunis, 921218 millimes per person."""
    long, _, _ = corpus
    row = long[(long.wave == 2010) & (long.product_ar == "التغذية")
               & (long.region == "Grand Tunis")]
    assert float(row.expenditure_pc_millimes.iloc[0]) == pytest.approx(921218)


def test_recovered_weights_are_the_real_population_shares(corpus):
    """The strongest check available: the weights are never told what they should be.

    They are fitted from the extracted table alone, and they have to come out as the
    regional population shares. Under a wrong column mapping no weights could.
    """
    long, _, _ = corpus
    wide = long.pivot_table(index=["wave", "product_ar"], columns="region",
                            values="expenditure_pc_millimes").reset_index()
    fitted = brp.recovered_population_shares(wide[wide.wave == 2021])

    household = pd.read_csv("data/processed/tn_hbs_2021_household.csv")
    actual = household.groupby("region").weight_pop.sum()
    actual = (actual / actual.sum()).reindex(brp.REGIONS).to_numpy()

    assert fitted.sum() == pytest.approx(1.0, abs=0.02)
    assert np.abs(fitted - actual).max() < 0.01


def test_rows_failing_the_national_check_are_published_not_dropped(corpus):
    _, _, refused = corpus
    assert len(refused) < 10, "a sudden crop of refusals means the parse regressed"
    assert {"wave", "product_ar", "implied_national", "reason"} <= set(refused.columns)


def test_no_kept_row_contradicts_its_own_regions(corpus):
    """What survives must reconcile; that is the point of publishing the refusals."""
    long, _, _ = corpus
    wide = long.pivot_table(index=["wave", "product_ar"], columns="region",
                            values="expenditure_pc_millimes").reset_index()
    for wave, group in wide.groupby("wave"):
        weights = brp.recovered_population_shares(group)
        implied = group[brp.REGIONS].to_numpy(float) @ weights
        national = group["National"].to_numpy(float)
        error = np.abs(implied - national)
        allowed = np.maximum(brp.TOLERANCE * national, brp.FLOOR)
        assert (error <= allowed).all(), f"{wave}: a kept row fails its own check"


# --------------------------------------------------------------------- the index

def test_an_evenly_spread_good_has_a_spatial_gini_of_zero():
    weights = np.full(7, 1 / 7)
    assert brp.spatial_gini(np.full(7, 250.0), weights) == pytest.approx(0.0, abs=1e-12)


def test_concentration_raises_the_index():
    weights = np.full(7, 1 / 7)
    even = brp.spatial_gini(np.array([10, 10, 10, 10, 10, 10, 10.0]), weights)
    skewed = brp.spatial_gini(np.array([1, 1, 1, 1, 1, 1, 64.0]), weights)
    assert even < skewed
    assert 0.0 <= skewed < 1.0


def test_the_index_ignores_the_unit_it_is_measured_in():
    """Millimes or dinars must give the same answer, or the series is not comparable."""
    weights = np.array([0.24, 0.14, 0.10, 0.24, 0.13, 0.09, 0.06])
    values = np.array([120.0, 80, 55, 110, 40, 70, 65])
    assert brp.spatial_gini(values, weights) == pytest.approx(
        brp.spatial_gini(values * 1000, weights))


def test_an_outlier_region_counts_for_as_many_people_as_it_holds():
    """Population weighting is the whole reason a small region cannot dominate.

    One region spends four times the rest. When it holds a hundredth of the country
    almost everybody still spends the same and the index is near zero; when it holds two
    fifths, a large minority really does spend differently and the index reflects that.
    """
    values = np.array([100.0, 100, 100, 100, 100, 100, 400])
    tiny = np.array([0.24, 0.15, 0.15, 0.15, 0.15, 0.15, 0.01])
    large = np.array([0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.40])
    assert brp.spatial_gini(values, tiny) < 0.05
    assert brp.spatial_gini(values, large) > 0.25


def test_a_balanced_panel_of_goods_exists(corpus):
    """111 goods are priced in all four waves; fewer would not make a series."""
    _, gini, _ = corpus
    counts = gini.groupby("product_ar").wave.nunique()
    assert (counts == 4).sum() >= 100


def test_the_published_index_is_rounded_so_it_reproduces_elsewhere(corpus):
    """A dataset that only rebuilds identically on one machine is not reproducible.

    The weights come from `lstsq`, whose last bits differ between BLAS builds, and that
    difference reached every Gini in the file. CI caught it; a reader would not have.
    """
    _, gini, _ = corpus
    values = gini.spatial_gini.dropna()
    assert (values.round(brp.GINI_DECIMALS) == values).all()

    long, _, _ = corpus
    wide = long.pivot_table(index=["wave", "product_ar"], columns="region",
                            values="expenditure_pc_millimes").reset_index()
    shares = brp.recovered_population_shares(wide[wide.wave == 2021])
    assert (np.round(shares, brp.SHARE_DECIMALS) == shares).all()
