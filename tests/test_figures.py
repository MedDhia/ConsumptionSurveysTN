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
