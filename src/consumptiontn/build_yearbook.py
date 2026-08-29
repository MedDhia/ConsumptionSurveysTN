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

# A bare run of years, optionally footnote-marked. Five digits (2018 with footnote 6
# printed as "20186") deliberately does not match, so such headers are skipped.
YEAR = re.compile(r"^(?:19|20)\d\d\*?$")

TABLE_NUMBER = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){1,2})\s+(\S.*)$")

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
    matches = list(NUMBER.finditer(line))
    if not matches:
        return None
    start, end = matches[0].start(), matches[-1].end()
    interior = line[start:end]
    residue = NUMBER.sub("", interior).strip()
    provisional = "*" in residue
    if residue.replace("*", "").strip():
        return None
    label = line[:start].strip(" .:-\t")
    values = [float(m.group().replace(" ", "")) for m in matches]
    return label, values, provisional


def _year_header(line: str) -> list[int] | None:
    tokens = line.split()
    if len(tokens) < 2 or not all(YEAR.match(t) for t in tokens):
        return None
    return [int(t.rstrip("*")) for t in tokens]


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
    """Rows accepted and rows refused, from one page."""
    lines = text.split("\n")
    rows: list[dict] = []
    refused: list[dict] = []

    for i, line in enumerate(lines):
        years = _year_header(line.strip())
        if years is None:
            continue
        heading = _table_at(lines, i)
        if heading is None:
            continue
        number, title = heading

        for body in lines[i + 1:]:
            stripped = body.strip()
            if not stripped:
                continue
            if _year_header(stripped) is not None:
                break  # a second table starts on the same page
            parts = split_row(stripped)
            if parts is None:
                if NUMBER.search(stripped):
                    refused.append({"edition": edition, "table_number": number,
                                    "row_label": stripped[:60],
                                    "reason": "unparsed characters among the numbers"})
                continue
            label, values, provisional = parts
            # A label needs to be a name, not a stray glyph: "P" is what is left of
            # "Population" on the one page where Arabic-Indic digits are injected into
            # the French word.
            if len(label) < 3 or not re.search(r"[A-Za-zÀ-ÿ]{3}", label):
                continue

            reason = None
            if label[-1].isdigit():
                reason = "label ends in a digit (footnote marker shifts the columns)"
            elif len(values) != len(years):
                reason = f"{len(values)} values for {len(years)} year columns"
            if reason:
                refused.append({"edition": edition, "table_number": number,
                                "row_label": label[:80], "reason": reason})
                continue

            kind = "aggregate" if SUBTOTAL.match(label) else "data"
            rows.extend(
                {
                    "edition": edition,
                    "table_number": number,
                    "table_title": title,
                    "page": page_index + 1,
                    "row_label": label,
                    "row_kind": kind,
                    "year": year,
                    "value": value,
                    "provisional": provisional,
                }
                for year, value in zip(years, values, strict=True)
            )
    return rows, refused


def extract(editions: tuple[int, ...] = EDITIONS) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Every year-column table the corpus yields, plus the rows that were refused."""
    kept: list[dict] = []
    refused: list[dict] = []
    for edition in editions:
        for index, text in enumerate(edition_pages(edition)):
            page_rows, page_refused = parse_page(edition, index, text)
            kept.extend(page_rows)
            refused.extend(page_refused)
    series = pd.DataFrame(kept)
    if not series.empty:
        series = series.drop_duplicates(
            ["edition", "table_number", "row_label", "year"]
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
    key = ["title_fr", "row_label", "year"]

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
               "year", "value", "provisional", "n_editions", "agreement",
               "edition", "page"]
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
             "status": "not extracted (shape not year-columns, or rows refused)"},
            index=pd.Index(missing, name="title_fr"),
        )
        coverage = pd.concat([coverage, extra])

    refused_reasons = (refused.assign(n=1).groupby("reason")["n"].sum()
                       if not refused.empty else pd.Series(dtype=int))
    coverage.attrs["refused"] = refused_reasons.to_dict()
    return index, series, coverage.reset_index().sort_values("title_fr")
