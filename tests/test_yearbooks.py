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
    annual, _divisions, _chained = prices
    years = set(annual.year)
    assert {2005, 2010, 2015, 2021} <= years
    assert annual.year.min() == 1999 and annual.year.max() == 2023


def test_every_base_year_reads_100_in_its_own_year(prices):
    """The cheapest check that the eight columns were not transposed."""
    annual, _divisions, _chained = prices
    for base in sorted(annual.base_year.unique()):
        own = annual[(annual.base_year == base) & (annual.year == base)]
        if own.empty:
            continue
        assert round(float(own["index"].iloc[0]), 1) == 100.0, base


def test_cpi_rises_monotonically_on_every_base(prices):
    """Tunisia had no deflation in any of these years. A dip means a misread row."""
    annual, _divisions, _chained = prices
    for base, block in annual.groupby("base_year"):
        series = block.sort_values("year")["index"]
        assert series.is_monotonic_increasing, f"base {base} dips"


def test_division_weights_sum_to_100000(prices):
    _, divisions, _chained = prices
    weights = divisions[divisions.function_code != 0].drop_duplicates("function_code")
    assert int(weights.weight_per_100000.sum()) == 100_000


def test_all_twelve_functions_present_plus_the_total(prices):
    _, divisions, _chained = prices
    assert set(divisions.function_code.unique()) == set(range(13))


def test_general_index_agrees_between_the_two_tables(prices):
    """13.6 and 13.7 are published separately and must tell the same story."""
    annual, divisions, _chained = prices
    for year in (2021, 2022, 2023):
        left = annual[(annual.year == year) & (annual.base_year == 2015)]["index"].iloc[0]
        right = divisions[(divisions.year == year) & (divisions.function_code == 0)]["index"]
        assert round(float(left), 1) == round(float(right.iloc[0]), 1), year


def test_cpi_reproduces_published_landmarks(prices):
    """Values read off the printed page by eye, as a guard against a plausible misparse."""
    annual, _divisions, _chained = prices
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
    annual, _divisions, _chained = prices
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
    tables, _, _, _subtotals = corpus
    from consumptiontn.config import YEARBOOK_FILE_IDS

    assert set(tables.edition) == set(YEARBOOK_FILE_IDS)


def test_catalogue_excludes_contents_page_entries(corpus):
    """Index entries match the heading pattern too, and near-duplicate every title.

    They are recognisable by their dotted leaders, and the catalogue is meant to hold
    the tables rather than the list that points at them.
    """
    tables, _, _, _subtotals = corpus
    leaders = tables[tables.table_title.str.contains(r"\.{4,}", regex=True, na=False)]
    assert leaders.empty, f"{len(leaders)} contents-page rows leaked into the catalogue"


def test_no_conflicting_cell_reaches_the_series(corpus):
    """The whole point of reconciliation: a cell two editions disagree about is dropped."""
    _, series, _, _subtotals = corpus
    assert "conflict" not in set(series.agreement)


def _year_column(series):
    """Cells whose column is a calendar year."""
    return series[series.column_label == series.year.astype(str)]


def _classification(series):
    """Cells whose column names a category rather than a period.

    School-year columns ("24-23") name a period too, so they belong with the years even
    though `column_label` keeps INS's notation rather than the calendar year. Lumping
    them in with the classification cells understates how often that group is
    uncorroborated, because a school-year table is a time series that later editions
    reprint.
    """
    is_year = series.column_label == series.year.astype(str)
    is_school = series.column_label.str.match(r"^\d{4}/\d{2}$").fillna(False)
    return series[~(is_year | is_school)]


def test_most_year_column_cells_are_corroborated_by_a_second_edition(corpus):
    """Editions overlap by five years, so corroboration should be the common case.

    Scoped to year-column tables on purpose. Those are the ones a later edition reprints,
    so a fall here would mean the title normalisation stopped matching the same table
    across editions -- silently disabling the corpus's main check. Measuring over every
    cell instead would let a flood of uncorroborable classification rows mask that.
    """
    _, series, _, _subtotals = corpus
    confirmed = (_year_column(series).agreement == "confirmed").mean()
    assert confirmed > 0.5, f"only {confirmed:.1%} of year-column cells are confirmed"


def test_classification_tables_are_honestly_marked_uncorroborated(corpus):
    """A single-year table cannot be cross-checked, and must not look as if it were.

    Table 1.4 in the 2023 edition is the population at 1.7.2023; the same table in the
    2019 edition is the population at 1.7.2019. Different data, so the cell is never
    printed twice and nothing corroborates it. `single source` is the correct label, and
    a reader filtering on `agreement` depends on it being applied.
    """
    _, series, _, _subtotals = corpus
    classification = _classification(series)
    assert not classification.empty
    single = (classification.agreement == "single source").mean()
    assert single > 0.8, f"only {single:.1%} of classification cells are marked single source"


def test_every_confirmed_cell_really_had_more_than_one_edition(corpus):
    _, series, _, _subtotals = corpus
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

    _, series, _, _subtotals = corpus
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
    _, series, _, _subtotals = corpus
    kinds = set(series.row_kind)
    assert kinds <= {"data", "aggregate"}
    assert (series.row_kind == "aggregate").sum() > 100


def test_coverage_accounts_for_every_catalogued_table(corpus):
    tables, _, coverage, _subtotals = corpus
    assert set(tables.table_title) <= set(coverage.title_fr)
    assert (coverage.values_kept <= coverage.values_read).all()


def test_years_are_plausible(corpus):
    _, series, _, _subtotals = corpus
    assert series.year.between(1900, 2030).all()


def test_classification_tables_carry_a_year_from_the_page(corpus):
    """Never dated from the edition's cover: table 13.8 in the 2023 edition covers
    2018-2022, so the cover year would be wrong by a year for every value in it."""
    _, series, _, _subtotals = corpus
    assert series.year.notna().all()


def test_column_labels_are_populated(corpus):
    _, series, _, _subtotals = corpus
    assert series.column_label.notna().all()
    assert (series.column_label.str.len() > 0).all()


def test_a_known_classification_table_matches_the_printed_page(corpus):
    """Table 1.8, fertility by governorate, 2023 edition: Tunis reads I.S.F 1.40 and
    T.G.F 41.6 on the page. Classification tables have no cross-edition check, so at
    least one is pinned against the paper."""
    _, series, _, _subtotals = corpus
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
    _, series, _, _subtotals = corpus
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
    _, series, _, _subtotals = corpus
    page = series[series.title_fr.str.contains("groupe d age genre", na=False)
                  & series.row_label.eq("Tunis") & series.column_label.eq("TOTAL")]
    assert not page.empty
    assert 535.4 in set(page.value)


def test_a_lone_dash_reads_as_zero(corpus):
    """INS's conventions table defines "-" as resultat rigoureusement nul: an observed
    zero, distinct from ">>" and "..." which mean unavailable. Table 1.13 records no
    still-births in Manouba for 2020 and 2021, printed as dashes."""
    _, series, _, _subtotals = corpus
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


# ------------------------------------------------ school years and inferred row labels

def test_school_years_are_told_apart_from_age_bands():
    """Both are written as reversed two-digit ranges, and only the span separates them.

    "24-23" is the 2023/24 school year; "04-00" is an age band. Reading an age-band
    header as years would turn a cross-section into a fake time series.
    """
    from consumptiontn.build_yearbook import _school_year_header

    # The label is canonicalised to the school year it names, so the two notations
    # editions use for the same year reconcile against each other.
    assert _school_year_header("24-23 23-22 22-21") == [
        ("2023/24", 2023), ("2022/23", 2022), ("2021/22", 2021)
    ]
    assert _school_year_header("04-00 09-05 14-10") is None
    assert _school_year_header("44-40 39-35") is None
    # The century turn: "00-99" is the 1999/2000 school year.
    assert _school_year_header("01-00 00-99") == [("2000/01", 2000), ("1999/00", 1999)]


def test_a_school_year_table_is_dated_without_a_year_on_the_page(corpus):
    """Table 2.1.3 counts schools by governorate with no calendar year printed anywhere.
    Tunis reads 190 schools for 24-23 and 188 for 20-19."""
    _, series, _, _subtotals = corpus
    schools = series[series.title_fr.str.contains("nombre d écoles par gouvernorat",
                                                  na=False, case=False)
                     & series.row_label.eq("Tunis")]
    by_year = dict(zip(schools.year, schools.value, strict=True))
    assert by_year[2023] == 190.0
    assert by_year[2019] == 188.0


def test_inferred_labels_are_flagged(corpus):
    """A label read from a neighbouring line is weaker evidence than one printed beside
    its numbers, so it is marked and a reader can drop the lot."""
    _, series, _, _subtotals = corpus
    assert series.label_inferred.any()
    assert not series.label_inferred.all(), "flag should mark a minority of rows"


def test_a_label_wrapped_around_its_numbers_is_reassembled(corpus):
    """Table 12.1.1 prints "Nombre d'abonnés au réseau de", then the numbers, then
    "téléphone fixe (en milliers)". Fixed-line and mobile share the first half, so
    stopping at the line above would give two different series the same name."""
    _, series, _, _subtotals = corpus
    phones = series[series.title_fr.str.contains("réseaux téléphoniques", na=False)
                    & series.year.eq(2023) & series.label_inferred]
    values = dict(zip(phones.row_label, phones.value, strict=True))
    # "telephone fixe", not merely "fixe": the density row is labelled
    # "Densite telephonique (fixe+mobile)" and would match a looser test.
    fixed = [label for label in values if "téléphone fixe" in label]
    mobile = [label for label in values if "téléphone mobile" in label]
    assert len(fixed) == 1 and len(mobile) == 1, list(values)
    assert values[fixed[0]] == 1863.0
    assert values[mobile[0]] == 16359.0


def test_an_ambiguous_inferred_label_is_dropped_rather_than_guessed():
    """Page 43 names two different teacher counts identically once the Arabic is
    stripped -- first cycle and second cycle. Nothing downstream could tell them apart,
    so the second is refused instead of overwriting or duplicating the first."""
    from consumptiontn.build_yearbook import edition_pages, parse_page

    rows, refused = parse_page(2023, 42, edition_pages(2023)[42])
    reasons = [r["reason"] for r in refused]
    assert any("not unique" in reason for reason in reasons), reasons
    inferred = {r["row_label"] for r in rows if r["label_inferred"]}
    assert len(inferred) == len({label for label in inferred})


def test_four_digit_school_years_resolve_to_the_same_year_as_two_digit():
    """Older editions write "2000-99" where newer ones write "00-99". Both are the
    1999/2000 school year and must resolve to 1999.

    They did not. The two-digit pattern missed the four-digit form, which fell through
    to the layout reader; that took its leading "2000" as a calendar year and dated
    every such column one year late. The two notations then disagreed by a year about
    the same printed figure.
    """
    from consumptiontn.build_yearbook import _school_year_header

    assert _school_year_header("2000-99 2001-00") == [("1999/00", 1999), ("2000/01", 2000)]
    assert _school_year_header("00-99 01-00") == [("1999/00", 1999), ("2000/01", 2000)]
    # Four-digit age-band-like spans are still refused.
    assert _school_year_header("2004-00 2009-05") is None


def test_the_two_school_year_notations_corroborate_each_other(corpus):
    """Canonicalising the label is what lets them: keyed on the printed token, two
    editions of the same figure would never have been compared."""
    _, series, _, _subtotals = corpus
    enrolment = series[series.title_fr.eq("population scolaire totale du 1er cycle de 8")
                       & series.row_label.eq("Sidi Bouzid")]
    by_year = enrolment.set_index("year")
    assert by_year.loc[2000, "value"] == 64235.0
    assert by_year.loc[2000, "n_editions"] >= 3
    assert by_year.loc[2000, "agreement"] == "confirmed"
    # One row per year: the notations merged rather than double-counting.
    assert not enrolment.year.duplicated().any()


def test_school_year_labels_are_canonical(corpus):
    _, series, _, _subtotals = corpus
    school = series[series.column_label.str.match(r"^\d{4}/\d{2}$").fillna(False)]
    assert not school.empty
    # The canonical form always names the year it starts in.
    starts = school.column_label.str.slice(0, 4).astype(int)
    assert (starts == school.year).all()


# ------------------------------------------------------------------- stacked panels

def test_repeated_row_labels_are_split_by_their_panel_heading():
    """Table 14.1 prints the twelve months twice, once per panel.

    Keying a row on its bare label kept whichever panel came first and dropped the
    other, so the whole exports half of the monthly trade table was missing from the
    corpus while looking complete.
    """
    from consumptiontn.build_yearbook import _qualify_panels

    entries = [
        {"label": "I – Importations", "values": [10.0], "provisional": False, "inferred": False},
        {"label": "Janvier", "values": [1.0], "provisional": False, "inferred": False},
        {"label": "II – Exportations", "values": [20.0], "provisional": False, "inferred": False},
        {"label": "Janvier", "values": [2.0], "provisional": False, "inferred": False},
    ]
    kept, refused = _qualify_panels(entries)
    assert refused == []
    by_label = {entry["label"]: entry["values"][0] for entry in kept}
    assert by_label["Importations / Janvier"] == 1.0
    assert by_label["Exportations / Janvier"] == 2.0


def test_a_panel_heading_carrying_no_numbers_still_names_its_panel():
    """Table 13.2 opens each branch with a line of text and no values at all."""
    from consumptiontn.build_yearbook import _qualify_panels

    entries = [
        {"label": "Industries agro-alimentaires", "values": None,
         "provisional": False, "inferred": False},
        {"label": "Janvier", "values": [154.6], "provisional": False, "inferred": False},
        {"label": "Mines", "values": None, "provisional": False, "inferred": False},
        {"label": "Janvier", "values": [177.0], "provisional": False, "inferred": False},
    ]
    kept, refused = _qualify_panels(entries)
    assert refused == []
    assert {entry["label"] for entry in kept} == {
        "Industries agro-alimentaires / Janvier", "Mines / Janvier"}
    # The heading is scaffolding, not an observation.
    assert all(entry["values"] is not None for entry in kept)


def test_a_repeat_with_no_heading_is_refused_rather_than_silently_halved():
    from consumptiontn.build_yearbook import _qualify_panels

    entries = [
        {"label": "Janvier", "values": [1.0], "provisional": False, "inferred": False},
        {"label": "Janvier", "values": [2.0], "provisional": False, "inferred": False},
    ]
    kept, refused = _qualify_panels(entries)
    # Both copies go, not one: keeping either would put an arbitrary half of the row
    # under a label that names the whole of it.
    assert kept == []
    assert {reason for _, reason in refused} == {
        "row label repeats with no panel heading above it"}
    assert len(refused) == 2


def test_panel_names_drop_the_enumerator_so_editions_agree():
    """Editions write "I - Importations", "I. Importations" and "A. Importations".

    Qualifying with the enumerator attached would put one printed series into three,
    and each would then be single-sourced instead of corroborating the others.
    """
    from consumptiontn.build_yearbook import _qualify_panels

    def january(opener):
        entries = [
            {"label": opener, "values": [10.0], "provisional": False, "inferred": False},
            {"label": "Janvier", "values": [1.0], "provisional": False, "inferred": False},
            {"label": "Mars", "values": [3.0], "provisional": False, "inferred": False},
            {"label": "B. Exportations", "values": [20.0], "provisional": False, "inferred": False},
            {"label": "Janvier", "values": [2.0], "provisional": False, "inferred": False},
            {"label": "Mars", "values": [4.0], "provisional": False, "inferred": False},
        ]
        kept, _ = _qualify_panels(entries)
        # The opener keeps the label it was printed with -- inventing a common one for
        # it would merge rows on a guess. What has to agree is the labels it qualifies.
        return {entry["label"] for entry in kept if " / " in entry["label"]}

    assert (january("I – Importations") == january("I. Importations")
            == january("A. Importations"))
    assert "Importations / Janvier" in january("I. Importations")


def test_both_trade_panels_survive_into_the_corpus(corpus):
    _, series, _, _subtotals = corpus
    trade = series[series.title_fr.str.contains("mensuelle des échanges", na=False)]
    months = trade[trade.row_label.str.endswith("Janvier")]
    panels = set(months.row_label.str.rsplit(" / ", n=1).str[0])
    assert {"Importations", "Exportations"} <= panels

    # The printed page: table 14.1 of the 2015 edition, January 2011.
    def value(panel):
        row = months[months.row_label.eq(f"{panel} / Janvier") & months.year.eq(2011)]
        return float(row.value.iloc[0])

    assert value("Importations") == pytest.approx(2289.2)
    assert value("Exportations") == pytest.approx(1731.2)


def test_monthly_trade_is_corroborated_across_editions(corpus):
    """Every edition reprints five years of this table, so most cells have witnesses.

    Measured over the cells that *have* a second witness, not over all of them. Merging
    the title variants pushed this series back to 1995 and out to 2023, and the years at
    either end are printed by one edition only -- no corroboration is possible there, and
    counting those against the parser would penalise the series for being longer.
    """
    _, series, _, _subtotals = corpus
    trade = series[series.title_fr.str.contains("mensuelle des échanges", na=False)]
    months = trade[trade.row_label.str.contains(" / ")]
    assert months.year.min() <= 1995 and months.year.max() >= 2023

    witnessed = months[months.n_editions > 1]
    confirmed = witnessed.agreement.eq("confirmed").mean()
    assert confirmed > 0.85, f"only {confirmed:.0%} of witnessed cells are confirmed"

    # The uncorroborated cells are the ends of the series and nothing else: a single
    # source in the middle would mean an edition had been missed.
    alone = set(months[months.n_editions == 1].year)
    assert alone <= {1995, 1996, 1997, 2023}, f"single-source years inside the run: {alone}"


# ------------------------------------------------- where the values begin on a row

def test_a_label_carrying_digits_does_not_swallow_them():
    """The commonest reason a row was refused: the label has a number in it.

    "20 a 24 ans" starts the numeric region inside the label, and the label's own words
    are then left over among the numbers. 16,040 rows across the corpus were refused for
    this, most of them real data.
    """
    from consumptiontn.build_yearbook import split_row

    label, values, _ = split_row("  20 à 24 ans          6 429       6 658  ")
    assert label == "20 à 24 ans"
    assert values == [6429.0, 6658.0]


def test_a_hyphen_in_a_region_name_is_not_read_as_a_nil():
    from consumptiontn.build_yearbook import split_row

    label, values, _ = split_row("Nord - Ouest      3 508     2 298    5 806 ")
    assert label == "Nord - Ouest"
    assert values == [3508.0, 2298.0, 5806.0]


def test_one_space_is_enough_of_a_gutter():
    """Demanding a wide gutter refused rows that set the label off with a single space."""
    from consumptiontn.build_yearbook import split_row

    label, values, _ = split_row("Bibliothèques pub pour enfant 1 542 877 1 443 367")
    assert label == "Bibliothèques pub pour enfant"
    assert values == [1542877.0, 1443367.0]


def test_the_split_never_falls_inside_a_token():
    """A footnote marker glued to the label must not become a value.

    Reading "Taux d'endettement5 52.3 48.1" as the label "Taux d'endettement" and a
    first value of 5 shifts every column by one, which is the failure this parser was
    written to refuse.
    """
    from consumptiontn.build_yearbook import split_row

    label, values, _ = split_row("Taux d'endettement5 52.3   48.1   44.0 ")
    assert label == "Taux d'endettement5"
    assert values == [52.3, 48.1, 44.0]
    # parse_page then refuses it outright for the label ending in a digit.


def test_a_row_whose_only_value_is_a_nil_still_reads():
    """A lone dash is an observed zero, and used to be refused when it came first."""
    from consumptiontn.build_yearbook import split_row

    label, values, _ = split_row("  Le Kef                       -   ")
    assert label == "Le Kef"
    assert values == [0.0]


def test_residue_among_the_numbers_still_refuses_the_row():
    """The strictness the boundary rule had to preserve."""
    from consumptiontn.build_yearbook import split_row

    # An ellipsis standing in for a missing year cannot be read as a value, so no start
    # position spans the whole run and the row comes out too short to fill its columns.
    assert split_row("  Céréales      1 013.5   ...   1 204.7 ")[1] == [1204.7]
    # A footnote digit glued to the label leaves the label ending in a digit, which is
    # refused outright rather than allowed to shift every column left.
    assert split_row("  Taux d'endettement5 52.3   54.1 ")[0].endswith("5")
    # A page footer carrying the edition year survives this far -- the region checked
    # ends at the last number, so the rule underlining it is not residue -- but it
    # yields a single value and so cannot fill a table of several year columns.
    footer = split_row("INS - Annuaire Statistique de la Tunisie 2001______")
    assert footer is not None and len(footer[1]) == 1


# --------------------------------------------- a year header with one extra column

def test_a_trailing_weight_column_does_not_refuse_the_table(corpus):
    """Table 13.7 prints three years of the price index and then a weight.

    Every row yielded one value too many and the whole table was refused -- 612 rows
    across ten editions, which is the consumer price index by product group for 2012 to
    2023. The weight is a constant, not a point in a series, so it is dropped.
    """
    _, series, _, _subtotals = corpus
    rows = series[series.table_number.eq("13.7")]
    assert not rows.empty, "table 13.7 is being refused again"
    assert rows.year.between(2012, 2023).all()

    # Read off the printed page: 2014 edition, food and non-alcoholic drinks.
    food = rows[rows.row_label.str.startswith("Produits alimentaires")
                & rows.year.eq(2014)]
    assert float(food.value.iloc[0]) == pytest.approx(128.9)


def test_the_trailing_column_rule_needs_a_label_to_the_right():
    """It must not fire on a word wrapped down from the title."""
    from consumptiontn.build_yearbook import _trailing_column

    header = "                    2014    2013      2012"
    beyond = " " * 46 + "Pondération"       # starts past where 2012 does, at column 38
    assert _trailing_column([header, beyond], 0, header) == 1
    # A line starting to the left of the years is a wrapped title, not a column.
    assert _trailing_column([header, "  à la consommation familiale"], 0, header) == 0
    # Nor is anything carrying digits of its own.
    assert _trailing_column([header, " " * 46 + "Base 100"], 0, header) == 0


def test_a_weight_column_beside_the_years_is_read_too(corpus):
    """Table 13.4 sets its weight column on the header line: "2023 2022 2021 Pondération".

    ``_year_header`` allows one caption word at each end, so it drops that token and the
    column becomes invisible; every row then came out one value too wide and the table
    was refused whole -- 515 rows across fifteen editions, which is annual consumer price
    *inflation* by product group, the series the price index alone does not give.
    """
    _, series, _, _subtotals = corpus
    rows = series[series.table_number.eq("13.4")]
    assert not rows.empty, "table 13.4 is being refused again"

    # Read off the printed page: 2023 edition, bread and cereals, base 2015 = 100.
    bread = rows[rows.row_label.eq("Pain et céréales")]
    printed = {2023: 6.8, 2022: 7.3, 2021: 2.7}
    for year, expected in printed.items():
        got = bread[bread.year.eq(year)].value
        assert float(got.iloc[0]) == pytest.approx(expected), year


def test_the_header_side_rule_will_not_fire_on_a_footnote_or_a_base(corpus):
    """The label beside the years has to be a word, and has to come after them."""
    from consumptiontn.build_yearbook import _trailing_column

    header = "                 2023      2022       2021     Pondération"
    assert _trailing_column([header], 0, header) == 1
    # A base statement carries digits, so it is not a column name.
    assert _trailing_column(["   2023   2022   2021   Base 100"], 0,
                            "   2023   2022   2021   Base 100") == 0
    # A caption to the *left* of the years is the row-label heading, not a column.
    assert _trailing_column(["   Gouvernorat  2023   2022   2021"], 0,
                            "   Gouvernorat  2023   2022   2021") == 0
    # A footnote marker is a single character, well short of a word.
    assert _trailing_column(["   2023   2022   2021  a"], 0, "   2023   2022   2021  a") == 0


def test_the_trailing_column_goes_before_a_wrapped_label_is_recovered(corpus):
    """Order matters: the trim has to come first or the widest rows are lost silently.

    A row whose label is printed above and below its numbers is recovered only when the
    values already match the column count. Trimming the weight afterwards left those rows
    one value wide, so the headline row of every one of these tables -- "Produits
    alimentaires et boissons non alcoolisées" -- was dropped without being refused.
    """
    _, series, _, _subtotals = corpus
    rows = series[series.table_number.eq("13.4")]
    headline = rows[rows.row_label.eq(
        "Produits alimentaires et boissons non alcoolisées") & rows.year.eq(2023)]
    assert not headline.empty, "the wrapped headline row is being dropped again"
    assert float(headline.value.iloc[0]) == pytest.approx(12.3)


def test_a_decimal_broken_by_a_space_is_repaired_not_refused(corpus):
    """``4 526 .2`` is 4526.2, and refusing it cost 779 rows across the corpus.

    This was previously read as damage and thrown away, on the reasoning that a broken
    number could not be told from two numbers. The corpus settles it: the repaired values
    are corroborated by editions that print the same figures cleanly. Male population in
    1999 comes to 4 768.7 thousand here and three separate editions agree, and none of
    the repaired cells lands in conflict. A wrong reading could not do that.
    """
    from consumptiontn.build_yearbook import split_row

    label, values, _ = split_row("  Sexe masculin      4 526 .2   4 590 .3   4 647 .0 ")
    assert label == "Sexe masculin"
    assert values == [4526.2, 4590.3, 4647.0]

    # A gap wide enough to be a column gutter is not closed up, so the row stays short
    # and is refused on its width rather than silently glued together.
    assert split_row("  Ventes      4 526     .2   4 590 ")[1] == [4590.0]

    _, series, _, _subtotals = corpus
    men = series[series.row_label.eq("Sexe masculin")
                 & series.title_fr.str.startswith("principales caract")]
    corroborated = men[men.year.eq(1999)]
    assert float(corroborated.value.iloc[0]) == pytest.approx(4768.7)
    assert int(corroborated.n_editions.iloc[0]) >= 3
    assert "conflict" not in set(men.agreement)


# --------------------------------------------- one table under several printed titles

def test_a_title_that_gained_words_is_still_the_same_table(corpus):
    """INS re-worded "evolution des offres d emploi" twice between 2001 and 2023.

    Keyed on the title as printed, one 29-year governorate panel was stored as three
    fragments of six to ten years, and the years two editions shared stopped confirming
    each other. Merged, Tunis runs 1995 to 2023 with 26 of those years printed by two or
    more editions.
    """
    _, series, _, _subtotals = corpus
    tunis = series[series.title_fr.str.contains("offres d emploi", na=False)
                   & series.row_label.eq("Tunis")]
    years = sorted(tunis.year)
    assert years == list(range(1995, 2024)), "the fragments are not being joined"
    assert len(years) == len(set(years)), "a year is counted twice"
    assert (tunis.n_editions > 1).sum() >= 25
    # Read off the 2022 edition's page 111.
    printed = {2022: 3497, 2021: 3815, 2020: 2730, 2019: 9987, 2018: 10110}
    for year, expected in printed.items():
        assert float(tunis[tunis.year.eq(year)].value.iloc[0]) == expected, year


def test_two_tables_that_merely_share_a_stem_are_left_apart():
    """The check that stops the merge being a guess.

    "nombre de salles de sports" is a prefix of "nombre de salles de sports privées" and
    the two list the same 24 governorates, so nothing about the wording or the row labels
    separates them. The numbers do: they agree on 2 of 384 shared cells.
    """
    import pandas as pd

    from consumptiontn.build_yearbook import canonical_titles

    frame = pd.DataFrame({
        "chapter": "2",
        "title_fr": (["nombre de salles de sports"] * 6
                     + ["nombre de salles de sports privées"] * 6),
        "row_label": ["Tunis", "Ariana", "Sfax"] * 4,
        "column_label": ["2019", "2019", "2019", "2020", "2020", "2020"] * 2,
        "year": [2019, 2019, 2019, 2020, 2020, 2020] * 2,
        "value": [140.0, 96, 122, 145, 99, 126,     # public halls
                  12.0, 8, 11, 13, 9, 12],          # private ones, nothing like them
    })
    canonical = canonical_titles(frame)
    assert canonical["nombre de salles de sports"] != canonical[
        "nombre de salles de sports privées"]


def test_a_title_variant_that_agrees_is_merged():
    """The same table, re-worded, reporting the same numbers for the years it shares."""
    import pandas as pd

    from consumptiontn.build_yearbook import canonical_titles

    shared = {"row_label": ["Tunis", "Ariana", "Sfax"] * 2,
              "column_label": ["2019"] * 3 + ["2020"] * 3,
              "year": [2019] * 3 + [2020] * 3,
              "value": [140.0, 96, 122, 145, 99, 126]}
    frame = pd.DataFrame({"chapter": "6",
                          "title_fr": ["evolution des placements"] * 6
                                      + ["evolution des placements par gouvernorat"] * 6,
                          **{k: v * 2 for k, v in shared.items()}})
    canonical = canonical_titles(frame)
    assert canonical["evolution des placements"] == canonical[
        "evolution des placements par gouvernorat"]
    # The longer, more explicit wording is the one kept.
    assert canonical["evolution des placements"] == (
        "evolution des placements par gouvernorat")


# ------------------------------------------- the caption that says which half of a table

def test_the_sex_a_population_table_describes_is_kept(corpus):
    """Tables 1.2, 1.3 and 1.4 are one table printed three times, for men, for women and
    for both. The sex is printed beside the row-label heading and nowhere else, so once it
    was dropped the three were indistinguishable -- their titles differ only by where each
    was truncated. Two editions printing different sexes were then reconciled against each
    other and one of them thrown away.
    """
    _, series, _, _subtotals = corpus
    captions = set(series[series.panel.ne("")].panel)
    assert captions == {"Masculin", "Féminin", "Masculin et Féminin"}

    population = series[series.title_fr.str.startswith("estimation de la population")]
    assert population.panel.nunique() >= 3


def test_the_two_sexes_add_up_to_the_both_sexes_panel(corpus):
    """The check that proves the captions were read the right way round.

    Nothing tells the parser what "Masculin" means. If the three panels had been attached
    to the wrong pages, men plus women would not come to the printed total for both -- and
    over Tunis's 20-24 age band across seven years, they do, to the last decimal.
    """
    _, series, _, _subtotals = corpus
    cells = series[series.panel.ne("") & series.row_label.eq("Tunis")
                   & series.column_label.eq("24-20")]
    wide = cells.pivot_table(index="year", columns="panel", values="value")
    wide = wide.dropna()
    assert len(wide) >= 5, "too few years carry all three panels to check"
    both = wide["Masculin"] + wide["Féminin"]
    agree = (both - wide["Masculin et Féminin"]).abs() <= 0.15
    assert agree.mean() > 0.8, wide[~agree].to_dict()


def test_a_caption_is_not_taken_from_a_wrapped_heading():
    """"Année Judiciaire" and "Produit Intérieur Brut" wrap onto the heading line and
    continue straight after the first word. A caption for the page sits far to its
    right, and that gap is the only thing separating the two."""
    from consumptiontn.build_yearbook import _panel_caption

    wide = ["Gouvernorat" + " " * 20 + "Masculin et Féminin", "  44-40   39-35   34-30"]
    assert _panel_caption(wide, 1) == "Masculin et Féminin"
    # The same words set immediately after the heading are its own continuation.
    assert _panel_caption(["Gouvernorat Masculin", "  44-40   39-35"], 1) == ""
    # An enumerator carries no lower-case letter and is not a caption.
    assert _panel_caption(["Catégorie" + " " * 20 + "III", "  44-40   39-35"], 1) == ""
    # Nor is a line that does not open with a row-label heading at all.
    assert _panel_caption(["Zaghouan" + " " * 20 + "Masculin", "  44-40"], 1) == ""


def test_separating_the_sexes_removed_false_revisions(corpus):
    """A cell whose two printings differ is a revision only if they are the same cell.

    Before the caption was kept, a man's figure and a woman's were reconciled against each
    other and the difference recorded as INS revising the number. 1,733 cells were marked
    that way.
    """
    _, series, _, _subtotals = corpus
    population = series[series.title_fr.str.startswith("estimation de la population")]
    assert (population.agreement == "revised").mean() < 0.15


# --------------------------------------------------- the region rows against their parts

def test_regions_agree_with_the_governorates_they_are_made_of(corpus):
    """The validator that needs no outside source and runs over the whole corpus.

    Many tables print the seven grandes régions alongside the 24 governorates, so each
    region row is a sum the corpus can check against its own parts. 5,847 such checks are
    available and 98.96% of them hold.
    """
    _, _series, _coverage, subtotals = corpus
    additive = subtotals[subtotals.additive]
    assert len(additive) > 10_000, "far fewer checks than the corpus should offer"
    assert additive.agrees.mean() > 0.98, additive[~additive.agrees].head().to_dict()


def test_the_region_disagreements_stay_concentrated(corpus):
    """A disagreement spreading across the corpus would mean the parser was drifting.

    They do not spread: over half sit in population by age group in two editions, 2009
    and 2018, and the rest in the births-by-place-of-delivery tables. All are *region*
    rows contradicting their parts rather than governorate rows, which is why the
    governorate panel built from the same corpus passes its own national-total check.
    """
    _, _series, _coverage, subtotals = corpus
    off = subtotals[subtotals.agrees == False]  # noqa: E712
    assert not off.empty, "the check has stopped finding the faults it used to"
    assert len(off) < 200, f"{len(off)} disagreements is more than this has ever found"
    population = off.title_fr.str.startswith("estimation de la population")
    births = off.title_fr.str.startswith("naissances")
    assert (population | births).all(), sorted(set(off[~(population | births)].title_fr))
    assert population.sum() >= 50


def test_a_rate_is_not_expected_to_add_up(corpus):
    """A region's fertility rate is its governorates' mean, not their sum.

    Checking those would report 1,681 disagreements that are arithmetic working properly.
    Wording catches most of them; the rest are caught from the numbers, because a column
    can be an average inside a table of counts -- "Accouch. assisté" is the percentage
    assisted, sitting among counts of births.
    """
    _, _series, _coverage, subtotals = corpus
    rates = subtotals[~subtotals.additive]
    assert len(rates) > 1_000
    assert rates.agrees.isna().all(), "a rate must not be counted as passing or failing"
    assert rates.title_fr.str.contains("naissances selon le lieu").any()


def test_both_sides_of_a_disagreement_are_published(corpus):
    """A sum cannot say which side is wrong, so neither is dropped."""
    _, _series, _coverage, subtotals = corpus
    assert {"parts_sum", "parts_mean", "printed", "gap", "agrees"} <= set(subtotals.columns)
    off = subtotals[subtotals.agrees == False]  # noqa: E712
    assert (off.parts_sum.notna() & off.printed.notna()).all()


def test_a_region_is_matched_however_it_is_spelt():
    """INS sets a region five ways and a governorate two; both sides are folded."""
    from consumptiontn.build_yearbook import _fold_label

    assert _fold_label("Nord - Est") == _fold_label("Nord-Est") == _fold_label("Nord Est")
    assert _fold_label("SidiBouzid") == _fold_label("Sidi Bouzid")
    assert _fold_label("Béja") == _fold_label("Beja")
    assert _fold_label("Nord-Est") != _fold_label("Nord-Ouest")


# ------------------------------------------------------ lines that are not rows at all

def test_a_unit_statement_is_not_a_row(corpus):
    """"Unité : Le Nombre   Année" carries the year beside it and reads as -2001."""
    _, series, _coverage, _subtotals = corpus
    assert not series.row_label.str.match(r"^\s*Unit[ée]\s*:", na=False).any()
    assert not series.row_label.str.contains("STATISTIQUES TUNISIE", na=False).any()


def test_the_rule_does_not_catch_a_real_label():
    """Words that merely begin the same way are data: a table of thermal springs has
    "Sources thermales" down its side, and a sports table has "Baseball"."""
    from consumptiontn.build_yearbook import NOT_A_ROW

    for caption in ("Unité : Le Nombre", "Source : INS", "Base (2015 = 100)",
                    "123   STATISTIQUES TUNISIE   ANNUAIRE STATISTIQUE"):
        assert NOT_A_ROW.search(caption), caption
    for label in ("Unités de production", "Sources thermales", "Baseball",
                  "Tunis", "Nord-Ouest"):
        assert not NOT_A_ROW.search(label), label
