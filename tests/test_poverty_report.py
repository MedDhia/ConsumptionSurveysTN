"""Checks on the 2000-2010 poverty and inequality report.

This is the one wholly French document in the corpus, so none of the right-to-left
hazards apply. What does apply is that its tables print two measures side by side and
wrap their rows in more than one way, and that its figures are deliberately not the ones
the panel carries.
"""

from __future__ import annotations

import pytest

from consumptiontn import build_poverty_report as R

pytestmark = pytest.mark.needs_raw


@pytest.fixture(scope="module")
def report():
    return R.build()


def test_the_regional_gini_matches_the_survey_volume(report):
    """Table 11 of the 2010 survey volume prints the same seven coefficients.

    Two independent documents, one French and one Arabic, and they agree to the last
    digit. That also settles a reading the Arabic volume leaves open: pdftotext reverses
    its header, so which end of the row is 2000 cannot be told from the volume alone.
    """
    printed_in_the_2010_volume = {
        "Grand Tunis": (0.377, 0.399, 0.376),
        "North East": (0.371, 0.365, 0.293),
        "North West": (0.386, 0.357, 0.358),
        "Centre East": (0.382, 0.372, 0.360),
        "Centre West": (0.388, 0.419, 0.374),
        "South East": (0.378, 0.402, 0.360),
        "South West": (0.373, 0.382, 0.360),
    }
    gini = report[report.indicator == "gini"]
    for region, expected in printed_in_the_2010_volume.items():
        got = gini[gini.geography == region].sort_values("year").value.tolist()
        assert got == pytest.approx(list(expected)), region


def test_the_2010_consumption_column_is_there(report):
    """The reason to read this report at all: the wave the panel is missing."""
    consumption = report[(report.indicator == "consumption_pc_mean")
                         & (report.source_table == "Tableau 3")]
    assert set(consumption.year) == {2000, 2005, 2010}
    grand_tunis = consumption[(consumption.geography == "Grand Tunis")
                              & (consumption.year == 2010)]
    assert float(grand_tunis.value.iloc[0]) == pytest.approx(3228)


def test_every_row_says_which_basis_it_is_on(report):
    """These figures are not interchangeable with the panel's and must not look it."""
    assert (report.basis == "2010 methodology").all()


def test_the_report_disagrees_with_the_panel_where_it_should(report):
    """A sanity check on the premise, not on the parse.

    The 2010 revision raised the poverty line, so consumption per head on this basis sits
    below the panel's expenditure per head for the same region and wave. If the two ever
    matched exactly it would mean one of them had been mislabelled.
    """
    import pandas as pd

    panel = pd.read_csv("data/processed/tn_consumption_panel.csv")
    published = panel[(panel.indicator == "expenditure_pc_mean")
                      & (panel.geography == "Grand Tunis") & (panel.wave == 2005)
                      & (panel.milieu == "all") & panel.subgroup.isna()]
    here = report[(report.indicator == "consumption_pc_mean")
                  & (report.geography == "Grand Tunis") & (report.year == 2005)]
    assert float(here.value.iloc[0]) != float(published.value.iloc[0])


def test_standard_errors_are_smaller_than_their_estimates(report):
    with_errors = report[report.standard_error.notna()]
    assert not with_errors.empty
    assert (with_errors.standard_error < with_errors.value.abs()).all()


def test_a_national_figure_lies_inside_its_regions(report):
    """The check that catches a row read off the wrong line."""
    for (indicator, year, table), group in report.groupby(
            ["indicator", "year", "source_table"]):
        national = group[group.geography == "Tunisia"].value
        regions = group[group.geography != "Tunisia"].value
        if national.empty or regions.empty:
            continue
        assert regions.min() <= national.iloc[0] <= regions.max(), (indicator, year, table)


def test_the_irregular_tables_are_left_out(report):
    """Tables 7 and 8 cannot be read positionally, so they are absent by decision."""
    assert "poverty_rate" not in set(report.indicator)
    assert {"Tableau 3", "Tableau 4", "Tableau 6", "Tableau 17"} == set(report.source_table)
