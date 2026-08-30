"""Poverty and inequality by region, 2000 to 2010, from INS's methodology report.

``mesure_pauvrete_inegalites_2000_2010.pdf`` is the report that accompanied the 2010
revision of Tunisia's poverty line. It is the only document in the corpus that is wholly
in French, and it carries twenty numbered tables of which several exist nowhere else:
consumption per head by region for 2000, 2005 *and 2010*, poverty incidence by region on
both the low and high lines, and Gini coefficients by region with their standard errors.

The 2010 column is the reason to read it. ``tn_consumption_panel`` carries regional mean
expenditure for every wave except 2010, which is why the product-by-region extractor has
to recover that wave's anchor from the survey volume's own summary page. This report
prints it directly.

**Two layouts, and only some of them are safe to read.** Tables 3, 4 and 6 put a row on
one line: label, then a value per year. Tables 7, 8 and 17 print the values on the line
above the label and the standard errors on the line below. Table 17 does that identically
for every row, so it can be read exactly. Tables 7 and 8 wrap irregularly -- a region's
two values can land on different lines, with its standard error beside the label -- and
which number belongs to which wave cannot be settled from the layout, so they are left
out rather than guessed at.

**These figures are not the panel's.** INS revised the poverty line in 2010 and recomputed
2000 and 2005 on the new basis, so the report disagrees with what those waves published at
the time on purpose: Grand Tunis in 2005 is 14.6% poor here against 12.3% in the panel.
Every row carries ``basis = "2010 methodology"`` so the two are never silently mixed.

The Gini figures are corroborated: table 11 of the 2010 survey volume prints the same
seven regional coefficients, and they agree to the last digit. That agreement also settles
a reading the Arabic volume left ambiguous, since ``pdftotext`` reverses its header and
leaves the year order in doubt.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass

import pandas as pd

from .config import INTERIM_DIR, raw_path

SOURCE = "mesure_pauvrete_2000_2010"

REGIONS = {
    "Grand Tunis": "Grand Tunis", "Nord Est": "North East", "Nord Ouest": "North West",
    "Centre Est": "Centre East", "Centre Ouest": "Centre West",
    "Sud Est": "South East", "Sud Ouest": "South West", "Tunisie": "Tunisia",
}
STRATA = {
    "Grandes villes": "large cities", "Moyennes communes": "medium communes",
    "Zones non-communales": "non-communal areas", "Communal": "communal",
    "Non communal": "non communal", "Tunisie": "Tunisia",
}

# French decimals use a comma, and a bracketed number is a standard error rather than a
# value. Keeping the two apart is what stops a standard error being read as an estimate.
VALUE = re.compile(r"(?<!\()\b\d{1,5}(?:[.,]\d+)?\b(?!\s*\))")
BRACKETED = re.compile(r"\((\d{1,3}(?:[.,]\d+)?)\)")

WAVES = (2000, 2005, 2010)


@dataclass(frozen=True)
class Table:
    """One table of the report, and how to read it."""

    number: int
    caption: str
    indicator: str
    unit: str
    labels: dict[str, str]
    inline: bool          # values on the label's own line
    waves: tuple[int, ...] = WAVES


TABLES = (
    Table(3, "Évolution de l’agrégat de consommation par tête selon les régions",
          "consumption_pc_mean", "dinars per person per year", REGIONS, inline=True),
    Table(4, "Évolution de l’agrégat de consommation par tête selon le milieu",
          "consumption_pc_mean", "dinars per person per year", STRATA, inline=True),
    Table(6, "Seuils de pauvreté et de pauvreté extrême",
          "poverty_line", "dinars per person per year", STRATA, inline=True),
    # Tables 7 and 8 (poverty incidence) are deliberately not read. They use the same
    # stacked shape as 17 but wrap irregularly -- a region's two values can land on
    # different lines with its standard error beside the label -- so which number belongs
    # to which wave cannot be settled from the layout. Table 17 wraps identically for
    # every row, which is why it can be.
    Table(17, "Les indices d’inégalité de Gini selon la région géographique",
          "gini", "index 0-1", REGIONS, inline=False),   # total expenditure, not
    # the annual-consumption Gini printed beside it
)


def report_lines() -> list[str]:
    """The report as text, cached under data/interim."""
    cache = INTERIM_DIR / f"{SOURCE}.txt"
    if not cache.exists():
        INTERIM_DIR.mkdir(parents=True, exist_ok=True)
        out = subprocess.run(["pdftotext", "-layout", str(raw_path(SOURCE)), "-"],
                             capture_output=True, check=True)
        cache.write_text(out.stdout.decode("utf-8", "replace"))
    return cache.read_text().split("\n")


def _number(text: str) -> float:
    return float(text.replace(",", ".").replace(" ", ""))


def table_body(lines: list[str], table: Table) -> list[str]:
    """The lines of one table: from its caption to whatever ends it."""
    opening = re.compile(rf"^\s*Tableau\s*{table.number}\s*:")
    start = next((i for i, line in enumerate(lines) if opening.match(line)), None)
    if start is None:
        raise RuntimeError(f"table {table.number} not found in the report")
    body = []
    for line in lines[start + 1:]:
        if re.match(r"^\s*(Tableau|Graphique|Figure)\s*\d", line):
            break
        body.append(line)
    return body


def read_inline(body: list[str], table: Table) -> list[dict]:
    """Rows whose values sit on the label's own line."""
    rows = []
    for line in body:
        label = next((k for k in table.labels if line.strip().startswith(k)), None)
        if label is None:
            continue
        rest = line.strip()[len(label):]
        values = [_number(m.group()) for m in VALUE.finditer(rest)]
        if len(values) < len(table.waves):
            continue
        # A trailing growth rate follows the years in tables 3 and 4; the years come
        # first, so taking the leading run keeps it out.
        for wave, value in zip(table.waves, values[:len(table.waves)], strict=True):
            rows.append({"geography": table.labels[label], "year": wave, "value": value,
                         "standard_error": None})
    return rows


def read_stacked(body: list[str], table: Table) -> list[dict]:
    """Rows printed as a line of values, then the label, then the standard errors.

    The layout is rigid once you see it, so this reads the two neighbouring lines
    exactly rather than sweeping a window: a window picks up the row above's standard
    errors and puts the waves out of order, which is how Grand Tunis first came out with
    2000 and 2005 swapped.
    """
    rows = []
    for index, line in enumerate(body):
        label = next((k for k in table.labels if line.strip() == k), None)
        if label is None or index == 0:
            continue
        values = [_number(m.group()) for m in VALUE.finditer(body[index - 1])]
        below = body[index + 1] if index + 1 < len(body) else ""
        errors = [_number(m.group(1)) for m in BRACKETED.finditer(below)]
        # Several of these tables set a second measure beside the first -- table 17 puts
        # the Gini of annual consumption next to the Gini of total expenditure, six
        # numbers to a line. Only the headline measure is carried, and the codebook says
        # so; the leading run is it.
        if len(values) < len(table.waves):
            continue
        values = values[:len(table.waves)]
        for position, wave in enumerate(table.waves):
            rows.append({
                "geography": table.labels[label], "year": wave,
                "value": values[position],
                "standard_error": errors[position] if position < len(errors) else None,
            })
    return rows


RANGES = {"gini": (0.0, 1.0), "poverty_rate": (0.0, 100.0),
          "consumption_pc_mean": (100.0, 20000.0), "poverty_line": (100.0, 20000.0)}


def _check(frame: pd.DataFrame) -> None:
    """What the report has to satisfy on its own terms, having no outside referee."""
    for table in TABLES:
        got = frame[frame.source_table == f"Tableau {table.number}"]
        # Tables draw on different subsets of the same label vocabulary -- table 4 has no
        # "Zones non-communales" row -- so what has to hold is not a total count but that
        # every row found carries a value for every wave, and that enough rows were found
        # to be a table at all.
        per_label = got.groupby("geography").year.nunique()
        if len(per_label) < 3:
            raise RuntimeError(f"Tableau {table.number}: only {len(per_label)} rows read")
        short = per_label[per_label != len(table.waves)]
        if not short.empty:
            raise RuntimeError(
                f"Tableau {table.number}: {dict(short)} do not carry all "
                f"{len(table.waves)} waves")
    for indicator, (low, high) in RANGES.items():
        bad = frame[(frame.indicator == indicator)
                    & ~frame.value.between(low, high)]
        if not bad.empty:
            raise RuntimeError(f"{indicator}: {len(bad)} values outside [{low}, {high}]")
    # A national figure that sits outside every region it aggregates is a misread row.
    for (indicator, year, source), group in frame.groupby(
            ["indicator", "year", "source_table"]):
        national = group[group.geography == "Tunisia"].value
        regions = group[group.geography != "Tunisia"].value
        if national.empty or regions.empty:
            continue
        if not regions.min() - 1e-9 <= national.iloc[0] <= regions.max() + 1e-9:
            raise RuntimeError(
                f"{indicator} {year} ({source}): Tunisia {national.iloc[0]} lies outside "
                f"the regions [{regions.min()}, {regions.max()}]")


def build() -> pd.DataFrame:
    """Every table this report yields that can be read without guessing."""
    lines = report_lines()
    frames = []
    for table in TABLES:
        body = table_body(lines, table)
        rows = read_inline(body, table) if table.inline else read_stacked(body, table)
        if not rows:
            raise RuntimeError(f"table {table.number} yielded no rows")
        frame = pd.DataFrame(rows)
        frame.insert(0, "indicator", table.indicator)
        frame["unit"] = table.unit
        frame["source_table"] = f"Tableau {table.number}"
        frames.append(frame)

    data = pd.concat(frames, ignore_index=True)
    data = data.drop_duplicates(["indicator", "geography", "year", "source_table"])
    _check(data)
    # Everything here is on the 2010 poverty line, including the recomputed 2000 and
    # 2005 columns. The panel's rows are as each wave published them.
    data["basis"] = "2010 methodology"
    columns = ["indicator", "geography", "year", "value", "standard_error", "unit",
               "basis", "source_table"]
    return data[columns].sort_values(columns[:3]).reset_index(drop=True)
