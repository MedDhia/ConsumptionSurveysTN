"""Checks on the governorate panel.

This dataset carries no numbers of its own: every value comes from `tn_yearbook_series`,
already reconciled across editions. What it adds is *interpretation* — which table a
number came from, what it measures, and which governorate it belongs to — and that is
exactly what can be wrong in a way no arithmetic would notice. A table of court seats
labelled as governorates looks perfectly well-formed.

So the tests here are about meaning rather than parsing: that the national totals hold,
that the tables which are not governorate tables stayed out, and that the two independent
checks available — INS's own printed totals, and Tunisia's known population — both pass.
"""

from __future__ import annotations

import pandas as pd
import pytest

from consumptiontn import build_governorates as G


@pytest.fixture(scope="module")
def panel():
    # The caption is empty for most rows, so pandas infers a mixed column unless told.
    return G.build(pd.read_csv("data/processed/tn_yearbook_series.csv",
                               dtype={"panel": "string"}))


# ------------------------------------------------------------------ shape and coverage

def test_every_indicator_covers_all_twenty_four_governorates(panel):
    """A governorate missing from one indicator is usually a spelling variant.

    Sidi Bouzid was absent from the money-order series because that table sets it without
    its space, and Ben Arous from the court tables for the same reason. One missing
    governorate quietly biases every cross-sectional comparison drawn from the panel.
    """
    frame, _ = panel
    # From 2002 on, every governorate exists and every indicator must carry all of them.
    settled = frame[frame.year.ge(2002) & ~frame.indicator.str.startswith("population_")]
    counts = settled.groupby("indicator").governorate.nunique()
    assert (counts == 24).all(), counts[counts != 24].to_dict()
    assert set(frame.governorate) == set(G.GOVERNORATES)


def test_the_long_series_really_are_long(panel):
    frame, _ = panel
    spans = frame[frame.breakdown.eq("")].groupby("indicator").year.nunique()
    assert (spans >= 10).all(), spans[spans < 10].to_dict()
    assert (spans >= 29).sum() >= 10, "ten indicators should run the full 1995-2023"


def test_a_cell_appears_once(panel):
    """A governorate reaching the panel under two printed labels must be pooled, not kept
    twice: "Ariana" and "7        Ariana" are the same place in two editions."""
    frame, _ = panel
    assert not frame.duplicated(["governorate", "year", "indicator", "breakdown"]).any()


def test_pooling_the_labels_raises_the_corroboration(panel):
    """The point of pooling is not tidiness. Two labels are two independent printings."""
    frame, _ = panel
    yearly = frame[frame.breakdown.eq("")]
    assert (yearly.agreement == "confirmed").mean() > 0.8


# --------------------------------------------------------------- what the numbers say

def test_the_population_series_matches_tunisia(panel):
    """The one check with an outside referee.

    Summed over the 24 governorates this has to be Tunisia's population, and it is: 10.03
    million in 2005 and 11.87 million in 2023, against published figures of the same. No
    column mapping that was wrong could land on those.
    """
    frame, _ = panel
    total = frame[frame.indicator.eq("population")].groupby("year").value.sum()
    assert total.loc[2005] == pytest.approx(10_029, abs=30)
    assert total.loc[2023] == pytest.approx(11_868, abs=30)
    # And it rises every single year, as Tunisia's population did.
    assert (total.sort_index().diff().dropna() > 0).all()


def test_the_governorates_sum_to_the_printed_national_total(panel):
    """INS prints the total beside the parts. They must agree, and they do."""
    frame, _ = panel
    series = pd.read_csv("data/processed/tn_yearbook_series.csv",
                         dtype={"panel": "string"})
    checked = G.national_totals(frame, series)
    assert len(checked) >= 300, "too few indicator-years could be checked"
    assert checked.agrees.all(), checked[~checked.agrees][
        ["indicator", "year", "summed", "printed"]].to_dict("records")


def test_the_years_that_fail_are_published_not_dropped(panel):
    """Each refusal marks a page worth re-reading, so it is named rather than deleted."""
    _, refused = panel
    assert not refused.empty
    assert {"indicator", "year", "governorate", "breakdown",
            "summed", "printed", "gap", "reason"} == set(refused.columns)
    # Library lending in 2000: Manouba reads 404 books against 150,250 the year after.
    assert ((refused.indicator == "library_books_lent") & (refused.year == 2000)).any()


def test_a_refused_year_is_absent_from_the_panel(panel):
    frame, refused = panel
    years = refused[refused.governorate.eq("")]
    for row in years.to_dict("records"):
        present = frame[(frame.indicator == row["indicator"]) & (frame.year == row["year"])]
        assert present.empty, f"{row['indicator']} {row['year']} was refused but shipped"


# --------------------------------------------------------- what is deliberately absent

def test_the_court_tables_stayed_out(panel):
    """They look like governorate tables. Their rows are courts of first instance.

    Grombalia is a court in Nabeul and Tunis is split into two, so the names that look
    like governorates sum to 86% of the printed total every year. Nothing about the table
    says so; only the total does.
    """
    frame, _ = panel
    assert "divorces" not in set(frame.indicator)
    assert "court_cases_filed" not in set(frame.indicator)
    for title in ("divorces prononcés par les tribunaux de 1ère instance 18",
                  "affaires enrolées devant les tribunaux de 1ere instance en matière 8"):
        assert title in G.EXCLUDED
        assert "courts of first instance" in G.EXCLUDED[title]


def test_the_paramedical_and_secondary_tables_stayed_out(panel):
    """Two tables whose breakdown cannot be read cleanly: grade labels fused with the
    year, and a column crossing period with measure in too many forms."""
    frame, _ = panel
    assert "répartition du personnel 4" in G.EXCLUDED
    assert "nombre d établissements du 2ème cycle de l enseignement de 14" in G.EXCLUDED
    assert not frame.indicator.str.contains("paramedical").any()


def test_nothing_is_both_named_and_excluded():
    assert not (set(G.INDICATORS) & set(G.EXCLUDED))


# ------------------------------------------------------------------ the label handling

def test_a_stray_digit_before_the_label_is_stripped():
    """pdftotext drops the Arabic side's digits onto their own lines, and one sometimes
    lands at the head of a row. The values are untouched, so the row is kept."""
    assert G._governorate("7        Ariana") == "Ariana"
    assert G._governorate("0        Béja") == "Béja"


def test_a_missing_space_still_resolves():
    assert G._governorate("SidiBouzid") == "Sidi Bouzid"
    assert G._governorate("BenArous") == "Ben Arous"


def test_something_that_is_not_a_governorate_is_refused():
    """Grombalia is a court seat and Total an aggregate; neither may become a row."""
    assert G._governorate("Grombalia") is None
    assert G._governorate("Total") is None
    assert G._governorate("District-Tunis") is None


def test_a_year_column_is_not_carried_as_a_breakdown():
    """Both notations INS uses for a period, and one that is not a period at all."""
    frame = pd.DataFrame({"column_label": ["2019", "2018/19", "19-18", "04-00"],
                          "year": [2019, 2018, 2018, 2010]})
    assert G._period_column(frame).tolist() == [True, True, True, False]


# ------------------------------------------------------------ population by age and sex

def test_population_by_age_is_now_readable(panel):
    """It used to be excluded outright. The sex was printed as a caption beside the
    row-label heading and dropped on extraction, leaving three near-identically titled
    tables that could not be told apart. The corpus keeps that caption now."""
    frame, _ = panel
    by_sex = frame[frame.indicator.str.startswith("population_")]
    assert set(by_sex.indicator) == {"population_male", "population_female", "population_all"}
    assert by_sex.year.min() == 2007
    assert by_sex.governorate.nunique() == 24
    assert "population_by_age" not in set(G.EXCLUDED)


def test_the_age_bands_are_written_the_right_way_round(panel):
    """INS prints them backwards: "24-20" is the 20-to-24 band."""
    frame, _ = panel
    bands = sorted(set(frame[frame.breakdown.ne("")].breakdown))
    assert bands[0] == "00-04"
    assert "20-24" in bands and "80+" in bands
    assert len(bands) == 17
    assert G._age_band("24-20") == "20-24"
    assert G._age_band("Masculin 80ans &+") == "80+"
    assert G._age_band("2019") is None


def test_men_and_women_make_the_figure_printed_for_both(panel):
    """Nothing tells the parser which page is which sex. If the captions had been attached
    to the wrong pages this would fail everywhere; instead it holds throughout, because
    the cells where it does not are refused."""
    frame, _ = panel
    age = frame[frame.breakdown.ne("")]
    wide = age.pivot_table(index=["governorate", "year", "breakdown"],
                           columns="indicator", values="value").dropna()
    assert len(wide) > 3_000
    gap = (wide.population_male + wide.population_female - wide.population_all).abs()
    assert (gap <= G.SEX_TOLERANCE).all()


def test_the_inconsistent_age_cells_are_published(panel):
    _, refused = panel
    sexes = refused[refused.reason.str.startswith("men plus women")]
    assert not sexes.empty
    assert (sexes.governorate != "").all() and (sexes.breakdown != "").all()


def test_only_the_age_table_carries_a_breakdown(panel):
    """The other thirty indicators are one value per governorate and year."""
    frame, _ = panel
    plain = frame[~frame.indicator.str.startswith("population_")]
    assert (plain.breakdown == "").all()


# ------------------------------------------- ready for cross-year and cross-governorate

def test_the_manouba_split_is_flagged_where_it_bites(panel):
    """Manouba was created in 2000 out of Ariana, and nothing in the table says so.

    Ariana falls between 43% and 54% in a single year across ten unrelated indicators --
    primary pupils 89,168 to 45,718, marriages 2,887 to 1,397 -- while Ariana plus Manouba
    stays continuous. Anyone comparing Ariana in 1999 with Ariana in 2005 is measuring an
    administrative boundary, so those rows say so.
    """
    frame, _ = panel
    flagged = frame[frame.boundary.ne("")]
    assert not flagged.empty
    assert set(flagged.governorate) == {"Ariana"}
    assert flagged.year.max() <= G.SPLIT_LAST_YEAR
    assert flagged.indicator.nunique() >= 10


def test_manouba_has_no_figures_before_it_existed(panel):
    """A printed 0 for a governorate that did not exist is not an observation of zero.

    Left in, a growth rate computed off it is infinite. They are removed and published.
    """
    frame, refused = panel
    early = frame[frame.governorate.eq("Manouba") & frame.year.lt(2000)]
    assert early.empty, early[["indicator", "year", "value"]].to_dict("records")
    removed = refused[refused.reason.str.startswith("Manouba did not exist")]
    assert not removed.empty
    assert removed.year.max() <= G.SPLIT_LAST_YEAR


def test_a_cell_level_refusal_does_not_take_the_year_with_it(panel):
    """A refusal naming one governorate must not delete the other twenty-three.

    Adding the pre-creation Manouba cells to the refusal frame silently dropped six years
    of job offers for every governorate, because the rule that removes a convicted *year*
    matched them too.
    """
    frame, _ = panel
    offers = frame[frame.indicator.eq("job_offers")]
    assert offers.year.min() == 1995
    assert offers[offers.year.eq(1995)].governorate.nunique() == 23  # all but Manouba


def test_a_count_can_be_put_per_head(panel):
    """Comparing counts across governorates without a denominator ranks them by size.

    Tunis has roughly nine times Tozeur's people, so the denominator travels with every
    row rather than being a join the reader has to get right.
    """
    frame, _ = panel
    assert "population_thousands" in frame.columns
    covered = frame[frame.year.ge(2005)]
    assert covered.population_thousands.notna().mean() > 0.99

    # And it is the right denominator: population per head is 1.
    people = frame[frame.indicator.eq("population") & frame.year.eq(2015)]
    ratio = people.value / people.population_thousands
    assert ratio.round(6).eq(1.0).all()


def test_the_years_without_a_denominator_are_visibly_empty(panel):
    """No yearbook in the corpus prints population by governorate before 2005.

    That is a limit of the source, not of the parse, so it is left missing rather than
    interpolated -- but a reader has to be able to see where.
    """
    frame, _ = panel
    early = frame[frame.year.lt(2005)]
    assert not early.empty
    assert early.population_thousands.isna().all()
