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

The check that scales is cross-edition agreement. Each edition carries a five-year
window, so 24 of the 26 years in the corpus appear in two or more editions -- most in
five. Where two editions report the same table, row and year they must agree, which is
what catches the doubled-integer columns that no local rule can.
"""

from __future__ import annotations

import collections
import re
import subprocess
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

# Rows that are aggregates of other rows. Kept, but marked, because summing them with
# their own components double-counts -- and because they are free arithmetic checks.
SUBTOTAL = re.compile(
    r"^(t\s*o\s*t\s*a\s*l|ensemble|sous\s*[- ]?\s*total|dont\b|district"
    r"|nord\s*-|centre\s*-|sud\s*-|grand\s+tunis|pib)\b",
    re.I,
)


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
    matches = list(NUMBER_OR_NIL.finditer(line))
    if not matches:
        return None
    start, end = matches[0].start(), matches[-1].end()
    interior = line[start:end]
    residue = NUMBER_OR_NIL.sub("", interior).strip()
    provisional = "*" in residue
    if residue.replace("*", "").strip():
        return None
    label = line[:start].strip(" .:-\t")
    values = [0.0 if m.group().strip() == "-" else float(m.group().replace(" ", ""))
              for m in matches]
    return label, values, provisional


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

        block: list[dict] = []
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
            label, values, provisional = parts
            inferred = False
            if len(label) < 3 or not re.search(r"[A-Za-zÀ-ÿ]{3}", label):
                # No label beside the numbers. It may be printed above them, or wrapped
                # around them -- recoverable, but weaker than a label read off the same
                # line, so the rows it yields say so.
                if label or len(values) != width:
                    continue
                candidate = _inferred_label(lines, offset)
                if candidate is None:
                    continue
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
            if label[-1].isdigit():
                reason = "label ends in a digit (footnote marker shifts the columns)"
            elif len(values) != width:
                reason = f"{len(values)} values for {width} columns"
            if reason:
                block_refused.append({"edition": edition, "table_number": number,
                                      "row_label": label[:80], "reason": reason})
                continue

            kind = "aggregate" if SUBTOTAL.match(label) else "data"
            block.extend(
                {
                    "edition": edition,
                    "table_number": number,
                    "table_title": title,
                    "page": page_index + 1,
                    "row_label": label,
                    "row_kind": kind,
                    "column_label": column,
                    "year": column_year,
                    "value": value,
                    "provisional": provisional,
                    "label_inferred": inferred,
                }
                for column, column_year, value in zip(columns, column_years, values,
                                                      strict=True)
            )

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
    key = ["title_fr", "row_label", "column_label", "year"]

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

    columns = ["table_number", "table_title", "title_fr", "row_label", "row_kind",
               "column_label", "year", "value", "provisional", "label_inferred",
               "n_editions", "agreement", "edition", "page"]
    clean = clean[columns].sort_values(["title_fr", "row_label", "year"])
    return clean.reset_index(drop=True), conflicts.reset_index(drop=True)


def build() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """The three yearbook datasets: catalogue, reconciled series, coverage report."""
    raw, refused = extract()
    series, conflicts = reconcile(raw)
    index = catalogue()

    per_table = raw.assign(title_fr=raw.table_title.map(_latin)).groupby("title_fr").agg(
        editions=("edition", "nunique"), values_read=("value", "size")
    )
    kept = series.groupby("title_fr").size().rename("values_kept")
    bad = conflicts.groupby("title_fr").size().rename("values_in_conflict")
    coverage = per_table.join(kept).join(bad).fillna({"values_kept": 0,
                                                      "values_in_conflict": 0})
    coverage = coverage.astype({"values_kept": int, "values_in_conflict": int})
    coverage["status"] = "extracted"
    coverage.loc[coverage.values_in_conflict > 0, "status"] = "extracted with conflicts"

    # Tables present in the corpus that yielded nothing at all.
    seen = set(index.table_title)
    missing = sorted(seen - set(coverage.index))
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
    return index, series, coverage.reset_index().sort_values("title_fr")


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
                "column_label": column,
                "year": column_year if column_year is not None else year,
                "value": value,
                "provisional": False,
                "label_inferred": False,
            }
            for column, column_year, value in zip(labels, years, values, strict=True)
        )
    return out
