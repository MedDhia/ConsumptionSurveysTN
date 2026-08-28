"""Structural checks on the indicator panel and the derived reference datasets."""

from __future__ import annotations

import pandas as pd
import pytest

from consumptiontn import build_panel, config, extract_pdf, panel_sources


@pytest.fixture(scope="module")
def published() -> pd.DataFrame:
    return panel_sources.published_rows()


def test_every_row_cites_a_real_source(published):
    """A transcribed number with no citation is not usable. Every key must resolve."""
    assert published["source_table"].notna().all()
    for key in published["source_key"].unique():
        assert key in config.SOURCES_BY_KEY


def test_no_duplicate_published_observations(published):
    keys = ["wave", "geography_level", "geography", "milieu", "subgroup_type", "subgroup", "indicator", "methodology"]
    duplicates = published[published.duplicated(keys, keep=False)]
    assert duplicates.empty, duplicates.to_string()


def test_poverty_methodologies_are_kept_apart(published):
    """2005 carries two national poverty rates on incompatible methodologies.

    3.8% on the pre-2011 basis, 23.1% on the revised one. Both are correct as published;
    the panel must never merge them into a single series.
    """
    rows = published[
        (published["indicator"] == "poverty_rate")
        & (published["wave"] == 2005)
        & (published["geography"] == "Tunisia")
        & (published["milieu"].isna())
        & (published["subgroup"].isna())
    ]
    assert set(rows["methodology"]) == {"pre-2011", "revised (2011)"}
    assert sorted(rows["value"]) == [3.8, 23.1]


def test_budget_shares_sum_to_100(published):
    coicop = published[
        (published["indicator"] == "budget_share")
        & (published["subgroup_type"] == "COICOP function")
    ]
    for wave, group in coicop.groupby("wave"):
        assert group["value"].sum() == pytest.approx(100, abs=0.3), wave


def test_wave_coverage_lists_every_wave():
    covered = set(panel_sources.WAVE_COVERAGE["wave"])
    assert set(config.WAVES) <= covered


def test_recomputed_2021_matches_published(published):
    """Where the panel holds both bases for the same cell, they must agree."""
    panel = build_panel.build()
    keys = ["wave", "geography_level", "geography", "milieu", "subgroup_type", "subgroup", "indicator"]
    wide = panel.pivot_table(index=keys, columns="basis", values="value", dropna=False)
    both = wide.dropna(subset=["published", "recomputed"]).reset_index()
    assert len(both) >= 20, "expected the 2021 cells to overlap in both bases"
    # Published figures are rounded before printing: whole dinars for money, one decimal
    # for rates. The agreement we can demand is half of that printing precision.
    money = both["indicator"].str.startswith(("expenditure_", "consumption_"))
    both["allowed"] = money.map({True: 0.51, False: 0.06})
    both["gap"] = (both["published"] - both["recomputed"]).abs()
    over = both[both["gap"] > both["allowed"]]
    assert over.empty, over.sort_values("gap").to_string()


def test_delegation_poverty_extraction():
    df = extract_pdf.delegation_poverty()
    assert len(df) > 240
    assert df["governorate"].nunique() == 23  # Siliana's table has no poverty column
    assert df["poverty_rate_pct"].between(0, 100).all()
    assert not df.duplicated(["governorate", "delegation"]).any()
    assert (df["estimate_type"] == "modelled small-area estimate").all()
