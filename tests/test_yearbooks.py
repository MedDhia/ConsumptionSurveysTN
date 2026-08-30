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


# ------------------------------------------------------------------- the whole corpus

@pytest.fixture(scope="module")
def corpus():
    from consumptiontn import build_yearbook

    return build_yearbook.build()


def test_catalogue_covers_every_edition(corpus):
    tables, _, _ = corpus
    from consumptiontn.config import YEARBOOK_FILE_IDS

    assert set(tables.edition) == set(YEARBOOK_FILE_IDS)


def test_catalogue_excludes_contents_page_entries(corpus):
    """Index entries match the heading pattern too, and near-duplicate every title.

    They are recognisable by their dotted leaders, and the catalogue is meant to hold
    the tables rather than the list that points at them.
    """
    tables, _, _ = corpus
    leaders = tables[tables.table_title.str.contains(r"\.{4,}", regex=True, na=False)]
    assert leaders.empty, f"{len(leaders)} contents-page rows leaked into the catalogue"


def test_no_conflicting_cell_reaches_the_series(corpus):
    """The whole point of reconciliation: a cell two editions disagree about is dropped."""
    _, series, _ = corpus
    assert "conflict" not in set(series.agreement)


def _year_column(series):
    """Cells from tables whose columns are years, as opposed to a classification."""
    return series[series.column_label == series.year.astype(str)]


def test_most_year_column_cells_are_corroborated_by_a_second_edition(corpus):
    """Editions overlap by five years, so corroboration should be the common case.

    Scoped to year-column tables on purpose. Those are the ones a later edition reprints,
    so a fall here would mean the title normalisation stopped matching the same table
    across editions -- silently disabling the corpus's main check. Measuring over every
    cell instead would let a flood of uncorroborable classification rows mask that.
    """
    _, series, _ = corpus
    confirmed = (_year_column(series).agreement == "confirmed").mean()
    assert confirmed > 0.5, f"only {confirmed:.1%} of year-column cells are confirmed"


def test_classification_tables_are_honestly_marked_uncorroborated(corpus):
    """A single-year table cannot be cross-checked, and must not look as if it were.

    Table 1.4 in the 2023 edition is the population at 1.7.2023; the same table in the
    2019 edition is the population at 1.7.2019. Different data, so the cell is never
    printed twice and nothing corroborates it. `single source` is the correct label, and
    a reader filtering on `agreement` depends on it being applied.
    """
    _, series, _ = corpus
    classification = series[series.column_label != series.year.astype(str)]
    assert not classification.empty
    single = (classification.agreement == "single source").mean()
    assert single > 0.8, f"only {single:.1%} of classification cells are marked single source"


def test_every_confirmed_cell_really_had_more_than_one_edition(corpus):
    _, series, _ = corpus
    confirmed = series[series.agreement == "confirmed"]
    assert (confirmed.n_editions > 1).all()
    single = series[series.agreement == "single source"]
    assert (single.n_editions == 1).all()


def test_generic_extractor_reproduces_the_bespoke_unemployment_series(corpus):
    """Two independent code paths over the same printed table must agree exactly.

    ``build_labour`` locates the table by title and reads named rows; the generic
    extractor finds it by shape and knows nothing about unemployment. Where they
    overlap they are reading the same ink, so any difference is a bug in one of them.
    """
    from consumptiontn import build_labour

    _, series, _ = corpus
    bespoke = build_labour.build()
    bespoke = bespoke[bespoke.breakdown == "education"]
    names = {"Sans niveau": "none", "Primaire": "primary", "Secondaire": "secondary",
             "Supèrieur": "higher", "Total": "all"}
    generic = series[series.title_fr.str.contains("chômage selon le niveau", na=False)]
    generic = generic.assign(group=generic.row_label.map(names)).dropna(subset=["group"])
    joined = bespoke.merge(generic, on=["year", "group"])
    assert len(joined) > 50, f"only {len(joined)} overlapping cells -- the join broke"
    assert (joined.unemployment_rate - joined.value).abs().max() == 0


def test_aggregate_rows_are_marked(corpus):
    """Totals and regional subtotals sit among the data rows; summing without filtering
    them roughly double-counts."""
    _, series, _ = corpus
    kinds = set(series.row_kind)
    assert kinds <= {"data", "aggregate"}
    assert (series.row_kind == "aggregate").sum() > 100


def test_coverage_accounts_for_every_catalogued_table(corpus):
    tables, _, coverage = corpus
    assert set(tables.table_title) <= set(coverage.title_fr)
    assert (coverage.values_kept <= coverage.values_read).all()


def test_years_are_plausible(corpus):
    _, series, _ = corpus
    assert series.year.between(1900, 2030).all()


def test_classification_tables_carry_a_year_from_the_page(corpus):
    """Never dated from the edition's cover: table 13.8 in the 2023 edition covers
    2018-2022, so the cover year would be wrong by a year for every value in it."""
    _, series, _ = corpus
    assert series.year.notna().all()


def test_column_labels_are_populated(corpus):
    _, series, _ = corpus
    assert series.column_label.notna().all()
    assert (series.column_label.str.len() > 0).all()


def test_a_known_classification_table_matches_the_printed_page(corpus):
    """Table 1.8, fertility by governorate, 2023 edition: Tunis reads I.S.F 1.40 and
    T.G.F 41.6 on the page. Classification tables have no cross-edition check, so at
    least one is pinned against the paper."""
    _, series, _ = corpus
    tunis = series[series.title_fr.str.contains("fécondite", na=False)
                   & series.row_label.eq("Tunis") & series.year.eq(2023)]
    values = dict(zip(tunis.column_label, tunis.value, strict=True))
    assert round(values["I.S.F"], 2) == 1.40
    assert round(values["T.G.F"], 1) == 41.6


# ------------------------------------------------- headers that need the page geometry

def test_nested_year_header_dates_each_column(corpus):
    """Table 1.9 puts 2023 and 2022 across the top with Masculin / Feminin / Mas-Fem
    under each. Six columns hang off two year cells, and each must inherit its own year
    -- a single page-level year would date half the table wrongly."""
    _, series, _ = corpus
    births = series[series.title_fr.str.contains("naissances par genre", na=False)
                    & series.row_label.eq("Tunis") & series.edition.eq(2023)]
    by_column = dict(zip(births.column_label, zip(births.year, births.value, strict=True),
                         strict=True))
    assert by_column["2023 Feminin"] == (2023, 5429.0)
    assert by_column["2022 Feminin"] == (2022, 5958.0)
    assert by_column["2023 Masculin"] == (2023, 5765.0)


def test_header_split_over_lines_is_reassembled(corpus):
    """On the continuation page of table 1.2 the cells read TOTAL, "80 ans &+" and the
    age bands across three lines, and TOTAL is printed last though it belongs first.
    Only the column geometry gets the order right."""
    _, series, _ = corpus
    page = series[series.title_fr.str.contains("groupe d age genre", na=False)
                  & series.row_label.eq("Tunis") & series.column_label.eq("TOTAL")]
    assert not page.empty
    assert 535.4 in set(page.value)


def test_a_lone_dash_reads_as_zero(corpus):
    """INS's conventions table defines "-" as resultat rigoureusement nul: an observed
    zero, distinct from ">>" and "..." which mean unavailable. Table 1.13 records no
    still-births in Manouba for 2020 and 2021, printed as dashes."""
    _, series, _ = corpus
    manouba = series[series.title_fr.str.contains("morts-n", na=False)
                     & series.row_label.eq("Manouba")]
    values = dict(zip(manouba.year, manouba.value, strict=True))
    assert values[2021] == 0.0
    assert values[2020] == 0.0
    assert values[2023] == 3.0


def test_year_header_may_be_flanked_by_its_caption():
    """"Gouvernorat 2023 2022 2021 2020 2019 الولاية" is a header, not prose."""
    from consumptiontn.build_yearbook import _year_header

    assert _year_header("Gouvernorat 2023 2022 2021 2020 2019 الولاية") == [
        2023, 2022, 2021, 2020, 2019
    ]
    assert _year_header("2015 2016") == [2015, 2016]
    # Two caption words at one end is prose, and must not be read as a header.
    assert _year_header("Evolution des prix entre 2015 2016") is None


def test_layout_reader_never_overrides_the_single_line_paths():
    """It runs only as a fallback, so it can add tables but not change one already read.

    Checked on a page the single-line path handles: both readers see it, and the
    fallback's output is discarded because the first one produced rows.
    """
    from consumptiontn.build_yearbook import edition_pages, parse_page, parse_page_layout

    text = edition_pages(2023)[23]  # table 1.4, read by the category-header path
    direct, _ = parse_page(2023, 23, text)
    assert direct, "expected the single-line path to handle this page"
    assert parse_page_layout(2023, 23, text), "expected the fallback to also parse it"
    # extract() prefers `direct`; this asserts the two agree on the values, so the
    # preference is not hiding a discrepancy.
    assert {(r["row_label"], r["value"]) for r in direct} == {
        (r["row_label"], r["value"]) for r in parse_page_layout(2023, 23, text)
    }
