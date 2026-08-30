"""Consumer price series read out of the INS statistical yearbooks.

Two tables, both from the 2023 edition, both located by their French title because
table *numbers* move between editions (this table is 13.6 in the 2023 edition and 13.7
in 2010).

``cpi_annual`` reads "Evolution de l'indice general des prix a la consommation familiale
selon les differentes annees de base", which carries 1999-2023 on eight base years in a
single page -- so the long price series needs no splicing across editions.

``cpi_by_division`` reads "Evolution de l'indice general des prix a la consommation
familiale", which gives the twelve COICOP divisions for 2021-2023 on base 2015 = 100,
with the weights INS used. Because both endpoints of 2015 -> 2021 are EBCNV survey
waves, this one table is enough to set price change beside budget-share change without
chaining anything.

Two things in these PDFs that will silently corrupt a naive parse:

* **Bold columns render every glyph twice.** The base-2010 column prints ``7700..00``
  for 70.0. ``_undouble`` detects and repairs it rather than guessing.
* **Thousands are separated by a space**, so ``1 013.5`` is one number, not two.

The extracted general index is checked against the division table's "Ensemble" row,
which is published separately and must agree.
"""

from __future__ import annotations

import re

import pandas as pd
import pdfplumber

from .config import raw_path

CPI_ANNUAL_TITLE = "selon les différentes années de base"
# The title wraps after "prix" on most editions' pages, so only the first line of it can
# be matched. That alone would also catch table 13.4, "Variations annuelles de l'indice
# général des prix", which is why the page must carry "Evolution" and the weight column.
CPI_DIVISION_TITLE = "Evolution de l’indice général des prix"

EDITION = 2023  # the edition the annual table is read from

# Every edition printing the division table in its three-years-plus-weight form. The
# 2012 edition and earlier print a single year in a different shape and are left out.
CPI_DIVISION_EDITIONS: tuple[int, ...] = (2014, 2015, 2016, 2017, 2018,
                                          2019, 2020, 2021, 2022, 2023)

# Line-start anchors for the twelve COICOP divisions, in INS's own wording and order.
# Anchored at line start so a division is never confused with one of its sub-rows
# ("Transports" against "Services de transport").
DIVISIONS: tuple[tuple[int, str, str], ...] = (
    # Anchors stop where the label wraps. Older editions break "Produits alimentaires et
    # boissons / non alcoolisees" and "Articles d'habillement et / chaussures" across two
    # lines with the numbers in between, so matching the full name finds nothing there.
    (1, r"Produits alimentaires et boissons", "Food and non-alcoholic beverages"),
    (2, r"Boissons alcoolisées et tabac", "Alcoholic beverages and tobacco"),
    (3, r"Articles d'habillement et", "Clothing and footwear"),
    (4, r"Logement\. eau\. gaz\. électricité et", "Housing, water, gas and electricity"),
    (5, r"Meubles\. articles de ménage et", "Furnishings and household maintenance"),
    (6, r"Santé", "Health"),
    (7, r"Transports", "Transport"),
    (8, r"Communications", "Communication"),
    (9, r"Loisirs et culture", "Recreation and culture"),
    (10, r"Enseignement", "Education"),
    (11, r"Restaurants et hôtels", "Restaurants and hotels"),
    (12, r"Biens et services divers", "Miscellaneous goods and services"),
)

TOTAL_ANCHOR = r"Ensemble"

_TRIPLE = re.compile(r"(\d[\d ]*\.\d+)\s+(\d[\d ]*\.\d+)\s+(\d[\d ]*\.\d+)\s+(\d{2,6})\b")


def _undouble(token: str) -> str:
    """Repair a bold-rendered number whose every glyph was emitted twice.

    ``7700..00`` -> ``70.0``. Guarded twice: the token must contain the doubled decimal
    point, which is the actual signature of the fault, *and* every character must be
    doubled. Without the first guard an honest integer like ``1100`` would be read as
    ``10``, which is exactly the kind of silent corruption this repo exists to avoid.
    """
    if ".." not in token:
        return token
    if len(token) % 2 == 0 and all(token[i] == token[i + 1] for i in range(0, len(token), 2)):
        return token[::2]
    return token


def _number(token: str) -> float:
    """Parse one INS number: repair doubled glyphs, drop the space thousands separator."""
    return float(_undouble(token.replace(" ", "")))


def _page_text(pdf: pdfplumber.PDF, title: str) -> list[str]:
    """Every page whose text contains ``title``, as text blocks."""
    return [t for p in pdf.pages if title in (t := p.extract_text() or "")]


def cpi_annual() -> pd.DataFrame:
    """Annual consumer price index, 1999-2023, on each of INS's eight base years."""
    with pdfplumber.open(raw_path(f"annuaire_{EDITION}")) as pdf:
        pages = _page_text(pdf, CPI_ANNUAL_TITLE)
    if len(pages) != 1:
        raise ValueError(f"expected one page carrying {CPI_ANNUAL_TITLE!r}, found {len(pages)}")

    lines = [ln.strip() for ln in pages[0].split("\n")]

    # The header is the run of base years; the data rows end with the year they describe.
    bases: list[int] | None = None
    rows = []
    for line in lines:
        tokens = line.split()
        if bases is None:
            if len(tokens) >= 6 and all(re.fullmatch(r"(19|20)\d\d", t) for t in tokens):
                bases = [int(t) for t in tokens]
            continue
        if not re.search(r"\b(19|20)\d\d$", line):
            continue
        year = int(line[-4:])
        # Repair doubled glyphs before matching numbers -- ``7700..00`` matches no
        # sane number pattern, so a naive parse silently drops the whole column.
        body = " ".join(_undouble(tok) for tok in line[:-4].split())
        values = [_number(m) for m in re.findall(r"\d[\d ]*\.\d+", body)]
        if len(values) != len(bases):
            raise ValueError(f"{year}: read {len(values)} values, expected {len(bases)}")
        rows.extend(
            {"year": year, "base_year": base, "index": value}
            for base, value in zip(bases, values, strict=True)
        )

    if bases is None:
        raise ValueError("could not find the base-year header row")
    frame = pd.DataFrame(rows).sort_values(["base_year", "year"]).reset_index(drop=True)

    # Each base year must read exactly 100.0 in its own year -- the cheapest possible
    # check that the columns were not transposed.
    for base in bases:
        own = frame[(frame.base_year == base) & (frame.year == base)]
        if not own.empty and round(float(own["index"].iloc[0]), 1) != 100.0:
            raise ValueError(f"base {base} reads {own['index'].iloc[0]} in {base}, expected 100.0")

    frame["source_key"] = f"annuaire_{EDITION}"
    frame["source_table"] = "13.6"
    return frame


def _division_page(edition: int) -> str:
    """The page of one edition carrying the division table, as text."""
    with pdfplumber.open(raw_path(f"annuaire_{edition}")) as pdf:
        pages = _page_text(pdf, CPI_DIVISION_TITLE)
    text = "\n".join(p for p in pages
                     if "années de base" not in p and "Pondération" in p)
    if not text:
        raise ValueError(f"could not find the division price table in {edition}")
    return text


def _division_header(text: str, edition: int) -> tuple[tuple[int, ...], int]:
    """The three years the columns stand for, and the base year they are indexed on.

    Both are read from the page rather than assumed. The base moves -- the 2014 edition
    prints base 2010 and the 2018 edition base 2015 -- and a series spliced across that
    change without noticing would be a different number every few years.
    """
    # "Base )2010 = 100(" -- the brackets come out reversed on these bilingual pages.
    base = re.search(r"Base\s*[()]?\s*((?:19|20)\d\d)\s*=\s*100", text)
    if base is None:
        raise ValueError(f"no base year printed on the division page of {edition}")
    for line in text.split("\n"):
        tokens = line.split()
        if len(tokens) == 3 and all(re.fullmatch(r"(19|20)\d\d", t) for t in tokens):
            years = tuple(int(t) for t in tokens)
            if years != tuple(sorted(years, reverse=True)):
                raise ValueError(f"{edition}: year columns {years} are not descending")
            return years, int(base.group(1))
    raise ValueError(f"no run of three year columns on the division page of {edition}")


def cpi_by_division_edition(edition: int) -> pd.DataFrame:
    """COICOP-division price index from one edition: three years and INS's weights."""
    text = _division_page(edition)
    years, base_year = _division_header(text, edition)

    rows = []
    for code, anchor, label_en in (*DIVISIONS, (0, TOTAL_ANCHOR, "All items")):
        match = re.search(rf"^{anchor}", text, re.MULTILINE)
        if match is None:
            raise ValueError(f"{edition}: division {code} ({label_en}) not found")
        found = _TRIPLE.search(text, match.end())
        if found is None:
            raise ValueError(f"{edition}: division {code} ({label_en}) has no numbers")
        weight = int(found.group(4))
        for year, token in zip(years, found.groups()[:3], strict=True):
            rows.append(
                {
                    "year": year,
                    "function_code": code,
                    "function": label_en,
                    "index": _number(token),
                    "weight_per_100000": weight,
                    "base_year": base_year,
                    "source_key": f"annuaire_{edition}",
                }
            )

    frame = pd.DataFrame(rows)
    weights = frame[frame.function_code != 0].drop_duplicates("function_code")
    total = int(weights["weight_per_100000"].sum())
    if total != 100_000:
        raise ValueError(f"{edition}: division weights sum to {total}, expected 100000")
    return frame


def cpi_by_division() -> pd.DataFrame:
    """COICOP-division price index for 2012-2023, from every edition that prints it.

    Each edition carries three years, so ten editions overlap two years deep and every
    cell but the outermost is printed two or three times. They have to agree: where two
    editions report the same division, year and base differently, one of them was misread
    and the build stops rather than picking a winner.
    """
    frames = [cpi_by_division_edition(edition) for edition in CPI_DIVISION_EDITIONS]
    frame = pd.concat(frames, ignore_index=True)

    key = ["year", "function_code", "base_year"]
    spread = frame.groupby(key)["index"].nunique()
    disputed = spread[spread > 1]
    if not disputed.empty:
        first = frame.set_index(key).loc[disputed.index[0]]
        raise ValueError(
            f"editions disagree on {disputed.index[0]}: "
            f"{sorted(first['index'].unique())}"
        )

    frame["n_editions"] = frame.groupby(key)["index"].transform("size")
    # The newest edition printing a cell is the authority for its weight, which INS
    # restates when it rebases.
    frame = (frame.sort_values("source_key")
             .drop_duplicates(key, keep="last")
             .sort_values(["base_year", "year", "function_code"]))
    frame["source_table"] = "13.7"
    return frame.reset_index(drop=True)


def build() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Both price tables, cross-checked against each other.

    The two tables are published separately, so the general index in one must equal the
    "Ensemble" row of the other. If INS ever revises one and not the other, this fails
    rather than quietly producing two versions of the same series.
    """
    annual, divisions = cpi_annual(), cpi_by_division()
    ensemble = divisions[divisions.function_code == 0]
    checked = 0
    # Plain dicts rather than itertuples: the column is called "index", which collides
    # with the namedtuple's own field and gets silently renamed.
    for row in ensemble.to_dict("records"):
        left = annual[(annual.year == row["year"]) & (annual.base_year == row["base_year"])]
        if left.empty:
            continue  # the annual table carries eight bases, not every one of them
        printed = float(left["index"].iloc[0])
        if round(printed, 1) != round(float(row["index"]), 1):
            raise ValueError(
                f"{row['year']} (base {row['base_year']}): general index {printed} "
                f"disagrees with the division table's Ensemble row {row['index']}"
            )
        checked += 1
    if checked < 10:
        raise ValueError(f"only {checked} years could be cross-checked, expected 10 or more")
    return annual, divisions
