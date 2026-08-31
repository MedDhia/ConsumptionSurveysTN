"""A governorate panel, assembled from the yearbook corpus.

``tn_yearbook_series`` already carries this data, but reaching it means filtering
174,473 rows on a French title you would have to know in advance, and then working out
whether a given table's columns are years or something else. This module does that once:
one row per governorate, year and indicator, under English names, for the tables whose
meaning was checked against the printed page.

Thirty of them are plain governorate-by-year series and carry no ``breakdown``. The
thirty-first is population by age group, which is also printed once per sex -- and which
used to be excluded outright, because the sex is set as a caption beside the row-label
heading and was dropped on extraction, leaving three near-identically titled tables that
could not be told apart. The corpus keeps that caption now, so it can be read: men plus
women come to the figure printed for both in 93% of the cells that carry all three, and
the cells where they do not are refused.

**Every name here was read off a page, not inferred from the title.** The titles the
corpus carries are truncated and merged across editions, and several are actively
misleading: "evolution des placements realises en tunisie par categorie professionnelle"
is a governorate table, the profession wording surviving from an edition that also broke
it down that way. "nombre de maisons de jeunes" is printed "maisons des jeûnnes" in the
source. Guessing from either would have produced a plausible, wrong label.

**What is deliberately left out**, and why, because a governorate panel that quietly mixed
these in would be worse than a smaller one:

* *Paramedical staff by grade* (table 4.4) has its grade labels fused with the year --
  "Année 2010 Inﬁrmiers" -- so the breakdown cannot be read cleanly.
* *Secondary establishments* (table 2.14) crosses the period with a measure
  ("1999 - 1998 Etab.", "2001 2000- Class- Elèves") in more variants than can be parsed
  back apart.
* *"Nombre de salles par gouvernorat"* shares a page with the cinema-attendance table and
  which of the two it belongs to could not be settled from the page.
* *The three justice tables* (divorces, cases filed, cases disposed) look like governorate
  tables and are not: their rows are courts of first instance. Grombalia is a court in
  Nabeul, and Tunis is split into two, so "Tunis" there is one court rather than the
  governorate. The national-total check is what found this -- the 24 names that look like
  governorates sum to 86% of the printed total, every year, by construction.

The check that runs over the whole panel is the printed national total: most of these
tables end with a "Total" row, and the 24 governorates have to sum to it. That catches a
governorate read from the wrong column, which is the failure mode a panel like this would
otherwise hide.
"""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

# As the yearbooks spell them. Manouba appears without its article and Le Kef with one;
# both are the source's own forms and are kept so a reader can trace a row back.
GOVERNORATES: tuple[str, ...] = (
    "Ariana", "Béja", "Ben Arous", "Bizerte", "Gabès", "Gafsa", "Jendouba", "Kairouan",
    "Kasserine", "Kébili", "Le Kef", "Mahdia", "Manouba", "Médenine", "Monastir",
    "Nabeul", "Sfax", "Sidi Bouzid", "Siliana", "Sousse", "Tataouine", "Tozeur",
    "Tunis", "Zaghouan",
)

# title_fr in tn_yearbook_series -> (indicator, unit). Two titles map to `marriages`:
# INS re-worded the table in 2009 and the two halves share no year, so the value check
# that merges title variants has nothing to compare and correctly leaves them apart.
# They are the same table, and naming them by hand is how they are joined.
INDICATORS: dict[str, tuple[str, str]] = {
    # Chapter 2 -- education and culture
    "evolution du reseau des bibliotheques par categorie et par gouvernorat":
        ("public_libraries", "libraries"),
    "evolution de la capacite des bibliotheques publiques par categorie et par":
        ("library_capacity", "seats"),
    "evolution des lecteurs par categorie de bibliotheques et par gouvernorat":
        ("library_readers", "readers"),
    "evolution des abonnes par categorie de bibliotheques et par gouvernorat":
        ("library_subscribers", "subscribers"),
    "evolution des fonds de livres par categorie de bibliotheques et par gouvernorat":
        ("library_book_stock", "books"),
    "evolution des livres prêtés par catégorie de 6":
        ("library_books_lent", "books"),
    "nombre d écoles par gouvernorat du 1er cycle de 3":
        ("primary_schools", "schools"),
    "nombre de locaux - classes par gouvernorat 4":
        ("primary_classrooms", "classrooms"),
    "personnel enseignant par gouvernorat du 1er cycle de 5":
        ("primary_teachers", "teachers"),
    "population scolaire totale du 1er cycle de 8":
        ("primary_pupils", "pupils"),
    "population scolaire totale du 2ème cycle de l enseignement 13":
        ("secondary_pupils", "pupils"),
    "nombre de salles de cinéma par gouvernorat":
        ("cinema_screens", "screens"),
    # Chapter 1 and 2 -- vital statistics
    "evolution des morts-nés par gouvernorat de déclaration 13.1":
        ("stillbirths", "stillbirths"),
    "mariages contractes par gouvernorat de declaration":
        ("marriages", "marriages"),
    "mariages contractés par gouvernorat de déclaration 14":
        ("marriages", "marriages"),
    "estimation de la population par gouvernorat au 1er juillet 5.1":
        ("population", "thousands"),
    # Chapter 3 -- youth and sport
    "evolution des nombres d abonnés aux maisons des 1":
        ("youth_centre_members", "members"),
    "nombre de maisons de jeûnes par gouvernorat 9":
        ("youth_centres", "centres"),
    "nombre de salles de sports par gouvernorat 7":
        ("sports_halls", "halls"),
    "nombre de salles de sports privées par gouvernorat 10.3":
        ("private_sports_halls", "halls"),
    "répartition des abonnés aux salles de sport privées 6":
        ("private_gym_members", "members"),
    "nombre de stades gazonnés par gouvernorat 8.3":
        ("grass_pitches", "pitches"),
    "nombre des centres de camping par gouvernorat 13":
        ("camping_centres", "centres"),
    "nombre des complexes de jeunesse par gouvernorat 12.3":
        ("youth_complexes", "complexes"),
    # Chapter 6 -- employment
    "evolution des offres d emploi reçues par gouvernorat 7":
        ("job_offers", "offers"),
    "evolution des placements realises en tunisie par categorie professionnelle":
        ("job_placements", "placements"),
    # Chapter 11 -- road traffic
    "evolution du nombre des tués par gouvernorat et par mois 8":
        ("road_deaths", "deaths"),
    "evolution du nombre des blessés par gouvernorat et par mois 7":
        ("road_injuries", "injuries"),
    # Chapter 12 -- communications
    "evolution du nombre d abonnés au réseau téléphonique fixe 2":
        ("fixed_line_subscribers", "subscribers"),
    "montant des mandats émis par l étranger et payés en tunisie par 7":
        ("money_orders_from_abroad", "dinars"),
    # Chapter 15 -- money and banking
    "evolution du réseau bancaire par gouvernorat 2.15":
        ("bank_branches", "branches"),
}

# Population by age is the one table here whose columns are not the period, so it carries
# a `breakdown`. It is also printed once per sex, and the sex lives in a caption beside the
# row-label heading that the corpus now keeps as `panel`; before that it was lost and the
# three printings were indistinguishable, which is why this table used to be excluded.
BY_SEX: dict[str, str] = {
    "Masculin": "population_male",
    "Féminin": "population_female",
    "Masculin et Féminin": "population_all",
}

# INS writes an age band backwards, high end first: "24-20" is 20 to 24. The open-ended
# band is set several ways across editions -- "80 ans &+", "80ans &+", and once with the
# Arabic still attached -- so it is matched on its number rather than its wording.
AGE_BAND = re.compile(r"^(\d{2})-(\d{2})$")
OPEN_BAND = re.compile(r"\b80\s*ans?\s*&")


def _age_band(column: str) -> str | None:
    """The age band a column stands for, written low end first."""
    band = AGE_BAND.match(str(column))
    if band:
        return f"{band.group(2)}-{band.group(1)}"
    return "80+" if OPEN_BAND.search(str(column)) else None


# Tables that carry governorate rows and are left out on purpose. Kept here rather than
# only in prose so the decision is visible from the code and testable.
EXCLUDED: dict[str, str] = {
    "répartition du personnel 4":
        "paramedical staff: grade labels are fused with the year",
    "nombre d établissements du 2ème cycle de l enseignement de 14":
        "secondary establishments: the column crosses period with measure in too many forms",
    "nombre de salles par gouvernorat":
        "shares a page with the cinema-attendance table; which one it is could not be settled",
    "divorces prononcés par les tribunaux de 1ère instance 18":
        "rows are courts of first instance, not governorates",
    "affaires enrolées devant les tribunaux de 1ere instance en matière 8":
        "rows are courts of first instance, not governorates",
    "affaires traitées devant les tribunaux de 1ere instance en matière 7":
        "rows are courts of first instance, not governorates",
}

# A national total the panel has to reproduce is only as good as its tolerance. INS rounds
# governorate figures independently of the total it prints, so the sum is allowed to drift
# by a little; a column read from the wrong place misses by far more than this.
TOTAL_TOLERANCE = 0.02
TOTAL_FLOOR = 5.0

# Above this share of indicator-years failing the total, the fault is in the extraction
# rather than in a handful of printed cells, and the build stops instead of publishing.
MAX_REFUSED_SHARE = 0.02


def _fold(name: str) -> str:
    """A governorate name reduced to what all its printings have in common."""
    bare = unicodedata.normalize("NFKD", str(name))
    return re.sub(r"[^a-z]", "", "".join(
        ch for ch in bare if not unicodedata.combining(ch)).lower())


FOLDED = {_fold(name): name for name in GOVERNORATES}

# pdftotext emits the Arabic side's digits on lines of their own, and one occasionally
# lands at the head of a governorate's row: "7        Ariana   86  86  85  85  83" in the
# 2005 edition's table 3.3. The values are not disturbed -- the row still yields exactly
# as many as there are columns, which is what a leaked value would break -- so the digit is
# stripped rather than the row refused. Without this, one governorate silently drops out of
# an indicator, which is how Sidi Bouzid ("SidiBouzid", set without its space) was missing
# from the money-order series.
LEADING_DIGITS = re.compile(r"^\d+\s+")


def _governorate(label: str) -> str | None:
    """The governorate a printed row label stands for, or None if it is not one."""
    return FOLDED.get(_fold(LEADING_DIGITS.sub("", str(label))))


def _period_column(frame: pd.DataFrame) -> pd.Series:
    """True where a row's column label is the period the row is dated to.

    A year column says "2019"; a school-year column says "2018/19" or, reversed, "19-18".
    Either way the value already carries that year, so there is nothing left to record as
    a breakdown. Anything else -- an age band, a measure -- means the table is more than a
    governorate-by-year series, and those tables are excluded rather than flattened.
    """
    label = frame.column_label.astype(str)
    plain = label.str.fullmatch(r"(19|20)\d\d")
    school = label.str.extract(r"^(?:(\d{4})[/-]\d{2}|(\d{2})-(\d{2}))$")
    starts = pd.to_numeric(school[0], errors="coerce")
    # "19-18" is 2018/19 written backwards: the later half is printed first.
    reversed_form = pd.to_numeric(school[2], errors="coerce")
    starts = starts.fillna(reversed_form + 2000).fillna(reversed_form + 1900)
    return plain | starts.eq(frame.year)


def build(series: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """One row per governorate, year and indicator, plus the years that were refused."""
    if series is None:
        series = pd.read_csv("data/processed/tn_yearbook_series.csv")

    known = set(INDICATORS)
    rows = series[series.title_fr.isin(known) & series.row_kind.eq("data")].copy()
    rows["governorate"] = rows.row_label.map(_governorate)
    rows = rows[rows.governorate.notna()]
    if rows.empty:
        raise RuntimeError("no governorate rows found; has tn_yearbook_series moved?")

    missing = known - set(rows.title_fr)
    if missing:
        raise RuntimeError(f"tables named here but absent from the corpus: {sorted(missing)}")

    # Only the plain governorate-by-year shape is carried. A row whose column says
    # something else belongs to a table this module does not claim to read.
    rows = rows[_period_column(rows)]

    named = rows.title_fr.map(INDICATORS)
    rows["indicator"] = [pair[0] for pair in named]
    rows["unit"] = [pair[1] for pair in named]
    rows["breakdown"] = ""
    rows = rows.rename(columns={"title_fr": "source_title"})
    rows = pd.concat([rows, _population_by_age(series)], ignore_index=True)

    panel, disputed = _combine(rows)

    # An indicator-year whose governorates do not sum to the total printed beside them has
    # a cell read wrong somewhere in it, and there is no way to say which from the sum
    # alone. The whole year goes, and it is published rather than dropped quietly: library
    # lending in 2000 fails because Manouba reads 404 books against 150,250 the year after,
    # a misread in the one edition that prints it, so no cross-edition check could see it.
    checked = national_totals(panel, series)
    refused = checked[~checked.agrees].drop(columns="agrees")
    refused["reason"] = "the governorates do not sum to the printed national total"
    inconsistent, panel = _drop_inconsistent_sexes(panel)
    refused = pd.concat([refused, disputed, inconsistent], ignore_index=True)
    columns = ["indicator", "year", "governorate", "breakdown",
               "summed", "printed", "gap", "reason"]
    for column in columns:
        if column not in refused:
            refused[column] = ""
    refused = refused[columns].fillna({"governorate": "", "breakdown": ""})
    _check(panel, checked)

    convicted = set(zip(refused.indicator, refused.year, strict=True))
    keep = [pair not in convicted
            for pair in zip(panel.indicator, panel.year, strict=True)]
    return panel[keep].reset_index(drop=True), refused


def _population_by_age(series: pd.DataFrame) -> pd.DataFrame:
    """Population by governorate, year, age band and sex.

    The one table here whose columns are a classification rather than the period, and the
    reason it can be read at all: the sex is printed as a caption beside the row-label
    heading, which the corpus keeps as `panel`. Without it, tables 1.2, 1.3 and 1.4 are the
    same figures under three near-identical titles and there is no telling which is which.
    """
    # An empty caption survives a CSV round-trip as NaN rather than "", so a reader
    # loading the file gets a different frame from the one the pipeline built. Normalising
    # here means this reads the same either way.
    panel = series.panel.fillna("") if "panel" in series else ""
    rows = series[pd.Series(panel, index=series.index).isin(BY_SEX)
                  & series.row_kind.eq("data")].copy()
    rows["panel"] = rows.panel.fillna("")
    rows["governorate"] = rows.row_label.map(_governorate)
    rows["breakdown"] = rows.column_label.map(_age_band)
    rows = rows[rows.governorate.notna() & rows.breakdown.notna()]
    rows["indicator"] = rows.panel.map(BY_SEX)
    rows["unit"] = "thousands"
    return rows.rename(columns={"title_fr": "source_title"})[
        ["governorate", "year", "indicator", "breakdown", "value", "unit",
         "n_editions", "agreement", "source_title"]]


# Men and women have to come to the printed figure for both. INS rounds each of the three
# to a tenth of a thousand independently, so a gap of a hundred people is arithmetic; the
# ones that fail cluster in particular years and reach 49,400.
SEX_TOLERANCE = 0.15


def _drop_inconsistent_sexes(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Remove age cells where men plus women do not make the figure printed for both.

    This is the only check the age table has, and it is a strong one: nothing tells the
    parser which page is which sex, so if the captions had been attached wrongly the sums
    would fail everywhere. They hold for 93% of the cells that carry all three. Where they
    do not, one of the three is misread and the sum cannot say which, so all three go.
    """
    age = panel[panel.breakdown.ne("")]
    wide = age.pivot_table(index=["governorate", "year", "breakdown"],
                           columns="indicator", values="value")
    needed = {"population_male", "population_female", "population_all"}
    if not needed <= set(wide.columns):
        return pd.DataFrame(), panel
    wide = wide.dropna(subset=list(needed))
    gap = (wide.population_male + wide.population_female - wide.population_all).abs()
    bad = wide[gap > SEX_TOLERANCE].index

    if len(bad) == 0:
        return pd.DataFrame(), panel
    convicted = set(bad)
    triples = zip(panel.governorate, panel.year, panel.breakdown, strict=True)
    keep = [triple not in convicted for triple in triples]
    refused = pd.DataFrame(list(bad), columns=["governorate", "year", "breakdown"])
    refused["indicator"] = "population_by_age"
    refused["gap"] = gap.loc[bad].to_numpy()
    refused["reason"] = "men plus women do not make the figure printed for both sexes"
    return refused, panel[keep].reset_index(drop=True)


def _combine(rows: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """One row per governorate, year and indicator, pooling a cell's printings.

    A governorate can reach here under two labels -- "Ariana" and "7        Ariana" -- from
    two different editions, which the corpus keeps apart because it keys on the label as
    printed. Pooling them is not merely tidying: the two are independent printings, so a
    cell that was single-source under either label becomes confirmed. All 55 such cells
    agree; one that did not would be a misread and is refused instead.
    """
    key = ["source_title", "indicator", "unit", "governorate", "year", "breakdown"]
    grouped = rows.groupby(key, as_index=False).agg(
        value=("value", "first"),
        distinct=("value", "nunique"),
        n_editions=("n_editions", "sum"),
        revised=("agreement", lambda seen: (seen == "revised").any()),
    )
    clash = grouped[grouped.distinct > 1][["indicator", "year"]].drop_duplicates()
    disputed = pd.DataFrame({
        "indicator": clash.indicator, "year": clash.year,
        "summed": float("nan"), "printed": float("nan"), "gap": float("nan"),
        "reason": "two printings of the same cell disagree",
    })

    panel = grouped[grouped.distinct == 1].copy()
    panel["agreement"] = "single source"
    panel.loc[panel.n_editions > 1, "agreement"] = "confirmed"
    panel.loc[panel.revised, "agreement"] = "revised"
    panel = panel[["governorate", "year", "indicator", "breakdown", "value", "unit",
                   "n_editions", "agreement", "source_title"]]
    return (panel.sort_values(["indicator", "governorate", "year", "breakdown"])
            .reset_index(drop=True), disputed)


def _check(panel: pd.DataFrame, checked: pd.DataFrame) -> None:
    """What the panel has to satisfy before it is worth publishing."""
    duplicated = panel.duplicated(["governorate", "year", "indicator", "breakdown"])
    if duplicated.any():
        clash = panel[duplicated].iloc[0]
        raise RuntimeError(
            f"{clash.indicator} has two values for {clash.governorate} in {clash.year}")

    if (panel.value < 0).any():
        bad = panel[panel.value < 0].iloc[0]
        raise RuntimeError(f"{bad.indicator} is negative in {bad.governorate} {bad.year}")

    thin = panel.groupby("indicator").governorate.nunique()
    if (thin < 23).any():
        raise RuntimeError(f"indicators covering fewer than 23 governorates: "
                           f"{thin[thin < 23].to_dict()}")

    if len(checked) < 100:
        raise RuntimeError(f"only {len(checked)} indicator-years could be checked against a "
                           f"printed national total, expected 100 or more")
    # Individual failures are expected and are published; a *rate* of them means something
    # broke in the extraction rather than in one printed cell.
    failed = (~checked.agrees).mean()
    if failed > MAX_REFUSED_SHARE:
        worst = checked[~checked.agrees].sort_values("gap", ascending=False).iloc[0]
        raise RuntimeError(
            f"{failed:.1%} of indicator-years do not sum to their printed total, above the "
            f"{MAX_REFUSED_SHARE:.0%} that is treated as ordinary; worst is "
            f"{worst.indicator} {worst.year}: governorates sum to {worst.summed} "
            f"against a printed {worst.printed}")


def national_totals(panel: pd.DataFrame, series: pd.DataFrame) -> pd.DataFrame:
    """The governorates summed, beside the national figure the same table prints.

    This is the check that scales: it needs no outside source, runs over every indicator
    at once, and a governorate attached to the wrong column cannot survive it.
    """
    printed = series[series.row_label.eq("Total") & series.title_fr.isin(INDICATORS)]
    printed = printed[["title_fr", "column_label", "year", "value"]].rename(
        columns={"value": "printed"})
    yearly = panel[panel.breakdown.eq("")]
    summed = (yearly.groupby(["source_title", "indicator", "year"], as_index=False)
              .agg(summed=("value", "sum"), n=("value", "size")))
    summed = summed[summed.n == 24]

    joined = summed.merge(printed, left_on=["source_title", "year"],
                          right_on=["title_fr", "year"], how="inner")
    joined = joined.drop_duplicates(["indicator", "year"])
    joined["gap"] = (joined.summed - joined.printed).abs()
    allowed = (TOTAL_TOLERANCE * joined.printed.abs()).clip(lower=TOTAL_FLOOR)
    joined["agrees"] = joined.gap <= allowed
    return joined[["indicator", "year", "summed", "printed", "gap", "agrees"]]
