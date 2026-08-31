"""Checks that the README's numbers are the corpus's numbers.

Every figure quoted in prose is a claim that was true when it was typed and has no way of
staying true. This has now gone wrong twice: `docs/SOURCES.md` described 21 artefacts after
22 yearbooks were registered, and the README quoted 181,291 corpus values and 4,918 long
series after both had moved — in the second case understating the corpus, which is the
direction nobody notices.

So the figures are derived here and compared against the text. A build that changes the
corpus now fails until the README is updated, which is the only mechanism that has ever
worked. These read `data/processed`, which is committed, so they need no fetch.
"""

from __future__ import annotations

import gzip
import re
from collections import Counter
from pathlib import Path

import pandas as pd
import pytest

from consumptiontn import config
from consumptiontn.build_governorates import _period_column

README = config.PROJECT_ROOT / "README.md"
PROCESSED = config.PROJECT_ROOT / "data" / "processed"


def _readme() -> str:
    return README.read_text()


def _rows(path: Path) -> int:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", errors="replace") as handle:
        return sum(1 for _ in handle) - 1


@pytest.fixture(scope="module")
def series() -> pd.DataFrame:
    frame = pd.read_csv(PROCESSED / "tn_yearbook_series.csv", dtype={"panel": "string"})
    frame["panel"] = frame.panel.fillna("")
    return frame


def test_the_dataset_table_row_counts_are_current():
    """The table in the README is the first thing a reader trusts and the easiest to break:
    every rebuild that changes a row count silently falsifies one cell of it."""
    claims = re.findall(r"^\| `(tn_[a-z0-9_]+)` \| ([\d,]+) \|", _readme(), re.M)
    assert len(claims) > 20, "the dataset table moved; this test needs rewriting"

    wrong = {}
    for name, claimed in claims:
        for suffix in (".csv", ".csv.gz"):
            path = PROCESSED / f"{name}{suffix}"
            if path.exists():
                actual = _rows(path)
                if f"{actual:,}" != claimed:
                    wrong[name] = (claimed, f"{actual:,}")
                break
        else:
            wrong[name] = (claimed, "no such dataset")
    assert not wrong, f"README row counts are stale (claimed, actual): {wrong}"


def test_every_dataset_appears_in_the_readme_table_exactly_once():
    """A dataset missing from the table is invisible to a reader; one listed twice is
    worse, because the two lines drift apart and neither is obviously the stale one.

    The duplicate half of this test earns its place: adding four datasets to the table, I
    re-added one that was already there, and every other check passed because both rows
    carried the same row count.
    """
    listed = re.findall(r"^\| `(tn_[a-z0-9_]+)` \|", _readme(), re.M)
    shipped = {p.name.split(".")[0] for p in PROCESSED.glob("tn_*.csv*")}
    assert not shipped - set(listed), f"shipped but undocumented: {sorted(shipped - set(listed))}"

    seen = Counter(listed)
    assert not [n for n, c in seen.items() if c > 1], f"listed twice: {seen.most_common(3)}"


def test_the_corpus_figures_quoted_in_prose_are_current(series):
    """The values, tables, confirmations and long-series counts in the yearbook section."""
    text = _readme()

    values, tables, editions = re.search(
        r"([\d,]+) values from ([\d,]+) tables across all (\d+) editions", text).groups()
    assert values == f"{len(series):,}"
    assert tables == f"{series.title_fr.nunique():,}"
    assert int(editions) == series.edition.nunique()

    confirmed = re.search(r"([\d,]+) of those values are confirmed", text).group(1)
    assert confirmed == f"{series.agreement.eq('confirmed').sum():,}"


def test_the_long_series_counts_quoted_in_prose_are_current(series):
    """A series is one cell followed across years.

    The subtlety worth pinning: on a year-header table the year *is* the column label, so
    keeping it in the key would make every year its own series and report a corpus of
    singletons. On a category-header table the column label must stay, because it names a
    different series. Getting that wrong is what produced the earlier undercount.
    """
    data = series[series.row_kind.eq("data")].copy()
    data["series_column"] = data.column_label.where(~_period_column(data), "")
    spans = data.groupby(["title_fr", "panel", "row_label", "series_column"]).year.nunique()

    text = _readme()
    ten, twenty = re.search(
        r"([\d,]+) of the series it yields run ten years or longer, ([\d,]+)\s*\n?"
        r"\s*of them twenty or longer", text).groups()
    assert ten == f"{(spans >= 10).sum():,}"
    assert twenty == f"{(spans >= 20).sum():,}"

    longest = int(re.search(r"The longest run (\d+) years", text).group(1))
    assert longest == int(spans.max())
