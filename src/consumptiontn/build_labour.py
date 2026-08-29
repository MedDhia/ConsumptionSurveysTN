"""Unemployment rates read out of the INS statistical yearbooks.

Two tables per edition -- unemployment by sex and by education level, both surveyed in
May -- spliced across three editions into 2011-2023.

**This series does not span the revolution.** The 2005, 2010 and 2012 editions carry no
unemployment table at all (checked, not assumed: the only match for "chômage" in those
volumes is a publications catalogue). 2011 is the earliest year INS puts in these
yearbooks, so anything built on it describes the period *since* the revolution and
cannot compare across it.

Editions overlap by design: each carries five years, so 2015 appears in both the 2015 and
2019 editions and 2019 in both the 2019 and 2023 editions. ``build`` requires the
overlapping years to agree exactly. That is the check that the right column was read --
a column offset would show up immediately as a mismatch rather than as a plausible
wrong number.
"""

from __future__ import annotations

import re

import pandas as pd
import pdfplumber

from .config import raw_path

EDITIONS = (2015, 2019, 2023)

BY_EDUCATION = "Taux de chômage selon le niveau éducatif"
BY_SEX = "Taux de chômage selon le sexe"

# INS's own row labels, including its consistent misspelling of "Supérieur".
EDUCATION_ROWS = {
    "Sans niveau": "none",
    "Primaire": "primary",
    "Secondaire": "secondary",
    "Supèrieur": "higher",
    "Total": "all",
}
SEX_ROWS = {"Masculin": "male", "Feminin": "female", "Total": "all"}


def _candidates(pdf: pdfplumber.PDF, title: str) -> list[str]:
    """Every page carrying the title, from the title line onward.

    There is always more than one: the table of contents lists the title too, and in
    some editions it comes first. Returning all of them lets the caller take the first
    that actually parses rather than trusting page order.
    """
    found = []
    for page in pdf.pages:
        text = page.extract_text() or ""
        index = text.find(title)
        if index != -1:
            found.append(text[index:])
    if not found:
        raise ValueError(f"{title!r} not found")
    return found


def _parse(text: str, rows: dict[str, str], breakdown: str, edition: int) -> list[dict]:
    """Read the year header, then one row per label."""
    years: list[int] | None = None
    for line in text.split("\n")[1:]:
        # The header is a bare run of years; 2014 carries an asterisk footnote marker.
        tokens = line.strip().split()
        if tokens and all(re.fullmatch(r"(19|20)\d\d\*?", t) for t in tokens):
            years = [int(t.rstrip("*")) for t in tokens]
            break
    if years is None:
        raise ValueError(f"{edition} {breakdown}: no year header")

    out = []
    for label, name in rows.items():
        match = re.search(rf"^{re.escape(label)}\s+((?:\d+\.\d+\s+){{{len(years)}}})", text, re.M)
        if match is None:
            raise ValueError(f"{edition} {breakdown}: row {label!r} not found")
        values = [float(v) for v in match.group(1).split()]
        out.extend(
            {
                "year": year,
                "breakdown": breakdown,
                "group": name,
                "unemployment_rate": value,
                "source_key": f"annuaire_{edition}",
                "source_table": "6.1.3" if breakdown == "education" else "6.1.2",
            }
            for year, value in zip(years, values, strict=True)
        )
    return out


def _parse_any(texts: list[str], rows: dict[str, str], breakdown: str, edition: int) -> list[dict]:
    """Parse the first candidate page that yields a complete table."""
    errors = []
    for text in texts:
        try:
            return _parse(text, rows, breakdown, edition)
        except ValueError as exc:
            errors.append(str(exc))
    raise ValueError(f"{edition} {breakdown}: no page parsed; tried {len(texts)}: {errors}")


def read_edition(edition: int) -> pd.DataFrame:
    """Both unemployment tables from one edition."""
    with pdfplumber.open(raw_path(f"annuaire_{edition}")) as pdf:
        rows = _parse_any(_candidates(pdf, BY_EDUCATION), EDUCATION_ROWS, "education", edition)
        rows += _parse_any(_candidates(pdf, BY_SEX), SEX_ROWS, "sex", edition)
    return pd.DataFrame(rows)


def build() -> pd.DataFrame:
    """Unemployment 2011-2023, spliced across editions, overlaps verified.

    Where two editions carry the same year they must report the same rate. A mismatch
    means a column was misread, so it raises rather than silently preferring one.
    """
    frames = [read_edition(edition) for edition in EDITIONS]
    everything = pd.concat(frames, ignore_index=True)

    key = ["year", "breakdown", "group"]
    spread = everything.groupby(key)["unemployment_rate"].agg(["min", "max", "size"])
    disagreeing = spread[(spread["max"] - spread["min"]).round(6) > 0]
    if not disagreeing.empty:
        raise ValueError(f"editions disagree on overlapping years:\n{disagreeing}")

    overlaps = int((spread["size"] > 1).sum())
    if overlaps == 0:
        raise ValueError("no overlapping years between editions -- the splice is unchecked")

    # Keep the latest edition's copy of each year: INS revises, and the newest volume
    # carries the revision.
    everything = everything.sort_values("source_key")
    return (
        everything.drop_duplicates(key, keep="last")
        .sort_values(["breakdown", "group", "year"])
        .reset_index(drop=True)
    )
