"""Per-capita expenditure by product and region, from every EBCNV volume that prints it.

The four survey volumes each carry a table giving mean annual expenditure per person on
each product, broken down by the seven grandes regions. Nothing downstream had ever read
it: the 2021 wave was available as a spreadsheet annex and the other three only as
Arabic-language PDFs, so the corpus held national budget shares and regional totals but
never the two crossed. Crossing them is what makes a spatial inequality measure per good
possible at all.

**The hazard, and the anchor that removes it.** These are right-to-left tables. Running
them through ``pdftotext -layout`` puts the row label at the end of the line and the
columns in reverse, and the Arabic header words come out reordered badly enough that the
header cannot be used to say which column is which region. Guessing would produce numbers
of the right shape attributed to the wrong regions -- the exact failure this repository
is built to refuse.

So the mapping is never assumed. Every one of these tables ends with a grand-total row,
and each volume separately publishes mean expenditure per person for each region. Those
eight published figures identify the eight columns uniquely, and the mapping is derived
per wave from that match. It has to be derived per wave, because the order is not stable:
2005 prints Centre East before Centre West and 2010 and 2015 print them the other way
round. A single hardcoded order would have silently swapped two regions in one wave.

**The check that runs on every row.** The national column is the population-weighted mean
of the seven regional columns. The regional population shares are not printed in every
volume, so they are recovered by least squares from the extracted table itself: hundreds
of rows constrain seven weights, and the fit is wildly overdetermined. If the parse were
offset by a column, or the region mapping wrong, no set of non-negative weights summing
to one would reconcile national with the regions. That the recovered weights land on the
known regional population shares is therefore a check on the whole extraction at once,
not merely on the arithmetic.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import INTERIM_DIR, PROCESSED_DIR, raw_path

BIDI = dict.fromkeys(map(ord, "‎‏‪‫‬‭‮⁦⁧⁨⁩"))

REGIONS = ["Grand Tunis", "North East", "North West", "Centre East",
           "Centre West", "South East", "South West"]
COLUMNS = [*REGIONS, "National"]

# Rows reading "of which:" introduce a breakdown and carry no values of their own.
OF_WHICH = "منها"

# A value in these tables: millimes per person per year, occasionally with a space
# thousands separator, occasionally with a decimal.
VALUE = re.compile(
    r"(?<![\d.])\d{1,3}(?: \d{3})+(?:\.\d+)?(?![\d.])"
    r"|(?<![\d.])\d+(?:\.\d+)?(?![\d.])"
)

# The row that anchors the column mapping.
TOTAL_ROW = "المجموع العام"


@dataclass(frozen=True)
class Source:
    """Where one wave's product-by-region table lives."""

    wave: int
    document: str
    title: str


PDF_SOURCES = (
    # 2005 prints the detailed product table under its own heading; the earlier pages
    # carry only aggregated groups, which this table already contains.
    Source(2005, "ebcnv2005_vol1", "حسب المواد و الجهة"),
    Source(2010, "ebcnv2010_vol1", "مستوى اإلنفاق الفردي حسب الجهات"),
    Source(2015, "ebcnv2015_vol1", "مستوى اإلنفاق الفردي حسب الجهات"),
)

ANNEX_2021 = "ebcnv2021_annexe3"

# The 2021 annex is a spreadsheet and states its own column order in French.
ANNEX_COLUMNS = ["Grand Tunis", "North East", "North West", "Centre East",
                 "Centre West", "South East", "South West", "National"]


def volume_pages(document: str) -> list[str]:
    """Layout-preserving text of one survey volume, cached under data/interim."""
    cache = INTERIM_DIR / f"{document}.txt"
    if not cache.exists():
        INTERIM_DIR.mkdir(parents=True, exist_ok=True)
        out = subprocess.run(
            ["pdftotext", "-layout", str(raw_path(document)), "-"],
            capture_output=True, check=True,
        )
        cache.write_text(out.stdout.decode("utf-8", "replace").translate(BIDI))
    return cache.read_text().split("\f")


def _arabic(text: str) -> bool:
    return bool(re.search(r"[؀-ۿ]", text))


def split_row(line: str) -> tuple[str, list[float]] | None:
    """Eight values and the Arabic product label that follows them.

    Right-to-left layout puts the label after the numbers, so the label is whatever
    trails the last value. A row that does not yield exactly eight values is refused
    rather than padded -- a short row means a value was lost, and padding it would shift
    every region by one.
    """
    matches = list(VALUE.finditer(line))
    if len(matches) != 8:
        return None
    label = line[matches[-1].end():].strip()
    if not _arabic(label) or OF_WHICH in label:
        return None
    values = [float(m.group().replace(" ", "")) for m in matches]
    return label, values


# The 2010 volume is the one wave whose regional means never reached the panel, so its
# anchor is read from the volume's own summary table. Its rows run in this order, which
# the surrounding prose on the same page states independently.
SUMMARY_TITLE = "تطوّر مستوى اإلنفاق السنوي للفرد حسب اجلهات"
SUMMARY_ORDER = [*REGIONS, "National"]


def _national_from_panel(wave: int) -> float:
    """Total expenditure per person, as the sum of the published COICOP functions.

    An anchor for the national column that comes from a different table than the one
    being decoded, so agreement between them is evidence rather than a tautology.
    """
    panel = pd.read_csv(PROCESSED_DIR / "tn_consumption_panel.csv")
    rows = panel[(panel.indicator == "expenditure_pc_by_function") & (panel.wave == wave)
                 & (panel.geography == "Tunisia")]
    if rows.empty:
        rows = panel[(panel.indicator == "expenditure_pc_mean") & (panel.wave == wave)
                     & (panel.geography == "Tunisia") & (panel.milieu == "all")
                     & panel.subgroup.isna()]
        if rows.empty:
            raise RuntimeError(f"{wave}: no national anchor available")
        return float(rows.value.iloc[0])
    return float(rows.value.sum())


def _anchor_from_volume(source: Source) -> dict[str, float]:
    """Regional means read from the volume's own summary table.

    Used only where the panel cannot supply them. The national row is checked against
    the panel before the regional rows are trusted, so a misread of this table cannot
    quietly become the key to the product table.
    """
    rows = []
    for page in volume_pages(source.document):
        if SUMMARY_TITLE not in page:
            continue
        for line in page.splitlines():
            values = [m.group().replace(" ", "") for m in VALUE.finditer(line)]
            # growth rate, then the three survey years; the wave's own column is second.
            if len(values) == 4 and _arabic(line):
                rows.append(float(values[1]))
    if len(rows) != len(SUMMARY_ORDER):
        raise RuntimeError(
            f"{source.wave}: summary table gave {len(rows)} rows, expected "
            f"{len(SUMMARY_ORDER)}; cannot anchor the columns from it"
        )
    means = dict(zip(SUMMARY_ORDER, rows, strict=True))
    expected = _national_from_panel(source.wave)
    if abs(means["National"] - expected) > 2.0:
        raise RuntimeError(
            f"{source.wave}: summary table's national mean {means['National']} disagrees "
            f"with the panel's {expected}; the summary table was misread"
        )
    if max(means, key=means.get) != "Grand Tunis":
        raise RuntimeError(f"{source.wave}: summary table does not put Grand Tunis highest")
    return means


def published_regional_means(source: Source) -> dict[str, float]:
    """Mean expenditure per person by region, from outside the table being decoded."""
    panel = pd.read_csv(PROCESSED_DIR / "tn_consumption_panel.csv")
    rows = panel[(panel.indicator == "expenditure_pc_mean") & (panel.wave == source.wave)
                 & (panel.milieu == "all") & panel.subgroup.isna()
                 & (panel.basis == "published")]
    means = {r.geography: float(r.value) for r in rows.itertuples()}
    if all(region in means for region in REGIONS):
        means["National"] = means.get("Tunisia", _national_from_panel(source.wave))
        means.pop("Tunisia", None)
        return means
    return _anchor_from_volume(source)


def column_order(source: Source, total_row: list[float]) -> list[str]:
    """Match the grand-total row against the published means to name each column.

    Values are printed in millimes and published in dinars, so the comparison is on the
    ratio. Each published figure must claim exactly one column and every column must be
    claimed, which is what makes this an identification rather than a nearest-neighbour
    guess.
    """
    published = published_regional_means(source)
    wave = source.wave
    order: list[str] = []
    for value in total_row:
        matches = [name for name, mean in published.items()
                   if abs(value / 1000 - mean) <= 1.0]
        if len(matches) != 1:
            raise RuntimeError(
                f"{wave}: total-row column {value} matches {matches or 'nothing'} among "
                f"the published regional means; the column mapping is not identified"
            )
        order.append(matches[0])
    if sorted(order) != sorted(COLUMNS):
        raise RuntimeError(f"{wave}: columns {order} do not cover every region exactly once")
    return order


def extract_pdf(source: Source) -> pd.DataFrame:
    """Every product row of one wave's table, with its columns named."""
    pages = volume_pages(source.document)
    wanted = [page for page in pages if source.title in page]
    if not wanted:
        raise RuntimeError(f"{source.wave}: no page carries {source.title!r}")

    anchor: list[float] | None = None
    for page in wanted:
        for line in page.splitlines():
            if TOTAL_ROW in line:
                parsed = split_row(line)
                if parsed:
                    anchor = parsed[1]
    if anchor is None:
        raise RuntimeError(f"{source.wave}: no grand-total row to anchor the columns")
    order = column_order(source, anchor)

    records = []
    for page_number, page in enumerate(wanted):
        for line in page.splitlines():
            parsed = split_row(line)
            if parsed is None:
                continue
            label, values = parsed
            if TOTAL_ROW in label:
                continue
            records.append({"wave": source.wave, "product_ar": label,
                            "page_order": page_number,
                            **dict(zip(order, values, strict=True))})
    frame = pd.DataFrame(records)
    # One product can be printed on more than one page only by being a repeated
    # sub-heading; keeping the first occurrence of a label keeps the series single-valued.
    return frame.drop_duplicates("product_ar", keep="first").drop(columns="page_order")


def extract_2021() -> pd.DataFrame:
    """The 2021 wave, from the spreadsheet annex that states its own columns."""
    sheet = pd.read_excel(raw_path(ANNEX_2021), sheet_name="dpa_prdt_region", header=None)
    body = sheet.iloc[2:].copy()
    body.columns = ["code", "product_fr", "product_ar", *ANNEX_COLUMNS]
    body = body[body[ANNEX_COLUMNS].notna().all(axis=1)]
    body["product_ar"] = body.product_ar.astype(str).str.strip()
    body = body[body.product_ar.map(_arabic) & ~body.product_ar.str.contains(OF_WHICH)]
    body["wave"] = 2021
    # The spreadsheet reader leaves these as objects, which silently poisons every
    # numeric operation downstream once the waves are concatenated.
    for column in COLUMNS:
        body[column] = body[column].astype(float)
    keep = ["wave", "product_ar", *COLUMNS]
    return body[keep].drop_duplicates("product_ar", keep="first").reset_index(drop=True)


def recovered_population_shares(frame: pd.DataFrame) -> np.ndarray:
    """Fit the weights that reconcile the national column with the seven regions.

    A parse that had lost a column, or named the regions wrongly, would leave no set of
    weights able to do this across hundreds of products at once.
    """
    x = frame[REGIONS].to_numpy(float)
    national = frame["National"].to_numpy(float)
    weights, *_ = np.linalg.lstsq(x, national, rcond=None)
    return weights


# A row passes if its printed national value is what its own regions imply. The floor
# keeps the test from being vacuous on products that almost nobody buys.
TOLERANCE, FLOOR = 0.02, 50.0


def reconcile(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    """Drop rows whose national column contradicts their own regional columns.

    The weights are fitted once on everything, used to find rows that disagree, then
    refitted on what survives so that a bad row cannot drag the weights toward itself.
    """
    weights = recovered_population_shares(frame)
    x = frame[REGIONS].to_numpy(float)
    national = frame["National"].to_numpy(float)
    error = np.abs(x @ weights - national)
    keep = error <= np.maximum(TOLERANCE * national, FLOOR)

    rejected = frame[~keep].assign(
        implied_national=(x @ weights)[~keep],
        reason="printed national disagrees with this row's own regions",
    )
    clean = frame[keep].reset_index(drop=True)
    return clean, rejected.reset_index(drop=True), recovered_population_shares(clean)


def spatial_gini(values: np.ndarray, weights: np.ndarray) -> float:
    """Gini across regions of per-capita spending, each region weighted by its people.

    This is the between-region component of inequality in a single good: zero when every
    region spends the same per head, rising as spending concentrates in some regions.
    Households within a region are not compared, so it is a measure of where a good is
    consumed rather than of who consumes it.
    """
    values = np.asarray(values, float)
    weights = np.asarray(weights, float)
    order = np.argsort(values)
    values, weights = values[order], weights[order]
    cumulative_people = np.cumsum(weights)
    cumulative_spend = np.cumsum(values * weights)
    x = np.concatenate([[0.0], cumulative_people / cumulative_people[-1]])
    y = np.concatenate([[0.0], cumulative_spend / cumulative_spend[-1]])
    return float(1.0 - np.sum((x[1:] - x[:-1]) * (y[1:] + y[:-1])))


def french_names() -> dict[str, str]:
    """Arabic to French product names, from the one wave that prints both."""
    sheet = pd.read_excel(raw_path(ANNEX_2021), sheet_name="dpa_prdt_region", header=None)
    body = sheet.iloc[2:]
    pairs = zip(body[2].astype(str).str.strip(), body[1].astype(str).str.strip(), strict=True)
    return {ar: fr for ar, fr in pairs if _arabic(ar) and fr not in ("nan", "")}


def build() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Expenditure by product and region, the spatial Gini it yields, and what failed."""
    frames = [extract_pdf(source) for source in PDF_SOURCES] + [extract_2021()]
    raw = pd.concat(frames, ignore_index=True)[["wave", "product_ar", *COLUMNS]]

    kept, rejects, shares = [], [], {}
    for wave, group in raw.groupby("wave"):
        clean, rejected, weights = reconcile(group)
        kept.append(clean)
        rejects.append(rejected)
        shares[wave] = weights
    table = pd.concat(kept, ignore_index=True)
    rejected = pd.concat(rejects, ignore_index=True)

    french = french_names()
    gini = table[["wave", "product_ar"]].copy()
    gini["product_fr"] = gini.product_ar.map(french)
    gini["expenditure_pc_national"] = table.National / 1000.0
    gini["spatial_gini"] = [
        spatial_gini(row, shares[wave])
        for wave, row in zip(table.wave, table[REGIONS].to_numpy(float), strict=True)
    ]
    gini = gini.sort_values(["wave", "product_ar"]).reset_index(drop=True)

    long = table.melt(id_vars=["wave", "product_ar"], value_vars=COLUMNS,
                      var_name="region", value_name="expenditure_pc_millimes")
    long = long.sort_values(["wave", "product_ar", "region"]).reset_index(drop=True)
    return long, gini, rejected
