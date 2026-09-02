"""Smoke checks on the figure script's data accessors.

`make figures` is in no CI job and was in no test, and it broke without anyone noticing.
The title-canonicalisation pass merged each yearbook table across editions, so the two
exact French strings `pupils_per_teacher` looked up stopped existing; both lookups returned
nothing, and figures 27 to 30, 33 and 34 died at `polyfit` on an empty array. The corpus
had improved and the figures had silently stopped building.

What makes that failure mode nasty is that it is quiet at the point of breakage: an empty
filter is a perfectly valid DataFrame, and it travels a long way before anything complains.
So these tests do not render anything -- a rendering failure is loud, and drawing 76 images
does not belong in a unit suite. They check the accessors return data of the shape the
figures assume, which is the part that can go wrong without a traceback.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def figures():
    spec = importlib.util.spec_from_file_location(
        "make_figures", ROOT / "scripts" / "make_figures.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["make_figures"] = module
    spec.loader.exec_module(module)
    return module


def test_the_pupils_per_teacher_panel_is_not_empty(figures):
    """The accessor that broke. Six figures read it and none of them checked."""
    panel = figures.pupils_per_teacher()
    assert not panel.empty
    assert panel.shape == (24, 21), "24 governorates over 1998-2018"
    assert min(panel.columns) == 1998
    assert max(panel.columns) == figures.PUPILS_LAST_YEAR
    # A ratio of pupils to teachers, so it has to be in a plausible class-size range.
    assert 8 < float(panel.mean().mean()) < 30


def test_no_year_of_pupils_per_teacher_is_entirely_missing(figures):
    """The specific shape of the old failure: a column present but empty throughout.

    `polyfit` on that raises "expected non-empty vector", eleven frames deep, which is a
    poor way to learn that a title was renamed.
    """
    panel = figures.pupils_per_teacher()
    assert not panel.isna().all().any()
    assert panel.notna().sum().sum() >= 500


def test_the_interior_and_coastal_groups_are_both_populated(figures):
    """Figures 29, 33 and 34 difference these two. An empty side is a silent zero."""
    panel = figures.pupils_per_teacher()
    interior = panel[panel.index.isin(figures.INTERIOR)]
    coastal = panel[~panel.index.isin(figures.INTERIOR)]
    assert len(interior) == 10
    assert len(coastal) == 14
    assert len(interior) + len(coastal) == 24


def test_the_monthly_trade_table_still_resolves(figures):
    """The one remaining lookup by French title, so the one that can still go this way."""
    trade = figures.monthly_trade()
    assert not trade.empty
    assert set(trade.panel) == {"Importations", "Exportations"}
    # Twelve months of both panels across the window the RDiT figures use.
    assert trade.groupby("panel").m.nunique().eq(12).all()


def test_the_lorenz_curves_are_well_formed(figures):
    """A Lorenz curve has to start at the origin, end at (1, 1) and never turn down."""
    frame = figures._per_head()
    block = figures._complete(frame, "job_offers", 2023)
    assert block is not None and len(block) == 24
    x, y = figures.lorenz(block)
    assert x[0] == 0 and y[0] == 0
    assert x[-1] == pytest.approx(1.0) and y[-1] == pytest.approx(1.0)
    assert (x[1:] >= x[:-1]).all() and (y[1:] >= y[:-1]).all()
    # Ordered least-served first, so the curve is weakly convex and never above the
    # diagonal: that is what makes the area between them meaningful.
    assert (y <= x + 1e-12).all()


def test_the_least_served_half_is_read_off_the_curve(figures):
    frame = figures._per_head()
    x, y = figures.lorenz(figures._complete(frame, "job_offers", 2023))
    share = figures.least_served_half(x, y)
    assert 0 < share < 0.5, "half the people cannot hold more than half of anything here"
    # Equal provision would put exactly half with half; concentration puts it below.
    flat_x = flat_y = [0.0, 0.5, 1.0]
    assert figures.least_served_half(flat_x, flat_y) == pytest.approx(0.5)


def test_the_unit_lorenz_curve_is_well_formed(figures):
    """Figures 47-49 read one basis, so 48's curve must give back 47's Gini exactly.

    That is the claim the figure makes in its own source note, and it holds only because
    the curve counts each unit once rather than weighting by population -- twice the area
    between an unweighted Lorenz curve and the diagonal is the unweighted Gini. If the two
    ever drift apart, the note is wrong before the figure is.
    """
    import numpy as np

    values = np.array([1.0, 2.0, 3.0, 10.0, 20.0, 30.0])
    x, y = figures._unit_lorenz(values)
    assert x[0] == y[0] == 0.0
    assert x[-1] == pytest.approx(1.0)
    assert y[-1] == pytest.approx(1.0)
    assert (np.diff(y) >= -1e-12).all(), "cumulative shares cannot fall"
    assert (y <= x + 1e-12).all(), "ordered smallest first, so never above the diagonal"

    area = np.trapezoid(y, x) if hasattr(np, "trapezoid") else np.trapz(y, x)
    assert 1 - 2 * area == pytest.approx(figures._gini_of(values), abs=1e-12)


def test_a_flat_distribution_lies_on_the_diagonal(figures):
    import numpy as np

    x, y = figures._unit_lorenz(np.array([5.0] * 7))
    assert np.allclose(x, y)


def test_the_period_levels_cover_both_sides_of_the_revolution(figures):
    """The accessor behind figure 48. Every service it draws needs both periods complete."""
    for indicator, _ in figures.LORENZ_INDICATORS:
        levels = figures._period_levels(indicator)
        assert set(levels) == {"pre", "post"}
        for period in ("pre", "post"):
            governorates, regions, years = levels[period]
            assert len(governorates) == 24, f"{indicator} {period}"
            assert len(regions) == 7, f"{indicator} {period}"
            assert years >= 6, f"{indicator} {period}: {years} years is not a period"
            # The region series is the same quantity aggregated, so the totals agree.
            assert governorates.sum() == pytest.approx(regions.sum())


def test_the_pre_post_table_reaches_the_figures(figures):
    """Each measure figures 47 and 49 plot must survive the window filter."""
    for measure in ("gini_governorate", "gini_region", "between_share"):
        table = figures._pre_post(measure)
        assert len(table) >= 15, measure
        assert table.index.is_unique
        assert not table[["pre", "post", "change", "predicted", "excess"]].isna().any().any()
