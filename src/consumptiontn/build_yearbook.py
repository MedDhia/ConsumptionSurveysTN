"""Turn the statistical yearbook corpus into datasets.

Twenty-two editions, roughly 260 numbered tables each. Hand-verifying that many tables
the way ``build_prices`` and ``build_labour`` verify their four is not possible, so the
approach here is different: extract broadly by shape, then reject anything that does not
survive a mechanical check, and publish what was rejected alongside what was kept.

**Why the parser is deliberately strict.** Surveying real pages turned up a long list of
ways a table parses cleanly and comes out wrong:

* ``146 406.9134 862.0`` is two values printed with no separator (17.8).
* ``Taux d'endettement5 52.3 ...`` glues a footnote marker to the label, giving six
  tokens for five columns and shifting every value by one (17.11).
* The 2010 edition prints whole bold columns with every glyph doubled and *no decimal
  point* -- ``1111 335511`` is 11 654 and 11 351. 57 such tokens, and no general rule can
  repair them safely: ``5599`` in the 2015 edition passes the same all-characters-paired
  test and is a genuine weight.
* ``...`` appears as a data value for a missing year (13.8, 2.1.2).
* Table 13.8 in the 2023 edition covers 2018-2022, not the 2019-2023 on the cover.

Every one of those is caught by refusing to guess: the year header is always read from
the page and never inferred, a row is accepted only when it yields *exactly* as many
numbers as there are year columns, and a label ending in a digit is rejected outright.
Strictness costs coverage, and the coverage table records exactly what it cost.

**Where a row's values begin.** The numeric region is not assumed to start at the first
number on the line, because plenty of labels contain one: "20 a 24 ans", "1.Production",
and "Nord - Ouest", whose hyphen reads as a nil. Each number is tried in turn as the
start and the first whose region is clean wins, which recovered 16,040 rows that were
being refused for their own labels appearing among the numbers. The split must fall on a
token boundary, so a footnote marker glued to a label ("Taux d'endettement5 52.3") cannot
become a value -- and because the region is chosen before the column count is known, a
row can still come out the wrong width and be refused for it. Choosing the start this way
also *corrected* rows that used to be kept with every value shifted one column left.

The check that scales is cross-edition agreement. Each edition carries a five-year
window, so 24 of the 26 years in the corpus appear in two or more editions -- most in
five. Where two editions report the same table, row and year they must agree, which is
what catches the doubled-integer columns that no local rule can.

**One table, several printed titles.** INS re-words a title between editions, usually by
saying more: "evolution des offres d emploi" becomes "... reçues par gouvernorat". Keyed
on the title as printed, one 29-year governorate panel was stored as three fragments and
the years two editions shared stopped confirming each other. Titles are merged where one
is a prefix of another *and the numbers bear it out* -- wording alone cannot settle it,
since "nombre de salles de sports" is a prefix of "nombre de salles de sports privées"
and those are two different tables over the same 24 governorates. They agree on 2 of 384
shared cells and are left apart.

**Values split across their decimal point.** ``4 526 .2`` is 4526.2, printed with a space
that pdftotext leaves in. This used to be treated as damage and refused, which cost 779
rows; the corpus itself settles it, since the repaired figures are confirmed by editions
that print the same numbers cleanly.

**Which half of a table a page carries.** Tables 1.2, 1.3 and 1.4 are one population-by-age
table printed for men, for women and for both. The sex appears only as a caption beside
the row-label heading -- "Gouvernorat <gap> Masculin" -- and once that was dropped the
three were indistinguishable, their titles differing only by where each was truncated:
two editions printing different sexes were reconciled against each other and 3,140 cells
were marked as INS revising a figure when they were men against women. The caption is now
kept as ``panel`` and forms part of a cell's identity. It is *recorded*, not interpreted:
layout alone cannot tell a caption for the page from a heading naming one column, so only
captions checked against the printed page are accepted.

**Stacked panels.** Many tables put two or more panels under one number and repeat the
same row labels down each: table 14.1 lists the twelve months once under "I -
Importations" and again under "II - Exportations", and table 13.2 lists them once per
industrial branch. Keying a row on its label alone silently collapsed those to whichever
panel was printed first -- around 30,000 values across roughly a thousand tables, with the
whole exports half of the monthly trade table among them, absent while the table looked
complete. Panels are now named from the line that opens them, whether that is an
enumerator carrying its own totals or a bare heading carrying no numbers at all, and a
repeat with no heading above it is refused and recorded rather than half-kept.
"""

from __future__ import annotations

import collections
import re
import subprocess
import unicodedata
from dataclasses import dataclass

import pandas as pd

from .config import INTERIM_DIR, YEARBOOK_FILE_IDS, raw_path

EDITIONS: tuple[int, ...] = tuple(sorted(YEARBOOK_FILE_IDS))

# Unicode bidi controls. pdftotext wraps Latin runs on bilingual pages in these; left in,
# they defeat every anchor regex.
BIDI = dict.fromkeys(map(ord, "‎‏‪‫‬‭‮⁦⁧⁨⁩"))

# A number, allowing INS's space thousands separator. Groups after the first must be
# exactly three digits, so "99 553300" reads as two numbers rather than one -- which is
# what makes the doubled-integer rows fail the column count instead of parsing wrongly.
NUMBER = re.compile(r"-?\d{1,3}(?: \d{3})+(?:\.\d+)?|-?\d+(?:\.\d+)?")

# INS's conventions table defines a lone dash as "resultat rigoureusement nul" -- an
# observed zero, not a missing value (which it writes as ">>" or "..."). Read as a value
# so that a row carrying one is not refused for having too few numbers.
NUMBER_OR_NIL = re.compile(NUMBER.pattern + r"|(?<=\s)-(?=\s|$)")

# pdftotext sometimes sets a space between a value's integer part and its decimal point:
# "4 526 .2" for 4526.2, "2 495 .0" for 2495.0. Left alone the row yields two values where
# one was printed, plus a stray dot among the numbers, and is refused -- 779 rows across
# the corpus, population by sex among them. INS never prints a bare ".2"; it writes 0.2.
# The gap is held to two spaces so a column gutter is not closed up, and because any line
# matching this already fails on the dot, the repair can only reach rows that are being
# refused today.
SPLIT_DECIMAL = re.compile(r"(?<=\d)\s{1,2}\.(?=\d)")

# A bare run of years, optionally footnote-marked. Five digits (2018 with footnote 6
# printed as "20186") deliberately does not match, so such headers are skipped.
YEAR = re.compile(r"^(?:19|20)\d\d\*?$")

# A school or judicial year, written by INS as a reversed two-digit range: "24-23" is
# 2023/24. Age bands are written the same way -- "04-00", "44-40" -- so the notation
# alone cannot tell them apart. The span does: a school year spans one year, an age band
# spans four. Getting this wrong would date a table of age groups as a time series.
# Older editions write the same thing with four digits -- "2000-99" for 1999/2000 --
# so both forms have to be recognised, and both must resolve to the same start year.
# They previously did not: the two-digit form was read correctly while the four-digit
# form fell through to the layout reader, which took its leading "2000" as the year and
# dated every such column one year late.
SCHOOL_YEAR = re.compile(r"^(\d{2}|\d{4})-(\d{2})$")

TABLE_NUMBER = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){1,2})\s+(\S.*)$")

# The reference year of a single-year table, printed either as its own header cell
# ("Année 2023") or inside the title ("... au 1.7.2023"). A table with neither is
# skipped rather than dated from the edition's cover, because the cover lies: table 13.8
# in the 2023 edition covers 2018-2022.
PAGE_YEAR = re.compile(
    r"Ann[ée]e\s*:?\s*((?:19|20)\d\d)"
    r"|\bau\s+\d{1,2}[./]\d{1,2}[./]((?:19|20)\d\d)"
)

# Contents-page rows look exactly like table headings but are dotted-leader index
# entries ("... par gouvernorat....... 86 ....... 2.4"). Indexing them inflates the
# catalogue with near-duplicate junk titles.
LEADER = re.compile(r"\.{4,}")

# Each heading ends with the table number again, rendered from the Arabic side ("4.2"
# for table 2.4), plus sometimes a page number. Neither belongs in the title.
TRAILING_NUMBERS = re.compile(r"[\s.]*\b\d{1,3}(?:\.\d{1,2})*\s*$")

# Lines that are not rows at all. A unit statement or a page footer occasionally yields a
# clean-looking row: "Unité : Le Nombre   Année" carries "2001" from the year beside it and
# reads as -2001, and "123   STATISTIQUES TUNISIE   ANNUAIRE STATISTIQUE" reads as a row
# labelled by the footer with the page number for a value. Ten cells across the corpus, and
# each is unambiguously furniture rather than data.
NOT_A_ROW = re.compile(
    r"^\s*(?:Unit[ée]\s*:|Base\s*[:(]|Source\s*:|N\.?B\s*:|Champ\s*:)"
    r"|STATISTIQUES\s+TUNISIE|ANNUAIRE\s+STATISTIQUE",
    re.I,
)

# Rows that are aggregates of other rows. Kept, but marked, because summing them with
# their own components double-counts -- and because they are free arithmetic checks.
SUBTOTAL = re.compile(
    r"^(t\s*o\s*t\s*a\s*l|ensemble|sous\s*[- ]?\s*total|dont\b|district"
    r"|nord\s*-|centre\s*-|sud\s*-|grand\s+tunis|pib)\b",
    re.I,
)

# Many tables are two or more panels stacked under one number, each panel repeating the
# same row labels: table 14.1 lists the twelve months once under "I - Importations" and
# again under "II - Exportations". Keying a row by its label alone silently collapses
# the panels into whichever came first, so the enumerator that opens a panel is kept and
# used to qualify the labels beneath it.
# The enumerator itself is not part of the panel's name, and editions do not agree on
# it: the same import panel is "I - Importations", "I. Importations" and "A.
# Importations" in different years. Qualifying with the enumerator attached would put
# those in three separate series and lose the cross-edition check, so it is stripped and
# only the text is kept.
# The space after the enumerator is optional: table 13.3 opens its panels with
# "5.Textiles, habillement et cuirs", set tight.
SECTION = re.compile(r"^(?:[IVX]{1,4}|[A-Z]|\d{1,2})\s*[–\-—.)]\s*(\S.*)$")


@dataclass(frozen=True)
class Table:
    """One table found on one page of one edition."""

    edition: int
    number: str
    title: str
    page: int


def _strip_bidi(text: str) -> str:
    return text.translate(BIDI)


def edition_pages(edition: int) -> list[str]:
    """Layout-preserving text of every page, cached under data/interim.

    ``pdftotext -layout`` rather than pdfplumber: it keeps a row's label and all its
    numbers on one line with the columns still separated, and renders Arabic in logical
    order instead of reversed. It is also three times faster, which matters across 22
    editions.
    """
    cache = INTERIM_DIR / f"annuaire_{edition}.txt"
    if not cache.exists():
        INTERIM_DIR.mkdir(parents=True, exist_ok=True)
        out = subprocess.run(
            ["pdftotext", "-layout", str(raw_path(f"annuaire_{edition}")), "-"],
            capture_output=True,
            check=True,
        )
        cache.write_text(_strip_bidi(out.stdout.decode("utf-8", "replace")))
    return cache.read_text().split("\f")


def split_row(line: str) -> tuple[str, list[float], bool] | None:
    """Split one printed row into French label, values, and a provisional flag.

    These pages read left to right as: French label, the numbers, then the same label in
    Arabic. So the numeric region runs from the first number to the last, and whatever
    trails it is the Arabic label rather than data.

    Only the *interior* of that region has to be clean. An ellipsis standing in for a
    missing year, or a footnote digit glued to a value, leaves residue there and refuses
    the row. Asterisks are the one exception: INS uses them to mark a provisional figure,
    so they are recorded rather than treated as damage.
    """
    line = SPLIT_DECIMAL.sub(".", line)
    matches = list(NUMBER_OR_NIL.finditer(line))
    if not matches:
        return None

    # Where the values begin is not always the first number on the line: plenty of
    # labels contain one. "20 a 24 ans", "1.Production", "Nord - Ouest" (the dash reads
    # as a nil) all start the region inside the label, and the row is then refused for
    # the label's own words being left over among the numbers -- 16,040 rows across the
    # corpus, most of them real data.
    #
    # So each number is tried in turn as the start, left to right, and the first one
    # whose region is clean wins. Trying left to right rather than searching for a start
    # that fits the column count is what keeps this conservative: the region is chosen
    # before the width is known, so a row can still come out with the wrong number of
    # values and be refused for it, exactly as before.
    for index, first in enumerate(matches):
        start, end = first.start(), matches[-1].end()
        # The split has to fall on a token boundary, or "Taux d'endettement5 52.3"
        # reads as the label "Taux d'endettement" and a value of 5. One space is enough
        # of a boundary: plenty of rows set the label off from the first value with a
        # single space, and demanding a wide gutter refused them outright.
        if start > 0 and not line[start - 1].isspace():
            continue
        # Slice with the preceding character kept, so the nil pattern's lookbehind for
        # a space still has one to find; without it a row whose first value is a lone
        # dash leaves that dash as residue and is refused for carrying its own zero.
        region = line[max(start - 1, 0):end]
        residue = NUMBER_OR_NIL.sub("", region).strip()
        provisional = "*" in residue
        if residue.replace("*", "").strip():
            continue
        label = line[:start].strip(" .:-\t")
        values = [0.0 if m.group().strip() == "-" else float(m.group().replace(" ", ""))
                  for m in matches[index:]]
        return label, values, provisional
    return None


def _year_header(line: str) -> list[int] | None:
    """The years a table's columns stand for.

    Some tables print the row-label caption on the same line as the years, in both
    languages: "Gouvernorat 2023 2022 2021 2020 2019 الولاية". One caption word is
    allowed at each end for that; everything between them still has to be years, so
    prose that happens to contain dates is not mistaken for a header.
    """
    tokens = line.split()
    if tokens and not YEAR.match(tokens[0]):
        tokens = tokens[1:]
    if tokens and not YEAR.match(tokens[-1]):
        tokens = tokens[:-1]
    if len(tokens) < 2 or not all(YEAR.match(t) for t in tokens):
        return None
    return [int(t.rstrip("*")) for t in tokens]


def _school_year_header(line: str) -> list[tuple[str, int]] | None:
    """Columns that are school or judicial years, with the calendar year each starts in.

    These date themselves, so a table headed this way needs no year printed on the page
    -- which is why so many of them were previously skipped.
    """
    tokens = line.split()
    if tokens and not SCHOOL_YEAR.match(tokens[0]):
        tokens = tokens[1:]
    if tokens and not SCHOOL_YEAR.match(tokens[-1]):
        tokens = tokens[:-1]
    if len(tokens) < 2:
        return None
    out = []
    for token in tokens:
        match = SCHOOL_YEAR.match(token)
        if match is None:
            return None
        end_text, start = match.group(1), int(match.group(2))
        end = int(end_text)
        if len(end_text) == 2:
            end = 2000 + end if end <= 50 else 1900 + end
        if (end - 1) % 100 != start:
            return None  # a span of four is an age band, not a year
        # Canonical "1999/00" rather than whichever of "2000-99" or "00-99" this
        # edition printed. Both denote one school year, and reconciliation keys on the
        # column label -- so leaving them distinct would keep two printings of the same
        # figure from ever checking each other.
        start_year = end - 1
        out.append((f"{start_year}/{end % 100:02d}", start_year))
    return out


def _category_header(line: str) -> list[str] | None:
    """A run of short column labels -- age bands, indicator codes -- rather than years.

    Many tables put governorates down the side and a classification across the top for a
    single year: "44-40 39-35 34-30 ..." or "I.S.F T.G.F 49-45 ...". Guessing which
    lines are headers from their own appearance is unreliable, so this only proposes a
    candidate; ``parse_page`` accepts it solely if enough following rows yield exactly
    this many numbers, which is what rules out prose.
    """
    tokens = line.split()
    if not 2 < len(tokens) <= 20:
        return None
    if any(len(token) > 9 for token in tokens):
        return None
    # At least half the tokens should look like codes rather than words: a header of
    # ordinary French words is a wrapped sentence, not a column row.
    coded = sum(bool(re.search(r"[\d.\-/]", token)) or token.isupper() for token in tokens)
    if coded * 2 < len(tokens):
        return None
    return tokens


# The caption a page sets to the right of its row-label heading -- "Gouvernorat
# <gap> Masculin" -- names which half of a table the page carries. Tables 1.2, 1.3 and 1.4
# are the same population-by-age table printed once for men, once for women and once for
# both, and without this the three are indistinguishable once the heading is gone: their
# titles differ only by a truncation.
#
# It is *recorded*, not interpreted. Whether such a caption names a panel or merely labels
# the column group cannot be told from the layout -- table 20.3 sets "Tranche de salariés"
# in exactly the same place -- so it becomes a column of its own rather than a qualifier on
# the row label, which would be a claim the page does not support.
PANEL_CAPTIONS = (
    "Gouvernorat", "Station", "Catégorie", "Categorie", "Désignation", "Designation",
    "Secteur", "Branche", "Pays", "Nationalité", "Nationalite", "Libellé", "Indicateur",
    "Rubrique",
)

# Only captions that were checked against the printed page are accepted. Layout alone
# cannot tell a caption for the page from a heading that names one column -- on the
# continuation pages the sex is set above the last column, so it looks exactly like that
# column's label, and a purely structural rule let "Total ND" and "Cabinets Cabinets de"
# through. A short vocabulary of verified captions claims only what was read.
PANEL_VALUES = ("Masculin", "Féminin", "Masculin et Féminin")

# A wrapped two-word heading -- "Année Judiciaire", "Produit Intérieur Brut" -- continues
# straight after its first word. A caption for the page sits far to the right of it.
PANEL_GAP = 8


def _caption_on(line: str) -> str:
    """The caption this line sets to the right of a row-label heading, if it is one."""
    latin = re.sub(r"[\u0600-\u06ff\ufb50-\ufdff\ufe70-\ufeff]+", " ", line)
    split = re.match(r"\s*(\S+)(\s+)(\S.*?)\s*$", latin)
    if split is None or split.group(1) not in PANEL_CAPTIONS:
        return ""
    if len(split.group(2)) < PANEL_GAP:
        return ""
    caption = " ".join(split.group(3).split())
    return caption if caption in PANEL_VALUES else ""


def _panel_caption(lines: list[str], at: int) -> str:
    """The caption printed beside the row-label heading above a table's columns."""
    for line in reversed(lines[max(0, at - 3):at]):
        if not line.strip():
            continue
        return _caption_on(line)
    return ""


def _latin_only(text: str) -> str:
    """Drop the Arabic rendering printed beside every French label.

    Removing the Arabic strands its punctuation -- "Total abonnes aux reseaux ( (
    telephoniques" -- so tokens left holding nothing but brackets go too.
    """
    stripped = re.sub(r"[\u0600-\u06ff]+", " ", text)
    kept = [token for token in stripped.split() if re.search(r"[A-Za-zÀ-ÿ0-9]", token)]
    return " ".join(kept).strip()


def _inferred_label(lines: list[str], at: int) -> str | None:
    """The label for a row printed as numbers alone, taken from the lines around it.

    Two layouts, both common in chapters 2 and 12. The label sits on the line above its
    numbers; or it wraps *around* them, with the remainder printed on the line below --
    "Nombre d'abonnes au reseau de", the numbers, then "telephone fixe (en milliers)".

    A continuation is recognised by starting lower-case, which is what distinguishes it
    from the next row's own label. Nothing here is printed alongside its numbers, so the
    rows it produces are marked `label_inferred` and a reader can leave them out.
    """
    above = None
    for line in reversed(lines[max(0, at - 2):at]):
        stripped = line.strip()
        if not stripped:
            continue
        if NUMBER.search(stripped):
            return None  # another row's numbers sit between: the pairing is ambiguous
        above = stripped
        break
    if above is None:
        return None
    above = _latin_only(above)
    if len(above) < 4 or not re.search(r"[A-Za-zÀ-ÿ]{3}", above):
        return None

    parts = [above]
    for line in lines[at + 1:at + 4]:
        stripped = line.strip()
        if not stripped:
            continue  # a blank line between the numbers and the rest of the label
        if NUMBER.search(stripped):
            break
        if not _latin_only(stripped)[:1].islower():
            break  # a new label, not the rest of this one
        parts.append(stripped)
    label = _latin_only(" ".join(parts)).strip(" .:-")
    return label or None


def _page_year(text: str) -> int | None:
    match = PAGE_YEAR.search(text)
    if match is None:
        return None
    return int(match.group(1) or match.group(2))


def _heading(line: str) -> tuple[str, str] | None:
    """Read a numbered-table heading, or None if the line is not one.

    Contents-page entries match the same pattern and are refused here, so the catalogue
    holds the tables themselves rather than the index that points at them.
    """
    stripped = line.strip()
    if LEADER.search(stripped):
        return None
    match = TABLE_NUMBER.match(stripped)
    if not match:
        return None
    title = TRAILING_NUMBERS.sub("", re.sub(r"\s+", " ", match.group(2))).strip(" .:-")
    if len(title) < 9 or not re.search(r"[A-Za-zÀ-ÿ]{3}", title):
        return None
    return match.group(1), title


def _table_at(lines: list[str], upto: int) -> tuple[str, str] | None:
    """The nearest numbered-table heading above a year header."""
    for line in reversed(lines[max(0, upto - 12):upto]):
        heading = _heading(line)
        if heading:
            return heading
    return None


def _qualify_panels(entries: list[dict]) -> tuple[list[dict], list[tuple[str, str]]]:
    """Disambiguate row labels that repeat because the table is stacked panels.

    A repeated label is qualified by the enumerator that opens its panel, so table
    14.1's two "Janvier" rows become "I - Importations / Janvier" and
    "II - Exportations / Janvier". Where a repeat has no enumerator above it there is
    nothing to tell the copies apart, and every copy is refused rather than letting one
    of them stand in for the row -- which is what keying on the bare label did.
    """
    data = [entry for entry in entries if entry["values"] is not None]
    seen: collections.Counter[str] = collections.Counter(entry["label"] for entry in data)
    repeated = {label for label, n in seen.items() if n > 1}
    if not repeated:
        return data, []

    kept: list[dict] = []
    refused: list[tuple[str, str]] = []
    section: str | None = None
    for entry in entries:
        label = entry["label"]
        if entry["values"] is None:
            section = label  # a bare heading line opens a panel and is not itself data
            continue
        opener = SECTION.match(label)
        if opener and label not in repeated:
            section = opener.group(1).strip()
            kept.append(entry)
            continue
        if label not in repeated:
            kept.append(entry)
            continue
        if section is None:
            refused.append((label, "row label repeats with no panel heading above it"))
            continue
        kept.append({**entry, "label": f"{section} / {label}"})

    # Qualifying can itself collide if one panel repeats a label internally.
    final: collections.Counter[str] = collections.Counter(entry["label"] for entry in kept)
    collided = {label for label, n in final.items() if n > 1}
    if collided:
        refused.extend((label, "row label repeats within one panel") for label in collided)
        kept = [entry for entry in kept if entry["label"] not in collided]
    return kept, refused


# A trailing column's label is plain words: letters, and the punctuation that binds
# them. Anything carrying a digit is a year or a footnote marker, not a column name.
TRAILING_LABEL = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\'\u2019.\- ]{3,}$")


def _trailing_column(lines: list[str], at: int, header: str) -> int:
    """One extra non-year column, labelled to the right of the years.

    Returns 1 when such a column is there and 0 otherwise. The label may sit on the
    header line itself -- table 13.4 heads its columns ``2023 2022 2021 Pondération`` --
    or on the line beneath the years, which is how table 13.7 sets the same weight.

    Either way it is deliberately narrow: the label must be plain text carrying no digits
    of its own, and must begin further right than the last year does, so a stray word
    wrapped from the title cannot be mistaken for a column.
    """
    years = list(re.finditer(r"(?:19|20)\d\d", header))
    if not years:
        return 0
    last_year = years[-1].start()
    # Beside the years. ``_year_header`` already drops this token when it reads the
    # header, so without this the column is invisible and every row comes out one value
    # too wide.
    tail = _latin_only(header[years[-1].end():]).strip()
    if TRAILING_LABEL.fullmatch(tail):
        return 1
    for line in lines[at + 1:at + 3]:
        # Position has to come from the raw line; stripping the Arabic side also strips
        # the indentation that says which column the label belongs to.
        if re.search(r"\d", line) or not re.search(r"[A-Za-zÀ-ÿ]{4}", _latin_only(line)):
            continue
        latin = re.sub(r"[؀-ۿ]", " ", line)
        start = len(latin) - len(latin.lstrip())
        if start > last_year:
            return 1
    return 0


def parse_page(edition: int, page_index: int, text: str) -> tuple[list[dict], list[dict]]:
    """Rows accepted and rows refused, from one page.

    Two table shapes. Columns are years -- the common case, and the one that dates
    itself. Or columns are a classification and the whole table describes one year,
    which then has to be found on the page.
    """
    lines = text.split("\n")
    rows: list[dict] = []
    refused: list[dict] = []
    page_year = _page_year(text)

    for i, line in enumerate(lines):
        years = _year_header(line.strip())
        school = None if years else _school_year_header(line.strip())
        categories = None if (years or school) else _category_header(line.strip())
        if years is None and school is None and categories is None:
            continue
        if years is None and school is None and page_year is None:
            continue  # a classification table with no year on the page is undatable
        heading = _table_at(lines, i)
        if heading is None:
            continue
        number, title = heading
        if years:
            columns, column_years = [str(y) for y in years], list(years)
        elif school:
            columns, column_years = [c for c, _ in school], [y for _, y in school]
        else:
            columns, column_years = categories, [page_year] * len(categories)
        width = len(columns)
        # Only a classification table needs this. A year header dates itself, so nothing
        # about it is ambiguous; it is the single-year tables printed once per sex that are
        # indistinguishable without the caption above their columns.
        panel = _panel_caption(lines, i) if categories is not None else ""
        # Some year tables carry one more column that is not a year, with its label on
        # the line below the years rather than beside them: table 13.7 prints the
        # consumer price index for three years and then each group's expenditure weight.
        # Every row then yields one value too many and the whole table is refused --
        # 612 rows across ten editions, which is the price index by product group for
        # 2012 to 2023. The weight is a constant, not a point in a time series, so it is
        # counted here and dropped rather than dated.
        trailing = _trailing_column(lines, i, line) if years else 0

        entries: list[dict] = []
        block_refused: list[dict] = []
        inferred_labels: set[str] = set()
        for offset, body in enumerate(lines[i + 1:], i + 1):
            stripped = body.strip()
            if not stripped:
                continue
            if _year_header(stripped) is not None:
                break  # a second table starts on the same page
            parts = split_row(stripped)
            if parts is None:
                if NUMBER.search(stripped):
                    block_refused.append({"edition": edition, "table_number": number,
                                          "row_label": stripped[:60],
                                          "reason": "unparsed characters among the numbers"})
                    continue
                # A line of text carrying no numbers at all, in the middle of a table,
                # is the heading of the panel that follows -- "Industries
                # agro-alimentaires" above table 13.2's first run of twelve months.
                # Recorded in row order so that repeated labels below can be qualified.
                heading_text = _latin_only(stripped)
                # A line starting lower-case is the tail of a label wrapped around its
                # own numbers -- "Produits d'origine animale ou", the values, then
                # "vegetale" -- which ``_inferred_label`` has already folded into the row
                # above. Registering it as a panel as well made it the qualifier for
                # every repeat that followed, so table 14.4's exports came out under
                # "vegetale" rather than "2. Exportations".
                if heading_text[:1].islower():
                    continue
                if len(heading_text) >= 3 and re.search(r"[A-Za-zÀ-ÿ]{3}", heading_text):
                    entries.append({"label": heading_text[:80], "values": None,
                                    "provisional": False, "inferred": False})
                continue
            label, values, provisional = parts
            # Drop the undated trailing column before the width is used for anything.
            # It has to go first: a row whose label is wrapped around its numbers is
            # recovered only when the values already match the column count, so trimming
            # afterwards would leave those rows one wide and silently discard them.
            if trailing and len(values) == width + trailing:
                values = values[:width]
            inferred = False
            if len(label) < 3 or not re.search(r"[A-Za-zÀ-ÿ]{3}", label):
                # No label beside the numbers. It may be printed above them, or wrapped
                # around them -- recoverable, but weaker than a label read off the same
                # line, so the rows it yields say so.
                if label or len(values) != width:
                    # A panel heading whose enumerator is a bare number reads as a row
                    # with no label and one value -- "5.Textiles, habillement et cuirs"
                    # yields 5. It opens a panel rather than carrying data, and without
                    # it table 13.3's twelve months repeat once per industrial branch
                    # with nothing to tell the branches apart.
                    opener = SECTION.match(stripped) if not label else None
                    if opener and len(values) < width:
                        heading = _latin_only(opener.group(1)).strip(" .:-")
                        if len(heading) >= 3 and re.search(r"[A-Za-zÀ-ÿ]{3}", heading):
                            entries.append({"label": heading[:80], "values": None,
                                            "provisional": False, "inferred": False})
                    continue
                candidate = _inferred_label(lines, offset)
                if candidate is None:
                    continue
                # The line this label was built from may already have been recorded as a
                # panel heading -- from above the numbers there is no telling the two
                # apart. Now there is: it belongs to this row, so it is retracted rather
                # than left to qualify every repeat below it, which is how table 14.4's
                # exports came out under "Produits d'origine animale ou". This has to
                # happen before the uniqueness test below, or the second copy of a
                # repeated layout keeps the heading the first copy retracted.
                if entries and entries[-1]["values"] is None:
                    opening = entries[-1]["label"].strip(" .:-")
                    if opening and candidate.startswith(opening):
                        entries.pop()
                # The same inferred label twice in one table means two different series
                # were reduced to one name -- on page 43 the teacher counts of the first
                # and second cycle, on page 195 fixed-line and mobile subscribers. There
                # is no way to tell them apart afterwards, so both are dropped.
                if candidate in inferred_labels:
                    block_refused.append({
                        "edition": edition, "table_number": number,
                        "row_label": candidate[:80],
                        "reason": "inferred label is not unique within the table",
                    })
                    continue
                inferred_labels.add(candidate)
                label, inferred = candidate, True

            reason = None
            if NOT_A_ROW.search(label):
                reason = "the label is a caption or a page footer, not a row"
            elif label[-1].isdigit():
                reason = "label ends in a digit (footnote marker shifts the columns)"
            elif len(values) != width:
                reason = f"{len(values)} values for {width} columns"
            if reason:
                block_refused.append({"edition": edition, "table_number": number,
                                      "row_label": label[:80], "reason": reason})
                continue

            entries.append({"label": label, "values": values,
                            "provisional": provisional, "inferred": inferred})

        # Panels have to be resolved with the whole table in hand: a label is only
        # ambiguous once it is known to repeat.
        entries, repeats = _qualify_panels(entries)
        block_refused.extend({"edition": edition, "table_number": number,
                              "row_label": label[:80], "reason": reason}
                             for label, reason in repeats)
        block = [
            {
                "edition": edition,
                "table_number": number,
                "table_title": title,
                "page": page_index + 1,
                "row_label": entry["label"],
                "row_kind": "aggregate" if SUBTOTAL.match(entry["label"]) else "data",
                "panel": panel,
                "column_label": column,
                "year": column_year,
                "value": value,
                "provisional": entry["provisional"],
                "label_inferred": entry["inferred"],
            }
            for entry in entries
            for column, column_year, value in zip(columns, column_years, entry["values"],
                                                  strict=True)
        ]

        # A year header is self-evidently a header. A run of short tokens is not, so a
        # classification table has to earn it: enough rows must fit the proposed width
        # for the line to have been a header rather than a coincidence.
        if categories is not None and len({r["row_label"] for r in block}) < 5:
            continue
        rows.extend(block)
        refused.extend(block_refused)
    return rows, refused


def extract(editions: tuple[int, ...] = EDITIONS) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Every year-column table the corpus yields, plus the rows that were refused."""
    kept: list[dict] = []
    refused: list[dict] = []
    for edition in editions:
        for index, text in enumerate(edition_pages(edition)):
            page_rows, page_refused = parse_page(edition, index, text)
            if not page_rows:
                # Only where the single-line header paths found nothing, so the
                # layout reader can add tables but never alter one already read.
                page_rows = parse_page_layout(edition, index, text)
            kept.extend(page_rows)
            refused.extend(page_refused)
    series = pd.DataFrame(kept)
    if not series.empty:
        series = series.drop_duplicates(
            ["edition", "table_number", "row_label", "column_label", "year"]
        ).sort_values(["edition", "table_number", "row_label", "year"]).reset_index(drop=True)
    return series, pd.DataFrame(refused)


# --------------------------------------------------------------------- reconciliation

# Above this relative gap, two editions reporting different numbers for the same cell is
# treated as a parse fault rather than a statistical revision. INS does revise figures
# between editions -- that is normal and shows up as a sub-percent wobble -- but a value
# that moves by an order of magnitude is the doubled-glyph fault, not a revision.
CONFLICT_RATIO = 1.10


def _latin(text: str) -> str:
    """Normalise a bilingual string down to its Latin part, for matching across editions.

    Table *numbers* move between editions -- 2010's 6.1.1 is 2023's 6.1.5 -- so the title
    is the only stable key.
    """
    stripped = re.sub(r"[^\x00-\x7FÀ-ÿ]+", " ", str(text))
    return re.sub(r"\s+", " ", stripped).strip().lower()


# The table number is printed a second time on the Arabic side, and dropping the Arabic
# strands it at the end of the Latin text: the same table is "evolution des offres d
# emploi 3" in one edition and "... 7" in the next. It is removed to compare two titles,
# never to key on them -- two different tables in a chapter can differ by nothing else,
# so a stem that matches is a candidate for merging and not a merge.
STEM = re.compile(r"\s+[\d.]+$")


def _stem(title: str) -> str:
    """A title reduced to what two editions can be expected to have in common.

    Accents come and go between editions -- "variations annuelles de l indice general"
    and "... de l indice général" are the same table, set once without accents and once
    with -- so they are folded away for the comparison. Like the table number, this is
    only ever used to *propose* a merge; the numbers still have to confirm it.
    """
    bare = unicodedata.normalize("NFKD", STEM.sub("", title).strip())
    return "".join(ch for ch in bare if not unicodedata.combining(ch))


# INS re-words a table's title between editions, usually by saying more: "evolution des
# offres d emploi" becomes "evolution des offres d emploi reçues par gouvernorat". Keyed
# on the title as printed, one 21-year governorate panel is stored as three short ones,
# and the years the two editions share stop confirming each other.
#
# Wording alone cannot settle it -- "nombre de salles de sports" is a prefix of "nombre de
# salles de sports privées", and those are two different tables listing the same 24
# governorates. So a merge is a *hypothesis*, tested against the numbers: the two must
# report enough of the same cells, and agree on nearly all of them. The sports halls
# agree on 2 of 384 shared cells and are left apart.
CANONICAL_MIN_SHARED = 5
CANONICAL_MIN_AGREEMENT = 0.95


def canonical_titles(frame: pd.DataFrame) -> dict[str, str]:
    """Map each title to the one it should be reconciled under.

    Candidates are titles in the same chapter where one is a prefix of the other. Each
    candidate pair is confirmed against the cells the two have in common, and the group's
    longest title -- the most explicit one INS settled on -- becomes the name for all of
    it. Merging is transitive, so a title that overlaps the next one in the chain joins
    the group even where it shares no year with the far end of it.
    """
    cells = {
        key: dict(zip(zip(group.row_label, group.column_label, group.year, strict=True),
                      group.value, strict=True))
        for key, group in frame.groupby(["chapter", "title_fr"])
    }
    parent = {title: title for _, title in cells}
    stems = {title: _stem(title) for _, title in cells}

    def find(title: str) -> str:
        while parent[title] != title:
            parent[title] = parent[parent[title]]
            title = parent[title]
        return title

    for chapter, group in frame.groupby("chapter"):
        titles = sorted(set(group.title_fr))
        for position, first in enumerate(titles):
            for second in titles[position + 1:]:
                left_stem, right_stem = stems[first], stems[second]
                if not (left_stem.startswith(right_stem)
                        or right_stem.startswith(left_stem)):
                    continue
                left, right = cells[(chapter, first)], cells[(chapter, second)]
                shared = set(left) & set(right)
                if len(shared) < CANONICAL_MIN_SHARED:
                    continue
                agreed = sum(
                    1 for cell in shared
                    if max(abs(left[cell]), abs(right[cell]))
                    / max(min(abs(left[cell]), abs(right[cell])), 1e-9) <= CONFLICT_RATIO
                )
                if agreed / len(shared) < CANONICAL_MIN_AGREEMENT:
                    continue
                root_first, root_second = find(first), find(second)
                if root_first != root_second:
                    parent[root_second] = root_first

    groups: dict[str, list[str]] = collections.defaultdict(list)
    for title in parent:
        groups[find(title)].append(title)
    # The name to keep is the most explicit wording, and among spellings of it the one
    # INS typeset properly. Length alone would name the merged table after whichever
    # edition happened to set it without accents, which is the older and worse rendering.
    def best(members: list[str]) -> str:
        return max(members, key=lambda title: (len(_stem(title)),
                                               sum(ord(ch) > 127 for ch in title)))

    return {title: best(members) for members in groups.values() for title in members}


def catalogue(editions: tuple[int, ...] = EDITIONS) -> pd.DataFrame:
    """Every numbered table heading in the corpus, extracted or not.

    Taken from the body pages rather than the sommaire: the page number is then observed
    instead of transcribed, and a table missing from the contents list is still found.
    """
    rows = []
    for edition in editions:
        for index, text in enumerate(edition_pages(edition)):
            for line in text.split("\n"):
                heading = _heading(line)
                if heading is None:
                    continue
                number, title = heading
                rows.append({
                    "edition": edition,
                    "table_number": number,
                    "chapter": number.split(".")[0],
                    "table_title": _latin(title),
                    "page": index + 1,
                })
    frame = pd.DataFrame(rows)
    return (frame.drop_duplicates(["edition", "table_number", "table_title"])
            .sort_values(["edition", "chapter", "table_number"])
            .reset_index(drop=True))


# pdftotext puts the Arabic side's digits on lines of their own, and one occasionally
# lands at the head of a row: "7        Ariana   86  86  85  85  83" in the 2005 edition's
# table 3.3. The values are untouched -- the row still yields exactly as many as there are
# columns, which a leaked value would break -- but the label is not the one the rest of the
# corpus uses, so the governorate is split into two series and each half stops confirming
# the other.
STRAY_DIGITS = re.compile(r"^\d+\s{2,}")


def _rejoin_stray_digits(frame: pd.DataFrame) -> pd.Series:
    """Strip a stray leading digit run, but only where the label it leaves already exists.

    Stripping unconditionally would merge rows that merely start with a number, and the
    page footers that reach this far -- "123   STATISTIQUES TUNISIE   ANNUAIRE STATISTIQUE"
    -- would collapse into one label across every page they appear on. Requiring the
    stripped form to be a label the same table already uses makes the repair evidence-led:
    there has to be something to rejoin.
    """
    stripped = frame.row_label.str.replace(STRAY_DIGITS, "", regex=True)
    changed = stripped != frame.row_label
    if not changed.any():
        return frame.row_label
    known = set(zip(frame.title_fr[~changed], frame.row_label[~changed], strict=True))
    joins = pd.Series([pair in known for pair in
                       zip(frame.title_fr, stripped, strict=True)], index=frame.index)
    rejoinable = changed & joins
    return frame.row_label.where(~rejoinable, stripped)


def reconcile(series: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Collapse the per-edition rows to one value per cell, and split off the conflicts.

    Each edition carries a five-year window, so most cells are reported two to five
    times. Where the copies agree the value is confirmed by an independent printing of
    the same figure. Where they differ by a little, INS revised it and the most recent
    edition wins. Where they differ by a lot, something was misread, and the cell is
    removed from the series and handed to the coverage table instead.
    """
    frame = series.copy()
    frame["title_fr"] = frame.table_title.map(_latin)
    frame["row_label"] = frame.row_label.str.strip()
    frame["row_label"] = _rejoin_stray_digits(frame)
    frame["chapter"] = frame.table_number.astype(str).str.split(".").str[0]
    frame["title_fr"] = frame.title_fr.map(canonical_titles(frame))
    # The caption is part of the identity of a cell, not a note about it: tables 1.2 and
    # 1.3 are the same population-by-age table for men and for women, and without it in the
    # key two editions printing different sexes would be compared and one thrown away.
    key = ["title_fr", "panel", "row_label", "column_label", "year"]

    stats = frame.groupby(key)["value"].agg(
        n_editions="size", lo="min", hi="max", distinct="nunique"
    )
    ratio = stats.hi.abs().clip(lower=1e-9) / stats.lo.abs().clip(lower=1e-9)
    stats["agreement"] = "single source"
    stats.loc[(stats.n_editions > 1) & (stats.distinct == 1), "agreement"] = "confirmed"
    stats.loc[(stats.distinct > 1) & (ratio <= CONFLICT_RATIO), "agreement"] = "revised"
    stats.loc[(stats.distinct > 1) & (ratio > CONFLICT_RATIO), "agreement"] = "conflict"

    # The newest edition is the authority: it carries INS's latest revision.
    latest = (frame.sort_values("edition")
              .drop_duplicates(key, keep="last")
              .set_index(key))
    joined = latest.join(stats[["n_editions", "agreement"]])

    conflicts = joined[joined.agreement == "conflict"].reset_index()
    clean = joined[joined.agreement != "conflict"].reset_index()

    columns = ["table_number", "table_title", "title_fr", "panel", "row_label", "row_kind",
               "column_label", "year", "value", "provisional", "label_inferred",
               "n_editions", "agreement", "edition", "page"]
    clean = clean[columns].sort_values(["title_fr", "row_label", "year"])
    return clean.reset_index(drop=True), conflicts.reset_index(drop=True)


# Tunisia's seven grandes régions and the governorates each is made of. Many tables print
# both, which makes the region row a sum the corpus can check against its own parts -- the
# validator the plan called for and never got. It needs no outside source and runs over
# every table carrying both at once.
GRANDES_REGIONS: dict[str, tuple[str, ...]] = {
    "District-Tunis": ("Tunis", "Ariana", "Ben Arous", "Manouba"),
    "Nord-Est": ("Nabeul", "Zaghouan", "Bizerte"),
    "Nord-Ouest": ("Béja", "Jendouba", "Le Kef", "Siliana"),
    "Centre-Est": ("Sousse", "Monastir", "Mahdia", "Sfax"),
    "Centre-Ouest": ("Kairouan", "Kasserine", "Sidi Bouzid"),
    "Sud-Est": ("Gabès", "Médenine", "Tataouine"),
    "Sud-Ouest": ("Gafsa", "Tozeur", "Kébili"),
}

# INS sets a region five ways -- "Nord-Est", "Nord -Est", "Nord - Est", "Nord Ouest" -- and
# a governorate two, so both sides are folded before being matched. The tables that print
# regions happen to use the hyphenated form throughout, so this adds no checks today; it
# means a future edition changing its spelling does not silently stop being checked.
SUBTOTAL_TOLERANCE = 0.02
SUBTOTAL_FLOOR = 1.0

# Only a count adds up. A region's fertility rate is not the sum of its governorates' --
# it is their population-weighted mean -- and the same goes for an index, a density, a
# share or an average. Checking those would report 1,400 disagreements that are arithmetic
# working correctly, and drown the ones that mean something: rate tables come out 10.8%
# in agreement against 97.8% for the rest. They are marked rather than dropped, so the
# dataset says which rows were checked and which could not be.
NOT_ADDITIVE = re.compile(
    r"\btaux\b|\bindice|\bratio\b|\bmoyenne|\bpour\s*1\s*000|\bdensit|\bpart\b"
    r"|\bisf\b|\btgf\b|%",
    re.I,
)


def _fold_label(name: str) -> str:
    bare = unicodedata.normalize("NFKD", str(name))
    return re.sub(r"[^a-z]", "",
                  "".join(ch for ch in bare if not unicodedata.combining(ch)).lower())


def region_subtotals(series: pd.DataFrame) -> pd.DataFrame:
    """Each printed region row beside the sum of the governorates it is made of.

    A region that disagrees with its own parts is a misread on one side or the other, and
    the sum cannot say which. Rather than drop either, both figures are published with the
    gap, so a reader knows exactly which cells not to trust.

    ``additive`` says whether the check applies at all: a rate, an index or an average is
    not the sum of its parts, so those rows are reported with ``agrees`` left empty rather
    than counted as failures. That is settled from the title where the wording gives it
    away and from the numbers otherwise, since a column can be an average inside a table
    of counts.
    """
    folded = series.row_label.map(_fold_label)
    key = ["title_fr", "panel", "column_label", "year"]
    frame = series.assign(folded=folded)
    checks = []
    for region, members in GRANDES_REGIONS.items():
        printed = frame[frame.folded.eq(_fold_label(region))]
        printed = printed.drop_duplicates(key).set_index(key).value.rename("printed")
        wanted = {_fold_label(name) for name in members}
        parts = frame[frame.folded.isin(wanted)]
        summed = parts.groupby(key).value.agg(parts_sum="sum", found="size")
        summed = summed[summed.found.eq(len(members))]
        joined = summed.join(printed, how="inner").reset_index()
        joined.insert(0, "region", region)
        joined["parts_mean"] = joined.parts_sum / len(members)
        checks.append(joined)

    result = pd.concat(checks, ignore_index=True)
    result["gap"] = (result.parts_sum - result.printed).abs()
    allowed = (SUBTOTAL_TOLERANCE * result.printed.abs()).clip(lower=SUBTOTAL_FLOOR)

    # Wording is not enough to say what adds up. "Naissances selon le lieu d'accouchement"
    # reads as a count and its columns are counts -- except "Accouch. assisté", which is
    # the percentage assisted, and a region's is the mean of its governorates' rather than
    # their sum. So non-additivity is also read off the numbers: where the region equals
    # the *mean* of its parts and not their sum, it is an average. A misread landing within
    # 2% of the mean by chance would be excused wrongly, which is why this marks a row
    # rather than deleting it.
    by_name = result.title_fr.str.contains(NOT_ADDITIVE, na=False)
    like_mean = (result.parts_mean - result.printed).abs() <= allowed
    result["additive"] = ~(by_name | (like_mean & (result.gap > allowed)))
    result["agrees"] = (result.gap <= allowed).where(result.additive)
    columns = ["title_fr", "panel", "region", "column_label", "year",
               "parts_sum", "parts_mean", "printed", "gap", "additive", "agrees"]
    return result[columns].sort_values(columns[:5]).reset_index(drop=True)


def build() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """The four yearbook datasets: catalogue, series, coverage report and subtotal check."""
    raw, refused = extract()
    series, conflicts = reconcile(raw)
    index = catalogue()

    # All three datasets have to speak the same table names, or a title the series merged
    # is reported twice by the coverage table -- once as extracted, once as read but never
    # kept -- and the catalogue cites a name nothing else uses.
    canonical = dict(zip(series.table_title.map(_latin), series.title_fr, strict=True))
    index["table_title"] = index.table_title.map(lambda t: canonical.get(t, t))
    titles = raw.table_title.map(_latin).map(lambda t: canonical.get(t, t))
    per_table = raw.assign(title_fr=titles).groupby("title_fr").agg(
        editions=("edition", "nunique"), values_read=("value", "size"))
    kept = series.groupby("title_fr").size().rename("values_kept")
    bad = conflicts.groupby("title_fr").size().rename("values_in_conflict")
    coverage = per_table.join(kept).join(bad).fillna({"values_kept": 0,
                                                      "values_in_conflict": 0})
    coverage = coverage.astype({"values_kept": int, "values_in_conflict": int})
    coverage["status"] = "extracted"
    coverage.loc[coverage.values_in_conflict > 0, "status"] = "extracted with conflicts"

    # Tables present in the corpus that yielded nothing at all.
    missing = sorted(set(index.table_title) - set(coverage.index))
    if missing:
        extra = pd.DataFrame(
            {"editions": 0, "values_read": 0, "values_kept": 0, "values_in_conflict": 0,
             "status": "not extracted (header unreadable, or rows refused)"},
            index=pd.Index(missing, name="title_fr"),
        )
        coverage = pd.concat([coverage, extra])

    refused_reasons = (refused.assign(n=1).groupby("reason")["n"].sum()
                       if not refused.empty else pd.Series(dtype=int))
    coverage.attrs["refused"] = refused_reasons.to_dict()
    return (index, series, coverage.reset_index().sort_values("title_fr"),
            region_subtotals(series))


# ------------------------------------------------------- layout-driven column headers
#
# The two shapes above assume the column labels sit on one line. Much of the corpus does
# not oblige:
#
#   * **Nested headers.** Table 1.9 puts 2023 and 2022 across the top and Masculin /
#     Feminin / Mas-Fem under each, so six columns hang off two year cells.
#   * **Headers split over lines.** On the continuation page of table 1.2 the cells read
#     "TOTAL", "80 ans &+" and "79-75 74-70 ..." across three separate lines, and the
#     text order is not the reading order -- TOTAL is printed last and belongs first.
#
# Neither can be solved by reading a single line. Both fall out of the geometry, which
# `pdftotext -layout` preserves: a header cell governs the columns that sit beneath it.
# So the columns are located from the data rows, and each header line is cut into cells
# that claim the span from their own start to the next cell's start.
#
# This runs only where the single-line paths found nothing, so it cannot change what
# they already extract.

CELL_GAP = re.compile(r"\s{3,}")

# How many lines above the first data row can hold column labels. Everything further up
# is the title block, and sweeping it in produces labels like
# "gouvernorat au 1.7.2023 Unite : Le millier Masculin 59-55".
HEADER_WINDOW = 9

# Cells that are page furniture rather than column labels.
NOT_A_COLUMN = re.compile(
    r"^(unit[ée]|source|gouvernorat|r[ée]gion|d[ée]signation|libell[ée])\b", re.I
)


def _cells(line: str) -> list[tuple[int, str]]:
    """Header cells with their start column. Split on wide gaps, so "80 ans &+" is one.

    Arabic duplicates of each label, unit notes and the row-label heading are dropped:
    they sit in the same band as the columns but name the table, not a column.
    """
    out = []
    for match in re.finditer(r"\S(?:.*?\S)?(?=\s{3,}|$)", line):
        text = match.group().strip()
        if not text or len(text) > 24:
            continue
        if re.search(r"[\u0600-\u06ff]", text):
            continue  # the Arabic rendering of the same label, printed alongside it
        if not re.search(r"[A-Za-z0-9]", text):
            continue
        if NOT_A_COLUMN.match(text) or ":" in text:
            continue
        out.append((match.start(), text))
    return out


def _data_columns(rows: list[tuple[str, list, list]]) -> list[float] | None:
    """Centre x of each numeric column, from rows that all have the same width."""
    widths = collections.Counter(len(spans) for _, _, spans in rows)
    if not widths:
        return None
    width, count = widths.most_common(1)[0]
    if width < 2 or count < 4:
        return None
    centres = []
    for i in range(width):
        positions = [(s[i][0] + s[i][1]) / 2 for _, _, s in rows if len(s) == width]
        centres.append(sum(positions) / len(positions))
    return centres


def _label_columns(header_lines: list[str], centres: list[float]) -> list[str]:
    """Compose a label per column by stacking the header cells above it.

    How a line's cells map onto the columns depends on how many there are, and guessing
    one rule for all of them gets it wrong in both directions -- a spanning year that
    claims only one of its sub-columns, or a single-column label smeared across every
    column to its right.

    * As many cells as columns: one to one, in order.
    * A whole-number multiple: a nested header, so each cell takes an equal contiguous
      group. Two years above six columns means three each.
    * Anything else: the cells are walked left to right and each takes the next column
      that starts at or after it. Nearest-neighbour fails here -- labels are printed
      left-aligned at their column while the numbers under them are right-aligned, so a
      cell often sits closer to the previous column's digits than to its own.
    """
    parts: list[list[str]] = [[] for _ in centres]
    count = len(centres)
    for line in header_lines:
        cells = _cells(line)
        if not cells or len(cells) > count:
            continue
        if len(cells) == count:
            for index, (_, text) in enumerate(cells):
                parts[index].append(text)
        elif len(cells) > 1 and count % len(cells) == 0:
            span = count // len(cells)
            for position, (_, text) in enumerate(cells):
                for index in range(position * span, (position + 1) * span):
                    parts[index].append(text)
        else:
            index = 0
            for start, text in cells:
                while index < count and centres[index] < start - 3:
                    index += 1
                if index >= count:
                    break
                parts[index].append(text)
                index += 1
    return [" ".join(dict.fromkeys(p)) for p in parts]


def parse_page_layout(edition: int, page_index: int, text: str) -> list[dict]:
    """Read a page whose header spans several lines or nests, using column geometry."""
    lines = text.split("\n")
    heading_at = next((i for i, line in enumerate(lines) if _heading(line)), None)
    if heading_at is None:
        return []
    number, title = _heading(lines[heading_at])

    candidates: list[tuple[int, str, list, list]] = []
    for i, line in enumerate(lines[heading_at + 1:], heading_at + 1):
        parts = split_row(line)
        if parts is None:
            continue
        label, values, _ = parts
        if len(label) < 3 or not re.search(r"[A-Za-zÀ-ÿ]{3}", label) or label[-1].isdigit():
            continue
        if NOT_A_ROW.search(label):
            continue  # a unit statement or page footer, not a row -- as in parse_page
        spans = [(m.start(), m.end()) for m in NUMBER.finditer(line)]
        if len(spans) != len(values):
            continue
        candidates.append((i, label, values, spans))

    # The table's width is whatever most rows agree on. Establishing it first matters:
    # a header line like "TOTAL   80 ans &+" or "Gouvernorat  2023  2022" parses as a
    # perfectly good one- or two-value row, and taking it for data would put the header
    # window above the real column labels and leave the columns unnamed.
    centres = _data_columns([(lbl, v, s) for _, lbl, v, s in candidates])
    if centres is None:
        return []
    width = len(centres)
    rows = [(lbl, v, s) for _, lbl, v, s in candidates if len(v) == width]
    first_data = next((i for i, _, v, _ in candidates if len(v) == width), None)
    if first_data is None:
        return []
    window = [line for line in lines[max(heading_at + 1, first_data - HEADER_WINDOW):first_data]
              if line.strip()]
    labels = _label_columns(window, centres)
    # The caption sits inside the header window here rather than just above it: the
    # continuation pages carrying the older age bands set "Gouvernorat   Masculin" two
    # lines above their column labels. Without this the second half of every population
    # table has no sex against it, which is the fault this was meant to repair.
    #
    panel = next((found for line in window if (found := _caption_on(line))), "")
    if any(not label for label in labels):
        return []  # an unlabelled column is not worth guessing at
    if len(set(labels)) != len(labels):
        return []  # repeated labels mean the geometry was misread

    # A nested header composes to "2023 Feminin": the year is the outer cell, and it
    # dates that column even though the label is no longer a bare year.
    year = _page_year(text)
    # A school-year label reads its own start year; a nested header's outer cell is a
    # bare leading year. Checking the school year first matters, because "2000-99" also
    # begins with four digits and would otherwise be dated a year late.
    years: list[int | None] = []
    for label in labels:
        school = _school_year_header(f"{label} {label}")
        if school:
            years.append(school[0][1])
            continue
        match = re.match(r"^((?:19|20)\d\d)\b(?!-)", label)
        years.append(int(match.group(1)) if match else None)
    if year is None and not all(y is not None for y in years):
        return []

    out = []
    for label, values, _ in rows:
        kind = "aggregate" if SUBTOTAL.match(label) else "data"
        out.extend(
            {
                "edition": edition,
                "table_number": number,
                "table_title": title,
                "page": page_index + 1,
                "row_label": label,
                "row_kind": kind,
                "panel": panel,
                "column_label": column,
                "year": column_year if column_year is not None else year,
                "value": value,
                "provisional": False,
                "label_inferred": False,
            }
            for column, column_year, value in zip(labels, years, values, strict=True)
        )
    return out
