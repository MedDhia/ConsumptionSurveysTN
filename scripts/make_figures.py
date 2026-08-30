"""Figures on the evolution of inequality in Tunisia, 1985-2021.

**No composite index appears anywhere in this directory.** No Gini, no Theil, no
Atkinson, no polarisation index. Every figure shows either an observed quantity (a
group's mean expenditure, a poverty rate, a budget share) or the relation between two
observed quantities (one region's mean against the national mean, a region's share of
spending against its share of people). A reader can recover any number here from the
underlying dataset with arithmetic they can do in their head.

That is a deliberate constraint, and it costs something: a single index compresses a
distribution into one comparable number, which these figures cannot do. What they give
back is that nothing is hidden inside a formula -- when the gap between Grand Tunis and
the Centre West widens, you see which line moved.

Written light and dark; `figures/README.md` serves the right one per viewer theme.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib as mpl
import numpy as np
import pandas as pd

from consumptiontn import rdit

mpl.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "figures"

# Validated with the dataviz skill's validate_palette.js: all checks pass in both
# modes (light worst-adjacent CVD dE 24.7, dark 26.8; both well clear of the >=8 gate).
THEMES = {
    "light": {
        "surface": "#fcfcfb",
        "ink": "#0b0b0b",
        "ink2": "#52514e",
        "muted": "#898781",
        "grid": "#e1e0d9",
        "axis": "#c3c2b7",
        "s1": "#2a78d6",
        "s2": "#eb6834",
    },
    "dark": {
        "surface": "#1a1a19",
        "ink": "#ffffff",
        "ink2": "#c3c2b7",
        "muted": "#898781",
        "grid": "#2c2c2a",
        "axis": "#383835",
        "s1": "#3987e5",
        "s2": "#d95926",
    },
}

REGIONS = [
    "Grand Tunis",
    "North East",
    "North West",
    "Centre East",
    "Centre West",
    "South East",
    "South West",
]


def style(t: dict) -> None:
    mpl.rcParams.update(
        {
            "figure.facecolor": t["surface"],
            "axes.facecolor": t["surface"],
            "savefig.facecolor": t["surface"],
            "text.color": t["ink"],
            "axes.labelcolor": t["ink2"],
            "axes.edgecolor": t["axis"],
            "xtick.color": t["muted"],
            "ytick.color": t["muted"],
            "grid.color": t["grid"],
            "grid.linewidth": 0.6,
            "axes.grid": True,
            "axes.axisbelow": True,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": False,
            "font.size": 10,
            "axes.titlesize": 11,
            "figure.dpi": 160,
            "lines.linewidth": 2.0,
            "lines.markersize": 7,
        }
    )


def finish(fig, t: dict, title: str, subtitle: str, source: str) -> None:
    """Title block above the plot, source note below. Never a number on every point.

    Both lines are figure text with an explicit top baseline: ``suptitle`` positions
    against the axes and collided with the subtitle at these figure heights.
    """
    fig.text(0.012, 0.975, title, ha="left", va="top", fontsize=13,
             fontweight="bold", color=t["ink"])
    fig.text(0.012, 0.912, subtitle, ha="left", va="top", fontsize=9.5, color=t["ink2"])
    # Wrap to the figure's own width: unwrapped notes ran off the right edge at 9in.
    wrapped = textwrap.fill(source, width=int(fig.get_figwidth() * 15.5))
    fig.text(0.012, 0.018, wrapped, ha="left", va="bottom", fontsize=8, color=t["muted"])


def panel(df: pd.DataFrame, indicator: str, basis: str = "published", **where) -> pd.DataFrame:
    """One tidy series out of the panel, on a single basis.

    2021 appears twice by design -- once transcribed from INS, once recomputed from the
    microdata -- so a basis has to be chosen or the series doubles. These figures use
    ``published`` throughout, because the pre-2015 waves exist only that way and mixing
    bases mid-series would compare two different things. The two agree to within INS's
    own rounding, so the choice does not move any line here.
    """
    d = df[(df.indicator == indicator) & (df.basis == basis)]
    for key, value in where.items():
        d = d[d[key].isna()] if value is None else d[d[key] == value]
    duplicated = d.duplicated(["wave", "geography", "milieu", "subgroup"])
    if duplicated.any():
        raise ValueError(f"{indicator}: {duplicated.sum()} duplicate rows after filtering")
    return d.sort_values("wave")


def weighted_quantile(values, weights, quantiles):
    """Weighted quantiles by interpolation on cumulative-weight midpoints.

    numpy has no weighted percentile. This is the same construction ``gini()`` uses in
    ``build_panel.py`` -- each observation is placed at the midpoint of the weight it
    occupies, then the quantile is read off by linear interpolation.
    """
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    order = np.argsort(values)
    values, weights = values[order], weights[order]
    midpoints = np.cumsum(weights) - 0.5 * weights
    return np.interp(np.asarray(quantiles) * weights.sum(), midpoints, values)


def weighted_share(frame: pd.DataFrame, mask, weight: str = "weight_pop") -> float:
    """Percentage of ``frame``'s weighted population satisfying ``mask``."""
    if frame.empty:
        raise ValueError("weighted_share got an empty frame -- check the filter")
    return 100 * float(np.average(mask, weights=frame[weight]))


def dumbbell(ax, t, left, right, labels, left_name, right_name):
    """Paired dots joined by a rule -- the repo's house form for a two-point comparison."""
    y = np.arange(len(labels))
    ax.grid(axis="y", visible=False)
    for yi, lo, hi in zip(y, left, right, strict=True):
        ax.plot([lo, hi], [yi, yi], color=t["axis"], lw=2, zorder=1, solid_capstyle="round")
    ax.scatter(left, y, s=95, color=t["surface"], zorder=2, edgecolor=t["s2"],
               linewidth=2.2, label=left_name)
    ax.scatter(right, y, s=95, color=t["s1"], zorder=3, edgecolor=t["surface"],
               linewidth=1.2, label=right_name)
    ax.set_yticks(y, labels, color=t["ink2"])
    return y


REVOLUTION = 2011

def mark_revolution(ax, t, label: bool = True, y: float = 0.94) -> None:
    """A rule at January 2011, drawn identically wherever it appears.

    The rule marks *when*, not *why*. Between the 2010 and 2021 waves Tunisia had the
    revolution, the 2015 Bardo and Sousse attacks and the tourism collapse, a sharp dinar
    depreciation, IMF programmes, and COVID -- and the 2021 survey was fielded in the
    middle of the pandemic. Nothing in these figures separates those.
    """
    ax.axvline(REVOLUTION, color=t["muted"], lw=1.2, ls=(0, (5, 4)), zorder=0)
    if label:
        ax.annotate("revolution", (REVOLUTION, y), xycoords=("data", "axes fraction"),
                    xytext=(5, 0), textcoords="offset points", fontsize=8.5,
                    color=t["muted"], va="top")


def poverty_series(p: pd.DataFrame, *, modelled: bool = False, **where) -> pd.Series:
    """A poverty series on the revised (2011) methodology, indexed by wave.

    The panel also carries pre-2011-methodology figures -- 3.8% for 2005 against 23.1% on
    the revised basis. Mixing them would produce a chart that looks like a collapse in
    poverty and means nothing, so methodology is always filtered explicitly.

    The 2019 estimate is on the revised methodology but *modelled*: its label reads
    "revised (2011), modelled from 2018-19 follow-up panel". Matching the methodology
    string exactly therefore drops it silently. ``modelled`` selects which side you
    want -- surveyed waves by default, the modelled points when asked -- so a caller has
    to say which, rather than getting one by accident.
    """
    d = p[(p.indicator == where.pop("indicator", "poverty_rate"))
          & (p.basis == "published")
          & (p.methodology.astype(str).str.startswith("revised (2011)"))]
    for key, value in where.items():
        d = d[d[key].isna()] if value is None else d[d[key] == value]
    is_modelled = d.methodology.str.contains("modelled")
    d = d[is_modelled] if modelled else d[~is_modelled]
    if d.empty:
        raise ValueError(f"empty poverty series (modelled={modelled}) for {where}")
    if d.wave.duplicated().any():
        raise ValueError(f"duplicate waves in poverty series for {where}")
    return d.sort_values("wave").set_index("wave")["value"]



SENTINELS = {9, 99, 999, 9999, 99999, 999999}


def clean_numeric(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    """Drop INS's "non declare" sentinels from a numeric column.

    999 / 9999 / 999999 survive in the processed files as codes, not amounts. Averaging
    a column that still holds them produces a number that is wrong by orders of
    magnitude and looks plausible, so every figure that touches one filters here and
    reports the denominator it kept.
    """
    keep = frame[frame[column].notna() & ~frame[column].isin(SENTINELS)]
    if keep.empty:
        raise ValueError(f"{column}: nothing left after dropping sentinels")
    return keep


def category_shares(frame: pd.DataFrame, column: str, group: str, weight: str) -> pd.DataFrame:
    """Weighted percentage breakdown of ``column`` within each level of ``group``."""
    present = frame[frame[column].notna() & frame[group].notna()]
    if present.empty:
        raise ValueError(f"{column} x {group}: no rows")
    out = {}
    for level, block in present.groupby(group, observed=True):
        out[level] = {
            value: weighted_share(block, block[column].eq(value), weight=weight)
            for value in present[column].dropna().unique()
        }
    return pd.DataFrame(out)


def read(name: str, columns: list[str] | None = None) -> pd.DataFrame:
    """Load a processed dataset by name."""
    return pd.read_parquet(PROCESSED / f"{name}.parquet", columns=columns)


# --------------------------------------------------------------- prices and work


# --------------------------------------------------------------------- the figures

def fig_quintiles(p: pd.DataFrame, t: dict):
    """Every quintile gained; the gap in dinars widened. Levels, not a ratio."""
    q = panel(p, "expenditure_pc_mean", subgroup_type="expenditure quintile")
    wide = q.pivot_table(index="subgroup", columns="wave", values="value")
    wide = wide.loc[[f"Quintile {i}" for i in range(1, 6)]]
    y = np.arange(len(wide))[::-1]

    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    ax.grid(axis="y", visible=False)
    for yi, (_, row) in zip(y, wide.iterrows(), strict=True):
        ax.plot([row[2015], row[2021]], [yi, yi], color=t["axis"], lw=2, zorder=1,
                solid_capstyle="round")
    ax.scatter(wide[2015], y, s=95, color=t["surface"], zorder=2,
               edgecolor=t["s2"], linewidth=2.2, label="2015")
    ax.scatter(wide[2021], y, s=95, color=t["s1"], zorder=3,
               edgecolor=t["surface"], linewidth=1.2, label="2021")
    for yi, (_, row) in zip(y, wide.iterrows(), strict=True):
        ax.annotate(f"+{row[2021] - row[2015]:,.0f} DT", (row[2021], yi),
                    xytext=(11, 0), textcoords="offset points", va="center",
                    fontsize=9, color=t["ink2"])
    ax.set_yticks(y, wide.index, color=t["ink2"])
    ax.set_xlabel("Mean expenditure per person per year, current dinars")
    ax.set_xlim(0, 14600)
    ax.legend(frameon=False, loc="upper right", labelcolor=t["ink2"])
    fig.subplots_adjust(left=0.13, right=0.97, top=0.80, bottom=0.18)
    finish(fig, t,
           "The poorest fifth gained 622 dinars. The richest gained 3,219.",
           "Mean annual expenditure per person by expenditure quintile, 2015 and 2021",
           "INS, EBCNV 2021 synthesis note, Tableau 3. Current prices, not deflated.")
    return fig


def fig_regional_gap(p: pd.DataFrame, t: dict):
    """Each region against the national mean. Small multiples: one series per panel."""
    reg = panel(p, "expenditure_pc_mean", geography_level="region", milieu="all")
    nat = panel(p, "expenditure_pc_mean", geography="Tunisia", milieu="all",
                subgroup_type=None).set_index("wave")["value"]

    fig, axes = plt.subplots(2, 4, figsize=(11.2, 5.4), sharex=True, sharey=True)
    for ax, region in zip(axes.flat, REGIONS, strict=False):
        d = reg[reg.geography == region]
        rel = 100 * d.set_index("wave")["value"] / nat.reindex(d.wave).to_numpy()
        ax.axhline(100, color=t["axis"], lw=1.2, zorder=1)
        ax.plot(rel.index, rel.to_numpy(), color=t["s1"], marker="o",
                markeredgecolor=t["surface"], markeredgewidth=1.0, zorder=2)
        ax.set_title(region, color=t["ink"], loc="left", pad=6)
        ax.set_ylim(50, 145)
        ax.set_xticks([1990, 2005, 2021])
    axes.flat[-1].axis("off")
    axes.flat[-1].plot([0.02, 0.16], [0.66, 0.66], color=t["axis"], lw=1.2,
                       transform=axes.flat[-1].transAxes, clip_on=False)
    axes.flat[-1].text(0.21, 0.66, "100 = the national mean\nfor that year",
                       color=t["muted"], fontsize=9, va="center",
                       transform=axes.flat[-1].transAxes)
    for ax in axes[:, 0]:
        ax.set_ylabel("% of national mean", color=t["ink2"], fontsize=9)
    fig.subplots_adjust(left=0.07, right=0.98, top=0.79, bottom=0.13, hspace=0.42, wspace=0.18)
    finish(fig, t,
           "Regional gaps narrowed at the bottom, but Grand Tunis stayed on top",
           "Each region's mean expenditure per person as a percentage of the national mean",
           "INS: EBCNV 2005 volume 1 (1990-2005) and the 2021 synthesis note (2015, 2021). "
           "No 2010 regional figure is published; markers show observed waves only.")
    return fig


def fig_urban_rural(p: pd.DataFrame, t: dict):
    """Levels on the left, the gap as a ratio on the right. Never on one pair of axes."""
    urban = panel(p, "expenditure_pc_mean", geography="Tunisia", milieu="urban")
    rural = panel(p, "expenditure_pc_mean", geography="Tunisia", milieu="rural")
    u = urban.set_index("wave")["value"]
    r = rural.set_index("wave")["value"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.4, 4.6))
    ax1.plot(u.index, u.to_numpy(), color=t["s1"], marker="o",
             markeredgecolor=t["surface"], markeredgewidth=1.0, label="Urban")
    ax1.plot(r.index, r.to_numpy(), color=t["s2"], marker="o",
             markeredgecolor=t["surface"], markeredgewidth=1.0, label="Rural")
    # Direct labels sit to the right of the final marker; above it they collided with
    # the panel title.
    ax1.set_xlim(1987, 2032)
    for series, name in ((u, "Urban"), (r, "Rural")):
        ax1.annotate(name, (series.index[-1], series.iloc[-1]), xytext=(9, -3),
                     textcoords="offset points", color=t["ink2"], fontsize=9.5)
    ax1.set_title("Mean expenditure per person", color=t["ink"], loc="left")
    ax1.set_ylabel("Current dinars per year", color=t["ink2"], fontsize=9)
    ax1.legend(frameon=False, loc="upper left", labelcolor=t["ink2"])

    ratio = 100 * r / u
    ax2.plot(ratio.index, ratio.to_numpy(), color=t["s1"], marker="o",
             markeredgecolor=t["surface"], markeredgewidth=1.0)
    ax2.set_title("Rural mean as a share of urban", color=t["ink"], loc="left")
    ax2.set_ylabel("%", color=t["ink2"], fontsize=9)
    ax2.set_ylim(40, 80)
    for wave in (ratio.index[0], ratio.index[-1]):
        ax2.annotate(f"{ratio[wave]:.0f}%", (wave, ratio[wave]), xytext=(0, 11),
                     textcoords="offset points", ha="center", fontsize=9.5, color=t["ink2"])
    fig.subplots_adjust(left=0.08, right=0.97, top=0.78, bottom=0.17, wspace=0.26)
    finish(fig, t,
           "A rural person still spends about two thirds of what an urban one does",
           "Urban and rural mean expenditure per person, and the ratio between them",
           "INS: EBCNV 2005 volume 1 (1990-2005) and the 2021 synthesis note. Rural is "
           "territory outside the communes of the pre-2014 boundaries. Current prices.")
    return fig


def fig_share_gap(p: pd.DataFrame, t: dict):
    """Share of spending minus share of people. Zero means proportionate."""
    pop = panel(p, "population_share", geography_level="region")
    exp = panel(p, "expenditure_share", geography_level="region")
    merged = pop.merge(exp, on=["geography", "wave"], suffixes=("_pop", "_exp"))
    merged["gap"] = merged["value_exp"] - merged["value_pop"]
    wide = merged.pivot_table(index="geography", columns="wave", values="gap")
    wide = wide.loc[[r for r in REGIONS if r in wide.index]].sort_values(2021)
    y = np.arange(len(wide))

    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    ax.grid(axis="y", visible=False)
    ax.axvline(0, color=t["axis"], lw=1.4, zorder=1)
    for yi, (_, row) in zip(y, wide.iterrows(), strict=True):
        ax.plot([row[2015], row[2021]], [yi, yi], color=t["axis"], lw=2, zorder=2,
                solid_capstyle="round")
    ax.scatter(wide[2015], y, s=95, color=t["surface"], zorder=3,
               edgecolor=t["s2"], linewidth=2.2, label="2015")
    ax.scatter(wide[2021], y, s=95, color=t["s1"], zorder=4,
               edgecolor=t["surface"], linewidth=1.2, label="2021")
    ax.set_yticks(y, wide.index, color=t["ink2"])
    ax.set_xlabel("Share of national expenditure minus share of population, "
                  "percentage points")
    ax.set_xlim(-5.6, 10.8)
    ax.text(0.4, len(wide) - 0.3, "spends more than its share of people",
            fontsize=8.5, color=t["muted"], va="center")
    ax.text(-0.4, len(wide) - 0.3, "spends less", fontsize=8.5, color=t["muted"],
            va="center", ha="right")
    ax.legend(frameon=False, loc="lower right", labelcolor=t["ink2"])
    fig.subplots_adjust(left=0.16, right=0.97, top=0.80, bottom=0.19)
    finish(fig, t,
           "Grand Tunis still spends beyond its size, by three points less than in 2015",
           "Each region's share of national expenditure against its share of population",
           "INS, EBCNV 2021 synthesis note, Tableau 10.")
    return fig


def fig_poverty(p: pd.DataFrame, t: dict):
    """Poverty rate by region against the national rate. One series per panel."""
    reg = panel(p, "poverty_rate", geography_level="region", subgroup_type=None)
    nat = panel(p, "poverty_rate", geography="Tunisia", milieu="all", subgroup_type=None,
                methodology="revised (2011)").set_index("wave")["value"]
    if nat.empty:
        raise ValueError("national poverty series is empty -- check the milieu filter")

    fig, axes = plt.subplots(2, 4, figsize=(11.2, 5.4), sharex=True, sharey=True)
    for ax, region in zip(axes.flat, REGIONS, strict=False):
        d = reg[reg.geography == region].set_index("wave")["value"]
        mark_revolution(ax, t, label=False)
        ax.plot(nat.index, nat.to_numpy(), color=t["axis"], lw=1.6, zorder=1)
        ax.plot(d.index, d.to_numpy(), color=t["s1"], marker="o",
                markeredgecolor=t["surface"], markeredgewidth=1.0, zorder=2)
        ax.set_title(region, color=t["ink"], loc="left", pad=6)
        ax.set_ylim(0, 55)
        ax.set_xticks([2005, 2010, 2015, 2021])
    axes.flat[-1].axis("off")
    axes.flat[-1].plot([0.02, 0.16], [0.60, 0.60], color=t["axis"], lw=1.6,
                       transform=axes.flat[-1].transAxes, clip_on=False)
    axes.flat[-1].text(0.21, 0.60, "national rate", color=t["muted"], fontsize=9,
                       va="center", transform=axes.flat[-1].transAxes)
    for ax in axes[:, 0]:
        ax.set_ylabel("% of people below\nthe poverty line", color=t["ink2"], fontsize=9)
    fig.subplots_adjust(left=0.09, right=0.98, top=0.79, bottom=0.13, hspace=0.42, wspace=0.18)
    finish(fig, t,
           "Poverty fell almost everywhere to 2015, then rose again in five regions",
           "Share of people below the national poverty line, by region",
           "INS, EBCNV 2021 synthesis note, Tableau 7. Revised (2011) methodology "
           "throughout; pre-2011 figures are not comparable and are not shown.")
    return fig


def fig_distribution(t: dict):
    """The 2021 microdata: who holds the spending, and what they spend it on."""
    hh = pd.read_csv(PROCESSED / "tn_hbs_2021_household.csv")
    fn = pd.read_csv(PROCESSED / "tn_hbs_2021_expenditure_by_function.csv")
    d = hh.merge(fn[["hh_id", "exp_food_01", "exp_total"]], on="hh_id")
    d["w"] = d["weight_pop"]

    grp = d.groupby("decile")
    spend = grp.apply(lambda g: (g.expenditure_pc * g.w).sum(), include_groups=False)
    share = 100 * spend / spend.sum()
    # Mean household food share, weighted by people -- not aggregate food spending over
    # aggregate spending. The two agree to a tenth of a point through decile 9 and then
    # split: the aggregate ratio puts the top decile at 28.5% and ticks *up* from decile
    # 9, because a handful of very large budgets dominate the sum. The mean of household
    # shares is what "how much of its budget does this tenth put on food" means, and it
    # falls monotonically.
    food = grp.apply(lambda g: 100 * np.average(g.exp_food_01 / g.exp_total,
                                                weights=g.weight_pop), include_groups=False)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.4, 4.6))
    ax1.grid(axis="x", visible=False)
    ax1.bar(share.index, share.to_numpy(), color=t["s1"], width=0.68, zorder=2)
    ax1.axhline(10, color=t["axis"], lw=1.4, zorder=3)
    ax1.annotate("10% = an equal share", (0.6, 10), xytext=(0, 7),
                 textcoords="offset points", ha="left", fontsize=8.5, color=t["muted"])
    ax1.annotate(f"{share.iloc[-1]:.0f}%", (10, share.iloc[-1]), xytext=(0, 5),
                 textcoords="offset points", ha="center", fontsize=9.5, color=t["ink2"])
    ax1.set_title("Share of all expenditure held by each tenth",
                  color=t["ink"], loc="left")
    ax1.set_xlabel("Decile of expenditure per person, poorest to richest")
    ax1.set_ylabel("% of national expenditure", color=t["ink2"], fontsize=9)
    ax1.set_xticks(range(1, 11))

    ax2.grid(axis="x", visible=False)
    ax2.bar(food.index, food.to_numpy(), color=t["s1"], width=0.68, zorder=2)
    for i in (1, 10):
        ax2.annotate(f"{food[i]:.0f}%", (i, food[i]), xytext=(0, 5),
                     textcoords="offset points", ha="center", fontsize=9.5, color=t["ink2"])
    ax2.set_title("Share of the tenth's budget spent on food",
                  color=t["ink"], loc="left")
    ax2.set_ylabel("mean household share, %", color=t["ink2"], fontsize=9)
    ax2.set_xlabel("Decile of expenditure per person, poorest to richest")
    ax2.set_xticks(range(1, 11))
    ax2.set_ylim(0, 45)

    fig.subplots_adjust(left=0.08, right=0.97, top=0.78, bottom=0.18, wspace=0.24)
    finish(fig, t,
           "The richest tenth holds 28% of all spending. The poorest tenth holds 3%.",
           "Distribution of expenditure across deciles, 2021, and the food share of each",
           "Recomputed from EBCNV 2021 microdata (17,394 households), weighted by the "
           "individual extrapolation factor. Food is COICOP function 01.")
    return fig


# ------------------------------------------------- inequality within groups, not between

def fig_within_region(t: dict):
    """Spread inside each region against the spread between regions.

    The regional figures above are built on means, which cannot show dispersion. This one
    is percentiles only -- still no index.
    """
    hh = pd.read_csv(PROCESSED / "tn_hbs_2021_household.csv")
    rows = []
    for region, g in hh.groupby("region", observed=True):
        p10, p50, p90 = weighted_quantile(g.expenditure_pc, g.weight_pop, [0.10, 0.50, 0.90])
        rows.append({"name": str(region), "p10": p10, "p50": p50, "p90": p90})
    national = weighted_quantile(hh.expenditure_pc, hh.weight_pop, [0.10, 0.50, 0.90])
    rows.sort(key=lambda r: r["p50"])
    rows.append({"name": "National", "p10": national[0], "p50": national[1], "p90": national[2]})
    d = pd.DataFrame(rows)
    y = np.arange(len(d))

    fig, ax = plt.subplots(figsize=(9.0, 5.0))
    ax.grid(axis="y", visible=False)
    for yi, row in zip(y, d.itertuples(), strict=True):
        national_row = row.name == "National"
        colour = t["muted"] if national_row else t["s1"]
        ax.plot([row.p10, row.p90], [yi, yi], color=t["axis"], lw=4, zorder=1,
                solid_capstyle="round")
        ax.scatter([row.p50], [yi], s=110, color=colour, zorder=3,
                   edgecolor=t["surface"], linewidth=1.4)
        ax.annotate(f"{row.p90 / row.p10:.1f}x", (row.p90, yi), xytext=(11, 0),
                    textcoords="offset points", va="center", fontsize=9, color=t["ink2"])
    ax.set_yticks(y, d["name"], color=t["ink2"])
    ax.set_xlabel("Annual expenditure per person, current dinars")
    ax.set_xlim(0, 14200)
    fig.subplots_adjust(left=0.14, right=0.96, top=0.80, bottom=0.17)
    # State the between-region comparator the title rests on, so a reader can check it.
    regions = d[d["name"] != "National"]
    between = regions["p50"].max() / regions["p50"].min()
    within = regions["p90"] / regions["p10"]
    finish(fig, t,
           "Every region is more unequal inside itself than the regions are from each other",
           f"Within a region the 90th percentile is {within.min():.1f} to {within.max():.1f} "
           f"times the 10th. Between regions, the highest median is only "
           f"{between:.1f} times the lowest.",
           "Bar spans the 10th to 90th percentile, dot is the median, figure at right is "
           "p90 divided by p10. Recomputed from EBCNV 2021 microdata, weighted by the "
           "individual extrapolation factor. Percentiles only -- no inequality index.")
    return fig


def fig_delegations(t: dict):
    """253 delegations inside 23 governorates. The average hides most of the variation."""
    d = pd.read_csv(PROCESSED / "tn_poverty_delegations_2015.csv")
    order = d.groupby("governorate").poverty_rate_pct.median().sort_values().index.tolist()
    y = {name: i for i, name in enumerate(order)}

    fig, ax = plt.subplots(figsize=(9.4, 6.4))
    ax.grid(axis="y", visible=False)
    for name in order:
        g = d[d.governorate == name].poverty_rate_pct
        ax.plot([g.min(), g.max()], [y[name], y[name]], color=t["axis"], lw=2, zorder=1,
                solid_capstyle="round")
        ax.scatter(g, np.full(len(g), y[name]), s=42, color=t["s1"], alpha=0.75, zorder=2,
                   edgecolor=t["surface"], linewidth=0.8)
    widest = (d.groupby("governorate").poverty_rate_pct.max()
              - d.groupby("governorate").poverty_rate_pct.min()).idxmax()
    span = d[d.governorate == widest].poverty_rate_pct
    ax.annotate(f"{widest}: {span.min():.1f}% to {span.max():.1f}%",
                (span.max(), y[widest]), xytext=(10, 0), textcoords="offset points",
                va="center", fontsize=9, color=t["ink2"])
    ax.set_yticks(list(y.values()), list(y.keys()), color=t["ink2"], fontsize=9)
    ax.set_xlabel("Poverty rate, % of people below the poverty line")
    ax.set_xlim(-2, 62)
    fig.subplots_adjust(left=0.15, right=0.97, top=0.85, bottom=0.15)
    finish(fig, t,
           "One dot per delegation: a governorate average hides a 35-point range",
           "Poverty rate of each of 253 delegations, grouped by governorate",
           "Carte de la pauvrete en Tunisie (INS, 2020). Modelled small-area estimates, "
           "not survey estimates: EBCNV is representative at region x milieu, not below. "
           "Siliana's table in that report carries no poverty column, so it is absent.")
    return fig


def fig_incidence_vs_share(p: pd.DataFrame, t: dict):
    """Who is most at risk is not who most of the poor are."""
    inc = panel(p, "poverty_rate", subgroup_type="head socio-professional category")
    con = panel(p, "poverty_contribution_relative",
                subgroup_type="head socio-professional category")
    d = (inc[["subgroup", "value"]].rename(columns={"value": "incidence"})
         .merge(con[["subgroup", "value"]].rename(columns={"value": "share"}), on="subgroup")
         .sort_values("incidence"))
    short = {
        "senior managers and professionals": "Senior managers, professions",
        "mid-level managers and professionals": "Mid-level managers",
        "other employees": "Other employees",
        "employers in industry, trade and services": "Employers",
        "own-account workers and artisans in industry, trade and services": "Own-account, artisans",
        "non-agricultural workers": "Non-agricultural workers",
        "farm operators": "Farm operators",
        "agricultural workers": "Agricultural workers",
        "unemployed": "Unemployed",
        "retired": "Retired",
        "other inactive": "Other inactive",
    }
    labels = [short.get(x, x) for x in d.subgroup]

    fig, ax = plt.subplots(figsize=(9.4, 5.2))
    dumbbell(ax, t, d["share"].to_numpy(), d["incidence"].to_numpy(), labels,
             "share of all poor people", "poverty rate within the group")
    # Label only the two groups that make the point: highest risk, and largest count.
    for name in ("Unemployed", "Non-agricultural workers"):
        idx = labels.index(name)
        row = d.iloc[idx]
        ax.annotate(f"{row.incidence:.0f}% poor, {row.share:.0f}% of the poor",
                    (max(row.incidence, row["share"]), idx), xytext=(11, 0),
                    textcoords="offset points", va="center", fontsize=8.5, color=t["ink2"])
    ax.set_xlabel("Percent")
    ax.set_xlim(0, 62)
    ax.legend(frameon=False, loc="lower right", labelcolor=t["ink2"], fontsize=9)
    fig.subplots_adjust(left=0.25, right=0.97, top=0.80, bottom=0.15)
    finish(fig, t,
           "The group most likely to be poor is not the group most of the poor belong to",
           "Poverty rate within each group, and each group's share of all poor people, 2021",
           "INS, EBCNV 2021 synthesis note, Tableau 9, by the household head's "
           "socio-professional category. Both series are percentages, so they share one axis.")
    return fig


def fig_deprivation(t: dict):
    """Inequality with no dinars in it: what a household actually has."""
    d = pd.read_csv(PROCESSED / "tn_hbs_2021_dwelling.csv")
    items = [
        ("Mains water, billed", "water_source", "SONEDE mains, billed"),
        ("Flush toilet", "toilet_type", "flush toilet"),
        ("Connected to sewerage", "connected_to_sewerage", "yes"),
        ("Bathroom with hot water", "bathroom_type", "bathroom with hot water"),
        ("Cooks on mains gas", "cooking_energy", "natural gas (STEG)"),
        ("Washing machine", "has_washing_machine", "yes"),
        ("Computer", "has_computer", "yes"),
        ("Refrigerator", "has_refrigerator", "yes"),
    ]
    poor, rich = d[d.poor == "poor"], d[d.poor == "not poor"]
    rows = [{"label": label,
             "poor": weighted_share(poor, poor[col].eq(target)),
             "rich": weighted_share(rich, rich[col].eq(target))}
            for label, col, target in items]
    frame = pd.DataFrame(rows).assign(gap=lambda x: x.rich - x.poor).sort_values("gap")

    fig, ax = plt.subplots(figsize=(9.0, 4.8))
    dumbbell(ax, t, frame["poor"].to_numpy(), frame["rich"].to_numpy(),
             frame["label"].tolist(), "poor", "not poor")
    for yi, row in enumerate(frame.itertuples()):
        ax.annotate(f"{row.gap:.0f} pts", (max(row.poor, row.rich), yi), xytext=(11, 0),
                    textcoords="offset points", va="center", fontsize=8.5, color=t["ink2"])
    ax.set_xlabel("% of people whose household has it")
    ax.set_xlim(0, 122)
    ax.legend(frameon=False, loc="upper right", labelcolor=t["ink2"], fontsize=9)
    fig.subplots_adjust(left=0.24, right=0.97, top=0.80, bottom=0.16)
    finish(fig, t,
           "A fridge is nearly universal. Mains gas and a computer are not.",
           "Household amenities, poor against non-poor, 2021",
           "Recomputed from EBCNV 2021 living-conditions microdata, weighted by the "
           "individual extrapolation factor.")
    return fig


def fig_protection(t: dict):
    """Contributory social insurance reaches the non-poor about twice as often."""
    i = pd.read_csv(PROCESSED / "tn_hbs_2021_individuals.csv")
    covered = i.dropna(subset=["social_insurance"]).copy()
    covered["affiliated"] = covered.social_insurance.isin(
        ["CNRPS (public sector fund)", "CNSS (private sector fund)"])
    rows = []
    for region, g in covered.groupby("region", observed=True):
        poor, rich = g[g.poor == "poor"], g[g.poor == "not poor"]
        rows.append({"label": str(region),
                     "poor": weighted_share(poor, poor.affiliated, weight="weight"),
                     "rich": weighted_share(rich, rich.affiliated, weight="weight")})
    frame = pd.DataFrame(rows).sort_values("rich")
    national_poor = weighted_share(covered[covered.poor == "poor"],
                                   covered[covered.poor == "poor"].affiliated, weight="weight")
    national_rich = weighted_share(covered[covered.poor == "not poor"],
                                   covered[covered.poor == "not poor"].affiliated, weight="weight")

    fig, ax = plt.subplots(figsize=(9.0, 4.8))
    dumbbell(ax, t, frame["poor"].to_numpy(), frame["rich"].to_numpy(),
             frame["label"].tolist(), "poor", "not poor")
    ax.set_xlabel("% affiliated to CNSS or CNRPS")
    ax.set_xlim(0, 62)
    ax.legend(frameon=False, loc="lower right", labelcolor=t["ink2"], fontsize=9)
    fig.subplots_adjust(left=0.19, right=0.97, top=0.80, bottom=0.17)
    finish(fig, t,
           f"Contributory cover reaches {national_rich:.0f}% of the non-poor "
           f"and {national_poor:.0f}% of the poor",
           "Affiliation to a contributory social-insurance fund, by region, 2021",
           "Recomputed from EBCNV 2021 health microdata, restricted to those the question "
           "was put to. INS's synthesis note reports 40.5% and 18.1% nationally. The "
           "sub-point difference is most likely the denominator, but INS does not state "
           "which base it used, so this is not a verified match.")
    return fig


def fig_literacy(t: dict):
    """The literacy gap by poverty status, across birth cohorts.

    Bands are cut from the raw ``age`` column rather than the four-way ``age_group``,
    which is too coarse to show a cohort gradient. The literacy question was put to
    respondents aged 10 and over, so this is restricted to 15+; every cell rests on at
    least 778 observations.
    """
    i = pd.read_csv(PROCESSED / "tn_hbs_2021_individuals.csv")
    lit = i.dropna(subset=["literate", "age"])
    lit = lit[lit.age >= 15]
    bands = [(15, 24, "15-24"), (25, 34, "25-34"), (35, 49, "35-49"),
             (50, 64, "50-64"), (65, 200, "65 and over")]
    rows = []
    for low, high, name in bands:
        g = lit[lit.age.between(low, high)]
        poor, rich = g[g.poor == "poor"], g[g.poor == "not poor"]
        rows.append({"label": name,
                     "poor": weighted_share(poor, poor.literate.eq("yes"), weight="weight"),
                     "rich": weighted_share(rich, rich.literate.eq("yes"), weight="weight")})
    frame = pd.DataFrame(rows).iloc[::-1].reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(9.0, 4.6))
    dumbbell(ax, t, frame["poor"].to_numpy(), frame["rich"].to_numpy(),
             frame["label"].tolist(), "poor", "not poor")
    for yi, row in enumerate(frame.itertuples()):
        gap = row.rich - row.poor
        ax.annotate(f"{gap:.0f} pts" if gap >= 1 else f"{gap:.1f} pts",
                    (row.rich, yi), xytext=(11, 0), textcoords="offset points",
                    va="center", fontsize=9, color=t["ink2"])
    ax.set_xlabel("% who can read and write")
    ax.set_xlim(0, 122)
    ax.legend(frameon=False, loc="upper left", labelcolor=t["ink2"], fontsize=9)
    fig.subplots_adjust(left=0.18, right=0.97, top=0.80, bottom=0.18)
    youngest = frame.iloc[-1]
    oldest = frame.iloc[0]
    finish(fig, t,
           "Among the under-25s the literacy gap has all but closed",
           f"Literacy by poverty status and age band, 2021. The gap runs from "
           f"{oldest.rich - oldest.poor:.0f} points among the over-65s to "
           f"{youngest.rich - youngest.poor:.1f} among the 15-24s.",
           "Recomputed from EBCNV 2021 education microdata, weighted by the household "
           "extrapolation factor. The literacy question was put to those aged 10 and over; "
           "this is restricted to 15 and over, with at least 778 observations per cell.")
    return fig


# --------------------------------------------------------- across the 2011 revolution

def fig_poverty_across(p: pd.DataFrame, t: dict):
    """National poverty 2005-2021, with the 2019 modelled point that changes the reading."""
    survey = poverty_series(p, geography="Tunisia", milieu="all", subgroup_type=None)
    modelled = poverty_series(p, geography="Tunisia", milieu="all", subgroup_type=None,
                              modelled=True)

    fig, ax = plt.subplots(figsize=(9.4, 5.0))
    mark_revolution(ax, t)
    ax.plot(survey.index, survey.to_numpy(), color=t["s1"], marker="o",
            markeredgecolor=t["surface"], markeredgewidth=1.2, zorder=3)
    ax.scatter(modelled.index, modelled.to_numpy(), s=95, color=t["surface"], zorder=4,
               edgecolor=t["s2"], linewidth=2.2)
    ax.annotate(f"2019: {modelled.iloc[0]:.1f}%\nmodelled, not surveyed",
                (2019, modelled.iloc[0]), xytext=(-8, -34), textcoords="offset points",
                ha="center", fontsize=8.5, color=t["ink2"])
    for wave in (2005, 2010, 2015, 2021):
        ax.annotate(f"{survey[wave]:.1f}%", (wave, survey[wave]), xytext=(0, 11),
                    textcoords="offset points", ha="center", fontsize=9.5, color=t["ink2"])
    ax.set_ylabel("% of people below the poverty line", color=t["ink2"], fontsize=9)
    ax.set_ylim(0, 27)
    ax.set_xticks([2005, 2010, 2015, 2019, 2021])
    fig.subplots_adjust(left=0.10, right=0.97, top=0.79, bottom=0.19)
    finish(fig, t,
           "Poverty was still falling in 2019. The rise happened in the COVID window.",
           "Share of people below the national poverty line, 2005-2021",
           "INS, EBCNV 2021 synthesis note, Tableau 6, and the 2019 estimate from p.10. "
           "Revised (2011) methodology throughout, which INS applied back to 2005 and "
           "2010. The 2019 figure is imputed from the 2018-19 follow-up panel, which "
           "collected no consumption data; the 2021 survey was fielded March 2021 to "
           "March 2022, during the pandemic. The rule marks when the revolution happened, "
           "not what caused what.")
    return fig


def fig_regional_gap_two_ways(p: pd.DataFrame, t: dict):
    """The Centre West against Grand Tunis, in ratio and in points. They disagree."""
    cw = poverty_series(p, geography_level="region", geography="Centre West",
                        subgroup_type=None)
    gt = poverty_series(p, geography_level="region", geography="Grand Tunis",
                        subgroup_type=None)
    waves = sorted(set(cw.index) & set(gt.index))
    ratio = (cw.loc[waves] / gt.loc[waves])
    difference = (cw.loc[waves] - gt.loc[waves])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.4, 4.8))
    for ax, series, title, unit, fmt in (
        (ax1, ratio, "Centre West poverty divided by Grand Tunis", "ratio", "{:.1f}x"),
        (ax2, difference, "Centre West poverty minus Grand Tunis", "percentage points",
         "{:.0f} pp"),
    ):
        mark_revolution(ax, t, label=(ax is ax1))
        ax.plot(series.index, series.to_numpy(), color=t["s1"], marker="o",
                markeredgecolor=t["surface"], markeredgewidth=1.2, zorder=3)
        # First label pushed right, last centred: at the left edge a centred label
        # lands on the y-axis ticks.
        for wave, offset, align in ((waves[0], (8, 8), "left"), (waves[-1], (0, 11), "center")):
            ax.annotate(fmt.format(series[wave]), (wave, series[wave]), xytext=offset,
                        textcoords="offset points", ha=align, fontsize=9.5,
                        color=t["ink2"])
        ax.set_title(title, color=t["ink"], loc="left", fontsize=10)
        ax.set_ylabel(unit, color=t["ink2"], fontsize=9)
        ax.set_xticks(waves)
    ax1.set_ylim(0, 9.5)
    ax2.set_ylim(0, 45)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.76, bottom=0.20, wspace=0.26)
    finish(fig, t,
           "Relative to the capital the gap doubled. In percentage points it barely moved.",
           "Two ways of measuring the same regional gap, 2005-2021",
           "INS, EBCNV 2021 synthesis note, Tableau 7, revised (2011) methodology. The "
           "ratio grew mostly because Grand Tunis fell from 11.1% to 4.7%, not because the "
           "Centre West rose. A figure showing only the ratio would mislead, which is why "
           "both are here. Separate panels because the units differ.")
    return fig


def fig_urban_rural_poverty(p: pd.DataFrame, t: dict):
    """Urban poverty is back above where it was before the revolution. Rural is not."""
    urban = poverty_series(p, geography="Tunisia", milieu="urban", subgroup_type=None)
    rural = poverty_series(p, geography="Tunisia", milieu="rural", subgroup_type=None)

    fig, ax = plt.subplots(figsize=(9.4, 5.0))
    mark_revolution(ax, t)
    ax.axhline(urban[2010], color=t["axis"], lw=1.2, zorder=1)
    for series, colour, name in ((rural, t["s2"], "Rural"), (urban, t["s1"], "Urban")):
        ax.plot(series.index, series.to_numpy(), color=colour, marker="o",
                markeredgecolor=t["surface"], markeredgewidth=1.2, zorder=3, label=name)
        ax.annotate(name, (series.index[-1], series.iloc[-1]), xytext=(9, -3),
                    textcoords="offset points", color=t["ink2"], fontsize=9.5)
    ax.annotate(f"urban level in 2010: {urban[2010]:.1f}%", (2005.1, urban[2010]),
                xytext=(0, -15), textcoords="offset points", fontsize=8.5,
                color=t["muted"])
    ax.set_ylabel("% of people below the poverty line", color=t["ink2"], fontsize=9)
    ax.set_ylim(0, 44)
    ax.set_xlim(2004, 2023)
    ax.set_xticks([2005, 2010, 2015, 2021])
    ax.legend(frameon=False, loc="upper right", labelcolor=t["ink2"])
    fig.subplots_adjust(left=0.10, right=0.97, top=0.79, bottom=0.17)
    finish(fig, t,
           "Rural poverty kept falling. Urban poverty ended above its pre-revolution level.",
           "Poverty rate by milieu, 2005-2021",
           "INS, EBCNV 2021 synthesis note, Tableau 6, revised (2011) methodology. Rural "
           "is territory outside the communes of the pre-2014 boundaries. The urban and "
           "rural series converged partly because rural improved and partly because urban "
           "did not.")
    return fig


def fig_budget_shift(p: pd.DataFrame, t: dict):
    """What moved in the household budget between the last pre- and post-revolution waves."""
    names = {1: "Food", 2: "Alcohol and tobacco", 3: "Clothing", 4: "Housing and energy",
             5: "Furniture", 6: "Health and hygiene", 7: "Transport", 8: "Communication",
             9: "Recreation", 10: "Education", 11: "Restaurants and holidays", 12: "Other"}
    b = panel(p, "budget_share", subgroup_type="COICOP function")
    wide = b.pivot_table(index="subgroup", columns="wave", values="value")
    wide.index = [names[int(i)] for i in wide.index]
    wide = wide.assign(change=wide[2021] - wide[2010]).sort_values("change")
    y = np.arange(len(wide))

    fig, ax = plt.subplots(figsize=(9.0, 5.0))
    ax.grid(axis="y", visible=False)
    ax.axvline(0, color=t["axis"], lw=1.4, zorder=1)
    colours = [t["s2"] if v < 0 else t["s1"] for v in wide["change"]]
    ax.barh(y, wide["change"], color=colours, height=0.66, zorder=2)
    for yi, value in zip(y, wide["change"], strict=True):
        offset = 6 if value >= 0 else -6
        ax.annotate(f"{value:+.1f}", (value, yi), xytext=(offset, 0),
                    textcoords="offset points", va="center",
                    ha="left" if value >= 0 else "right", fontsize=8.5, color=t["ink2"])
    ax.set_yticks(y, wide.index, color=t["ink2"])
    ax.set_xlabel("Change in share of the household budget, percentage points")
    ax.set_xlim(-3.4, 4.2)
    fig.subplots_adjust(left=0.23, right=0.97, top=0.79, bottom=0.23)
    finish(fig, t,
           "Clothing and health took a larger share; transport and communication a smaller",
           "Change in budget share by COICOP function, 2010 to 2021",
           "INS, EBCNV 2021 synthesis note, Tableau 4. 2010 is the last pre-revolution "
           "wave and 2021 the most recent. INS warns that the 2021 coefficients reflect "
           "the health crisis and should not be used to update the CPI basket, so this is "
           "a comparison of two years rather than a trend.")
    return fig


def fig_prices(t: dict):
    """What a fixed basket cost, 1999-2023, with the survey waves marked."""
    cpi = read("tn_cpi_annual")
    s = cpi[cpi.base_year == 2015].set_index("year")["index"].sort_index()

    fig, ax = plt.subplots(figsize=(9.4, 5.0))
    mark_revolution(ax, t)
    ax.plot(s.index, s.to_numpy(), color=t["s1"], zorder=3)
    waves = [2005, 2010, 2015, 2021]
    ax.scatter(waves, [s[w] for w in waves], s=80, color=t["surface"], zorder=4,
               edgecolor=t["s2"], linewidth=2.2)
    for wave in waves:
        ax.annotate(f"{wave}\n{s[wave]:.0f}", (wave, s[wave]), xytext=(0, -30),
                    textcoords="offset points", ha="center", fontsize=8.5, color=t["ink2"])
    ax.set_ylabel("index, 2015 = 100", color=t["ink2"], fontsize=9)
    ax.set_ylim(40, 180)
    ax.annotate("EBCNV survey waves", (2005, s[2005]), xytext=(14, 12),
                textcoords="offset points", fontsize=8.5, color=t["s2"])
    fig.subplots_adjust(left=0.09, right=0.97, top=0.79, bottom=0.19)
    finish(fig, t,
           "Prices rose 77% between the 2010 and 2021 surveys",
           "Consumer price index, 1999-2023, base 2015 = 100",
           "INS, Annuaire Statistique de la Tunisie 2023 edition, table 13.6. The eight "
           "base years INS publishes are rescalings of one series; this uses 2015 "
           "throughout. Orange markers are the EBCNV waves the rest of this directory "
           "rests on -- the dinar figures in figures 1 to 3 are nominal, and this is the "
           "yardstick they are not divided by.")
    return fig


# EBCNV consumption functions whose CPI division covers the same goods. Functions 6, 11
# and 12 are excluded: EBCNV's function 6 is "Hygiene et soins" while the CPI's division
# 6 is "Sante" with personal care filed under division 12, and EBCNV's function 11 folds
# holidays in with restaurants. Plotting those three would compare different baskets.
COMPARABLE_FUNCTIONS = (1, 2, 3, 4, 5, 7, 8, 9, 10)

FUNCTION_NAMES = {1: "Food", 2: "Alcohol and tobacco", 3: "Clothing",
                  4: "Housing and energy", 5: "Furniture", 6: "Health and hygiene",
                  7: "Transport", 8: "Communication", 9: "Recreation", 10: "Education",
                  11: "Restaurants and holidays", 12: "Other"}


def fig_price_against_budget(p: pd.DataFrame, t: dict):
    """Price change against budget-share change, 2015 to 2021. They are not the same thing."""
    shares = panel(p, "budget_share", subgroup_type="COICOP function").copy()
    shares["code"] = shares.subgroup.astype(int)
    wide = shares.pivot_table(index="code", columns="wave", values="value")
    prices = read("tn_cpi_by_division")
    prices = prices[prices.year == 2021].set_index("function_code")["index"]

    codes = list(COMPARABLE_FUNCTIONS)
    x = [prices[c] - 100 for c in codes]
    y = [wide.loc[c, 2021] - wide.loc[c, 2015] for c in codes]
    all_items = float(prices[0]) - 100

    fig, ax = plt.subplots(figsize=(9.4, 5.4))
    ax.axhline(0, color=t["axis"], lw=1.4, zorder=1)
    ax.axvline(all_items, color=t["muted"], lw=1.2, ls=(0, (5, 4)), zorder=1)
    ax.annotate(f"all items  +{all_items:.0f}%", (all_items, 0.02),
                xycoords=("data", "axes fraction"), xytext=(6, 0),
                textcoords="offset points", fontsize=8.5, color=t["muted"])
    ax.scatter(x, y, s=95, color=t["s1"], zorder=3,
               edgecolor=t["surface"], linewidth=1.2)
    # (offset, horizontal alignment) per point. Hand-placed: "above or below" alone
    # collides with the zero rule, the all-items rule, and the Housing/Transport pair,
    # and centred labels on the rightmost point run off the axis.
    placement = {
        1: ((-11, 4), "right"), 2: ((0, 13), "center"), 3: ((0, 13), "center"),
        4: ((-11, 0), "right"), 5: ((0, -20), "center"), 7: ((11, 4), "left"),
        8: ((0, -20), "center"), 9: ((0, -20), "center"), 10: ((0, -20), "center"),
    }
    for code, xi, yi in zip(codes, x, y, strict=True):
        (dx, dy), ha = placement[code]
        ax.annotate(FUNCTION_NAMES[code], (xi, yi), xytext=(dx, dy),
                    textcoords="offset points", ha=ha, va="center",
                    fontsize=8.5, color=t["ink2"])
    ax.set_xlabel("Change in price, 2015 to 2021 (%)")
    ax.set_ylabel("Change in share of the budget (pp)", color=t["ink2"], fontsize=9)
    ax.set_xlim(-4, 74)
    ax.set_ylim(-4.4, 5.6)
    fig.subplots_adjust(left=0.09, right=0.97, top=0.80, bottom=0.20)
    finish(fig, t,
           "Clothing took a bigger share of the budget mostly because it cost more",
           "Price change against budget-share change by consumption function, 2015 to 2021",
           "Prices from INS, Annuaire Statistique 2023 edition, table 13.7 (base 2015 = "
           "100); budget shares from the EBCNV synthesis note, Tableau 4. Nine of the "
           "twelve functions are shown: EBCNV's function 6 is hygiene and care while the "
           "CPI's division 6 is health with personal care filed elsewhere, and EBCNV "
           "folds holidays into restaurants, so those three compare different baskets. A "
           "share can rise because quantity rose or because price did; this figure "
           "separates the two questions, it does not answer the second.")
    return fig


def fig_unemployment(t: dict):
    """Unemployment by education since the revolution. The gradient runs the wrong way."""
    u = read("tn_unemployment_annual")
    u = u[u.breakdown == "education"]
    wide = u.pivot_table(index="year", columns="group", values="unemployment_rate")
    levels = [("none", "No schooling"), ("primary", "Primary"),
              ("secondary", "Secondary"), ("higher", "Higher education")]

    fig, axes = plt.subplots(2, 2, figsize=(9.4, 5.8), sharex=True, sharey=True)
    for ax, (key, label) in zip(axes.ravel(), levels, strict=True):
        ax.plot(wide.index, wide["all"], color=t["muted"], lw=1.4, zorder=2)
        ax.plot(wide.index, wide[key], color=t["s1"], zorder=3)
        ax.set_title(label, color=t["ink"], fontsize=10, loc="left")
        ax.set_ylim(0, 34)
        ax.set_xticks([2011, 2015, 2019, 2023])
    axes[0][0].annotate("national", (2016, wide.loc[2016, "all"]), xytext=(0, -20),
                        textcoords="offset points", fontsize=8.5, color=t["muted"],
                        ha="center")
    axes[0][0].set_ylabel("% of the labour force", color=t["ink2"], fontsize=9)
    axes[1][0].set_ylabel("% of the labour force", color=t["ink2"], fontsize=9)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.76, bottom=0.20, hspace=0.32, wspace=0.10)
    finish(fig, t,
           "The more schooling, the higher the unemployment -- every year since 2011",
           "Unemployment rate by education level, 2011-2023, against the national rate",
           "INS, Annuaire Statistique de la Tunisie, 2015, 2019 and 2023 editions, table "
           "6.1.3, surveyed each May. Where editions overlap they agree exactly, which is "
           "what checks the splice. This series does not reach before 2011: the 2005, "
           "2010 and 2012 yearbooks carry no unemployment table, so it describes the "
           "period since the revolution and cannot compare across it.")
    return fig


# ------------------------------------------------------ health, school, work, buying

def fig_out_of_pocket(t: dict):
    """What households pay out of pocket for care, poor against non-poor."""
    ind = read("tn_hbs_2021_individuals")
    items = [("consultation_expenditure", "Doctor visits, tests, imaging"),
             ("medicine_expenditure", "Medicine"),
             ("chronic_disease_expenditure", "Chronic illness"),
             ("hospital_stay_expenditure", "Hospital stay")]
    poor, rich, labels_, counts = [], [], [], []
    for column, label in items:
        d = clean_numeric(ind, column)
        d = d[d[column] > 0]
        poor.append(d[d.poor == "poor"][column].median())
        rich.append(d[d.poor == "not poor"][column].median())
        counts.append(len(d))
        labels_.append(label)

    fig, ax = plt.subplots(figsize=(9.0, 4.6))
    y = dumbbell(ax, t, poor, rich, labels_, "Poor", "Not poor")
    for yi, lo, hi in zip(y, poor, rich, strict=True):
        ax.annotate(f"{lo:.0f}", (lo, yi), xytext=(-9, 0), textcoords="offset points",
                    ha="right", va="center", fontsize=8.5, color=t["ink2"])
        ax.annotate(f"{hi:.0f}", (hi, yi), xytext=(9, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=8.5, color=t["ink2"])
    ax.set_xlabel("Median annual out-of-pocket spending, dinars")
    ax.set_xlim(0, 470)
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    fig.subplots_adjust(left=0.27, right=0.97, top=0.78, bottom=0.24)
    finish(fig, t,
           "The poor pay less out of pocket at every step, and fewer of them pay at all",
           "Median out-of-pocket health spending among those who report any, 2021",
           "EBCNV 2021 health module, recomputed. Medians among people reporting a "
           "positive amount, so the bars are conditional on using care at all: 69% of the "
           "poor report paying for a consultation against 79% of the non-poor. INS's "
           "non-declared sentinel codes are dropped. These amounts are in dinars -- INS's "
           "own labels give no unit, and the household file settles it. The hospital row "
           "rests on 87 poor and 720 non-poor observations and should be read as "
           "indicative; the other three rest on 769 to 16,603.")
    return fig


def fig_chronic(t: dict):
    """Reported chronic illness, and who holds a card, among those who report it."""
    ind = read("tn_hbs_2021_individuals")
    have = ind[ind.has_chronic_disease.notna()]
    prevalence = [weighted_share(have[have.poor == g], have[have.poor == g]
                                 .has_chronic_disease.eq("yes"), weight="weight")
                  for g in ("poor", "not poor")]
    ill = ind[ind.has_chronic_disease.eq("yes") & ind.care_card.notna()]
    nocard = [weighted_share(ill[ill.poor == g], ill[ill.poor == g].care_card.eq("none"),
                             weight="weight") for g in ("poor", "not poor")]

    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.4))
    for ax, values, title, top in (
        (axes[0], prevalence, "Report a chronic illness", 26),
        (axes[1], nocard, "Of those, hold no care card", 92),
    ):
        ax.grid(axis="x", visible=False)
        ax.bar(["Poor", "Not poor"], values, color=[t["s2"], t["s1"]], width=0.55, zorder=2)
        for x, value in enumerate(values):
            ax.annotate(f"{value:.1f}%", (x, value), xytext=(0, 5),
                        textcoords="offset points", ha="center", fontsize=9.5,
                        color=t["ink2"])
        ax.set_title(title, color=t["ink"], fontsize=10, loc="left")
        ax.set_ylim(0, top)
    axes[0].set_ylabel("% of people", color=t["ink2"], fontsize=9)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.76, bottom=0.26, wspace=0.22)
    finish(fig, t,
           "The poor report half as much chronic illness, which is unlikely to mean they have less",
           "Reported chronic illness and care-card cover, 2021",
           "EBCNV 2021 health module, recomputed. A chronic illness has to be diagnosed "
           "before it can be reported, so the left panel most plausibly measures contact "
           "with a doctor rather than health -- read alongside figure 20, where the poor "
           "spend and consult less. The right panel is the clearer finding on its own "
           "terms: free and reduced-tariff cards do reach the poor more often (34.1% "
           "against 20.0%), and still leave roughly two thirds of the chronically ill "
           "poor holding no card at all.")
    return fig


def fig_leaving_school(t: dict):
    """Why people left school, poor against non-poor."""
    ind = read("tn_hbs_2021_individuals")
    shares = category_shares(ind, "reason_left_school", "poor", "weight")
    shares = shares.sort_values("poor")
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    dumbbell(ax, t, shares["poor"], shares["not poor"], list(shares.index),
             "Poor", "Not poor")
    ax.set_xlabel("% of people who left education, by reason given")
    ax.set_xlim(0, 50)
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    fig.subplots_adjust(left=0.30, right=0.97, top=0.78, bottom=0.22)
    finish(fig, t,
           "Cost drives the poor out of school; the non-poor are three times likelier to finish",
           "Reason given for leaving education, by poverty status, 2021",
           "EBCNV 2021 education module, recomputed, weighted by person. Asked of people "
           "who had left education. \"Completed studies\" is the one answer that is not a "
           "reason for dropping out, and it separates the two groups most sharply: 18.9% "
           "against 6.4%.")
    return fig


def fig_school_distance(t: dict):
    """How far school is, and how long it takes to reach, urban against rural."""
    ind = read("tn_hbs_2021_individuals")
    bands = ["under 2 km", "2-4 km", "over 4 km"]
    shares = category_shares(ind, "school_distance", "milieu", "weight").loc[bands]
    travel = clean_numeric(ind[ind.travel_time_to_school_min.notna()],
                           "travel_time_to_school_min")

    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.6), width_ratios=[1.35, 1])
    ax = axes[0]
    ax.grid(axis="x", visible=False)
    x = np.arange(len(bands))
    ax.bar(x - 0.19, shares["urban"], width=0.36, color=t["s1"], label="Urban", zorder=2)
    ax.bar(x + 0.19, shares["rural"], width=0.36, color=t["s2"], label="Rural", zorder=2)
    for xi, (urban, rural) in enumerate(zip(shares["urban"], shares["rural"], strict=True)):
        ax.annotate(f"{urban:.0f}", (xi - 0.19, urban), xytext=(0, 4),
                    textcoords="offset points", ha="center", fontsize=8.5, color=t["ink2"])
        ax.annotate(f"{rural:.0f}", (xi + 0.19, rural), xytext=(0, 4),
                    textcoords="offset points", ha="center", fontsize=8.5, color=t["ink2"])
    ax.set_xticks(x, bands, color=t["ink2"])
    ax.set_ylim(0, 82)
    ax.set_ylabel("% of pupils and students", color=t["ink2"], fontsize=9)
    ax.set_title("Distance to the institution", color=t["ink"], fontsize=10, loc="left")
    ax.legend(loc="upper right", frameon=False, fontsize=9)

    ax = axes[1]
    ax.grid(axis="x", visible=False)
    quantiles = [0.25, 0.5, 0.75]
    for offset, milieu, colour in ((-0.16, "urban", t["s1"]), (0.16, "rural", t["s2"])):
        block = travel[travel.milieu == milieu]
        lo, mid, hi = weighted_quantile(block.travel_time_to_school_min,
                                        block["weight"], quantiles)
        ax.plot([offset, offset], [lo, hi], color=colour, lw=6, solid_capstyle="round",
                alpha=0.35, zorder=2)
        ax.scatter([offset], [mid], s=90, color=colour, zorder=3,
                   edgecolor=t["surface"], linewidth=1.2)
        ax.annotate(f"{mid:.0f} min", (offset, mid), xytext=(14, 0),
                    textcoords="offset points", va="center", fontsize=9, color=t["ink2"])
    ax.set_xticks([-0.16, 0.16], ["Urban", "Rural"], color=t["ink2"])
    ax.set_xlim(-0.5, 0.6)
    ax.set_ylim(0, 62)
    ax.set_ylabel("minutes", color=t["ink2"], fontsize=9)
    ax.set_title("Travel time, median and quartiles", color=t["ink"], fontsize=10, loc="left")

    fig.subplots_adjust(left=0.08, right=0.97, top=0.76, bottom=0.22, wspace=0.30)
    finish(fig, t,
           "A rural pupil is three times as likely to be more than 4 km from school",
           "Distance and travel time to the education institution, 2021",
           "EBCNV 2021 education module, recomputed, weighted by person, among those "
           "currently enrolled. Non-declared sentinel times are dropped. Distance is "
           "not only an inconvenience: asked separately why they never attended at all, "
           "18.8% of the poor and 24.6% of the non-poor answer that school was too far. "
           "That is a different question from figure 22, which asks people who did "
           "attend why they left.")
    return fig


def fig_not_working(t: dict):
    """Why people are not working. The answer is almost entirely about sex."""
    ind = read("tn_hbs_2021_individuals")
    shares = category_shares(ind, "reason_not_working", "sex", "weight")
    shares = shares[shares.max(axis=1) >= 2].sort_values("female")

    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    dumbbell(ax, t, shares["male"], shares["female"], list(shares.index),
             "Men", "Women")
    ax.set_xlabel("% of people not in work, by reason given")
    ax.set_xlim(0, 62)
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    fig.subplots_adjust(left=0.26, right=0.97, top=0.78, bottom=0.22)
    finish(fig, t,
           "Housework keeps 55% of non-working women out of work, and 0.6% of men",
           "Reason given for not working, by sex, 2021",
           "EBCNV 2021 labour module, recomputed, weighted by person. Reasons given by "
           "fewer than 2% of both sexes are omitted. Read with figure 19: the "
           "unemployment rate counts only people looking for work, so the women in the "
           "top row are not in it at all.")
    return fig


def fig_where_poor_work(t: dict):
    """The poor are not less likely to be employees. They work somewhere else."""
    ind = read("tn_hbs_2021_individuals")
    shares = category_shares(ind, "workplace", "poor", "weight")
    shares = shares[shares.max(axis=1) >= 4].sort_values("poor")

    fig, ax = plt.subplots(figsize=(9.2, 5.0))
    dumbbell(ax, t, shares["poor"], shares["not poor"], list(shares.index),
             "Poor", "Not poor")
    ax.set_xlabel("% of working people, by where they work")
    ax.set_xlim(0, 26)
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    fig.subplots_adjust(left=0.31, right=0.97, top=0.79, bottom=0.21)
    finish(fig, t,
           "Farms and building sites for the poor; the state and firms for everyone else",
           "Where working people work, by poverty status, 2021",
           "EBCNV 2021 labour module, recomputed, weighted by person. Workplaces below 4% "
           "in both groups are omitted. Employment status barely separates the two -- 82% "
           "of the working poor are employees against 80% of the non-poor -- so what "
           "distinguishes them is not self-employment but the sector they are employed "
           "in. Public administration and public enterprises together take 22.0% of "
           "non-poor workers and 9.6% of poor ones.")
    return fig


def fig_where_bought(t: dict):
    """Where the money is actually spent, poor against non-poor."""
    household = read("tn_hbs_2021_household", ["hh_id", "poor", "weight_hh"])
    lines = read("tn_hbs_2021_expenditure",
                 ["hh_id", "expenditure_annual_dt", "purchase_place"])
    lines = lines.merge(household, on="hh_id", how="left")
    lines = lines[lines.purchase_place.notna()]
    # Weight by dinars, not by lines: the question is where the money goes, and one
    # supermarket trip is not one loaf of bread.
    lines["spend"] = lines.expenditure_annual_dt * lines.weight_hh

    table = {}
    for group, block in lines.groupby("poor", observed=True):
        table[group] = block.groupby("purchase_place", observed=True)["spend"].sum() \
            / block["spend"].sum() * 100
    shares = pd.DataFrame(table)
    shares = shares[shares.max(axis=1) >= 1].sort_values("poor")

    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    y = dumbbell(ax, t, shares["poor"], shares["not poor"], list(shares.index),
                 "Poor", "Not poor")
    # Label the outside of each pair, not "poor on the left": the two cross whenever
    # the poor share is the larger one, which put both labels inside the rule.
    for yi, lo, hi in zip(y, shares["poor"], shares["not poor"], strict=True):
        for value, offset, align in ((min(lo, hi), -9, "right"), (max(lo, hi), 9, "left")):
            ax.annotate(f"{value:.1f}", (value, yi), xytext=(offset, 0),
                        textcoords="offset points", ha=align, va="center",
                        fontsize=8.5, color=t["ink2"])
    ax.set_xscale("log")
    ax.set_xlim(0.4, 200)
    ax.set_xticks([1, 3, 10, 30, 90], ["1%", "3%", "10%", "30%", "90%"])
    ax.set_xlabel("Share of all household spending, log scale")
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    fig.subplots_adjust(left=0.24, right=0.97, top=0.78, bottom=0.24)
    finish(fig, t,
           "The poor's money goes to the weekly market, not the supermarket",
           "Where household spending goes, by type of outlet, 2021",
           "EBCNV 2021 product-level file, 3.26M acquisition lines, recomputed. Shares of "
           "dinars rather than of lines, so a supermarket trip is not counted equal to a "
           "loaf of bread. The log scale is needed because the private shop takes more "
           "than 80% of both groups' spending; without it every other outlet would be "
           "invisible. Own production is 2.1% of poor spending against 0.9% of non-poor, "
           "and 2.9% of rural against 0.4% of urban.")
    return fig

# ------------------------------------------- can the revolution's effect be identified?
#
# These four ask whether the yearbook panel can support a causal claim about January
# 2011, and answer no -- by running the tests rather than asserting the conclusion.
#
# The obstacle is structural. The revolution treated all 24 governorates at the same
# instant, so there is no untreated unit inside Tunisia and no donor pool here to build
# a synthetic one from. That leaves an interrupted time series, whose counterfactual is
# an extrapolated pre-trend, or a difference-in-differences on differential exposure,
# which needs parallel pre-trends. Figures 28 and 29 test exactly those two things.

GOVERNORATES = [
    "Tunis", "Ariana", "Ben Arous", "Manouba", "Nabeul", "Zaghouan", "Bizerte", "Béja",
    "Jendouba", "Le Kef", "Siliana", "Sousse", "Monastir", "Mahdia", "Sfax", "Kairouan",
    "Kasserine", "Sidi Bouzid", "Gabès", "Medenine", "Tataouine", "Gafsa", "Tozeur",
    "Kébili",
]

# INS's own western regions: Nord-Ouest, Centre-Ouest, Sud-Ouest. Used as the
# differential-exposure split in figure 29 -- the interior is where the revolution began
# and where the grievance was concentrated.
INTERIOR = {"Béja", "Jendouba", "Le Kef", "Siliana", "Kairouan", "Kasserine",
            "Sidi Bouzid", "Gafsa", "Tozeur", "Kébili"}


def pupils_per_teacher() -> pd.DataFrame:
    """Governorate x year panel, 1998-2018. Rows are governorates, columns years.

    Pupils per teacher in the first cycle of basic education: a provision ratio that
    needs no population denominator, since both halves come from the same chapter and
    the same years. 23 governorates (Medenine is absent from the staff table) over 21
    years, 481 of 483 cells present.
    """
    series = read("tn_yearbook_series")

    def block(title: str) -> pd.DataFrame:
        rows = series[series.title_fr.eq(title) & series.row_label.isin(GOVERNORATES)]
        return rows.groupby(["row_label", "year"]).value.first().unstack()

    return (block("population scolaire totale du 1er cycle 8")
            / block("personnel enseignant par gouvernorat")).dropna(how="all")


def _segmented(years, values, break_year):
    """Level shift at ``break_year`` from a segmented regression -- the ITS estimate."""
    post = (years >= break_year).astype(float)
    design = np.column_stack([np.ones_like(years, dtype=float), years - break_year,
                              post, (years - break_year) * post])
    return np.linalg.lstsq(design, values, rcond=None)[0][2]


def fig_counterfactual(t: dict):
    """The ITS answer depends entirely on which pre-trend you extrapolate."""
    panel = pupils_per_teacher()
    national = panel.mean()
    years = np.array(sorted(national.index))
    pre = years[years <= 2010]

    # The last two land within 0.8 of each other at 2018, so the label offsets are
    # explicit rather than uniform.
    models = [("Linear, 1998-2010", pre, 1, 0), ("Quadratic, 1998-2010", pre, 2, -16),
              ("Linear, 2006-2010", pre[pre >= 2006], 1, 14)]
    future = years[years >= 2010].astype(float)

    fig, ax = plt.subplots(figsize=(9.4, 5.2))
    mark_revolution(ax, t)
    for label, window, degree, lift in models:
        fitted = np.polyval(np.polyfit(window.astype(float), national[window].to_numpy(),
                                       degree), future)
        ax.plot(future, fitted, color=t["muted"], lw=1.4, ls=(0, (5, 4)), zorder=2)
        ax.annotate(f"{label}\n\"effect\" {national[2018] - fitted[-1]:+.1f}",
                    (2018, fitted[-1]), xytext=(6, lift), textcoords="offset points",
                    va="center", fontsize=8, color=t["muted"])
    ax.plot(years, national.to_numpy(), color=t["s1"], zorder=3)
    ax.annotate("observed", (2016, national[2016]), xytext=(-4, 12),
                textcoords="offset points", ha="right", fontsize=9, color=t["s1"])
    ax.set_ylabel("pupils per teacher", color=t["ink2"], fontsize=9)
    ax.set_xlim(1997, 2026)
    ax.set_ylim(9, 26)
    fig.subplots_adjust(left=0.08, right=0.78, top=0.79, bottom=0.17)
    finish(fig, t,
           "The counterfactual is an assumption, and it decides the answer",
           "Pupils per teacher, first cycle, 23 governorates averaged, 1998-2018",
           "INS yearbooks, tables 2.1.5 and 2.1.8. An interrupted time series compares "
           "what happened against a pre-trend carried forward, so the estimate is only "
           "as good as that extrapolation. Three defensible choices give effects from "
           "+2.6 to +6.9 pupils per teacher -- a factor of 2.7 -- and nothing in the "
           "data adjudicates between them. Read this as a demonstration that the design "
           "is unidentified, not as an estimate.")
    return fig


def fig_placebo_breaks(t: dict):
    """If 2011 is not special, the break cannot be attributed to it."""
    panel = pupils_per_teacher()
    national = panel.mean()
    years = np.array(sorted(national.index))
    values = national[years].to_numpy()
    candidates = np.arange(2003, 2016)
    steps = [_segmented(years, values, int(b)) for b in candidates]

    fig, ax = plt.subplots(figsize=(9.4, 5.0))
    ax.axhline(0, color=t["axis"], lw=1.4, zorder=1)
    colours = [t["s2"] if b == REVOLUTION else t["s1"] for b in candidates]
    ax.bar(candidates, steps, color=colours, width=0.62, zorder=2)
    revolution = steps[list(candidates).index(REVOLUTION)]
    ax.annotate(f"2011\n{revolution:+.2f}", (REVOLUTION, revolution), xytext=(0, 8),
                textcoords="offset points", ha="center", fontsize=9, color=t["s2"])
    peak = int(candidates[int(np.argmax(steps))])
    ax.annotate(f"largest step is {peak}", (peak, max(steps)), xytext=(0, 26),
                textcoords="offset points", ha="center", fontsize=8.5, color=t["ink2"])
    ax.set_ylabel("estimated level shift (pupils per teacher)", color=t["ink2"], fontsize=9)
    ax.set_xlabel("break year assumed")
    ax.set_xticks(candidates[::2])
    ax.set_ylim(-2.4, 2.4)
    fig.subplots_adjust(left=0.10, right=0.97, top=0.79, bottom=0.19)
    finish(fig, t,
           "Every year from 2009 on gives about the same break. 2011 is not special.",
           "Level shift estimated by segmented regression at each assumed break year",
           "The same interrupted-time-series specification run thirteen times, moving "
           "only the assumed break. If January 2011 caused a discrete change, the "
           "estimate should peak there. It does not: 2010 gives an identical +1.06, and "
           "2014 and 2015 give larger steps. A smooth ramp of estimates across candidate "
           "years is the signature of a gradual trend change, which a single-break "
           "design cannot separate from an event.")
    return fig


def fig_parallel_trends(t: dict):
    """Differential exposure needs parallel pre-trends. They are not parallel."""
    panel = pupils_per_teacher()
    interior = panel[panel.index.isin(INTERIOR)].mean()
    coastal = panel[~panel.index.isin(INTERIOR)].mean()
    gap = (interior - coastal).sort_index()
    years = np.array(gap.index)
    pre = years[years <= 2010]
    slope = np.polyfit(pre.astype(float), gap[pre].to_numpy(), 1)[0]

    fig, ax = plt.subplots(figsize=(9.4, 5.2))
    mark_revolution(ax, t)
    ax.axhline(0, color=t["axis"], lw=1.4, zorder=1)
    ax.plot(years[years <= 2010], gap[years <= 2010].to_numpy(), color=t["s2"], zorder=3)
    ax.plot(years[years >= 2010], gap[years >= 2010].to_numpy(), color=t["s1"], zorder=3)
    # Placed in the empty lower-left rather than offset from the line: any offset small
    # enough to read as attached put the text across the line itself.
    ax.text(1998.4, -4.3, f"already diverging\n{slope:+.2f} per year before 2011",
            fontsize=8.5, color=t["s2"])
    ax.set_ylabel("interior minus coastal (pupils per teacher)", color=t["ink2"], fontsize=9)
    ax.set_ylim(-5.4, 0.8)
    ax.set_xticks(range(1998, 2019, 4))
    fig.subplots_adjust(left=0.10, right=0.97, top=0.79, bottom=0.17)
    finish(fig, t,
           "The two groups were diverging for twelve years before the revolution",
           "Gap in pupils per teacher, interior governorates against the rest, 1998-2018",
           "The interior -- INS's Nord-Ouest, Centre-Ouest and Sud-Ouest, where the "
           "revolution began -- against the coastal and metropolitan governorates. A "
           "difference-in-differences on this split needs the two groups to have been on "
           "parallel paths beforehand. They were not: the gap widened every year from "
           "1998, by 0.21 a year, so any post-2011 difference is indistinguishable from "
           "a trend that was already running. Note the sign: interior governorates have "
           "*fewer* pupils per teacher, small rural schools against crowded coastal ones.")
    return fig


def fig_dispersion(t: dict):
    """What the data does support: description, with no break at 2011."""
    panel = pupils_per_teacher()
    years = np.array(sorted(panel.columns))
    widest = (panel.max() / panel.min())[years]
    middle = (panel.quantile(0.75) / panel.quantile(0.25))[years]

    fig, ax = plt.subplots(figsize=(9.4, 5.0))
    mark_revolution(ax, t)
    ax.plot(years, widest.to_numpy(), color=t["s1"], zorder=3)
    ax.plot(years, middle.to_numpy(), color=t["s2"], zorder=3)
    ax.annotate("highest governorate / lowest", (2015, widest[2015]), xytext=(0, 10),
                textcoords="offset points", ha="center", fontsize=8.5, color=t["s1"])
    ax.annotate("upper quartile / lower quartile", (2015, middle[2015]), xytext=(0, -20),
                textcoords="offset points", ha="center", fontsize=8.5, color=t["s2"])
    for year in (1998, 2010, 2018):
        ax.annotate(f"{widest[year]:.2f}", (year, widest[year]), xytext=(0, 10),
                    textcoords="offset points", ha="center", fontsize=9, color=t["ink2"])
    ax.set_ylabel("ratio between governorates", color=t["ink2"], fontsize=9)
    ax.set_ylim(0.95, 2.15)
    ax.set_xticks(range(1998, 2019, 4))
    fig.subplots_adjust(left=0.09, right=0.97, top=0.79, bottom=0.17)
    finish(fig, t,
           "Regional spread widened steadily from 1998, straight through 2011",
           "Dispersion in pupils per teacher across 23 governorates, 1998-2018",
           "Two ratios between observed quantities, so no composite index is involved. "
           "The widest gap grew from 1.21 to 1.93 and the interquartile ratio from 1.06 "
           "to 1.29, both climbing before, across and after the revolution with no step "
           "at 2011. This is the honest summary the other three figures leave standing: "
           "regional provision diverged over two decades, and the yearbook data cannot "
           "attribute any part of that to the revolution.")
    return fig


# --- Regression discontinuity in time -------------------------------------------------
#
# Figures 27-30 ruled out the designs that need an untreated unit. RDiT needs none: the
# running variable is the calendar and the cutoff is the event, so nobody can be on the
# wrong side of it by choice. What it does need is to get close to the cutoff, and how
# close depends on how often the series is published. The corpus holds both a monthly
# series and an annual one, so these four figures ask the same question of each.

MONTH_NAMES = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août",
               "Septembre", "Octobre", "Novembre", "Décembre"]

# Table 14.1 runs on this basis from 2003. Earlier editions print monthly trade under a
# different table with a different coverage, and splicing them would put a seam eight
# years before the cutoff.
TRADE_FROM, TRADE_TO = 2003, 2023

TRADE_BANDWIDTH = 12       # months either side, for the fitted lines in figure 31
PLACEBO_BANDWIDTH = 12     # months, for the placebo sweep in figure 32


def monthly_trade() -> pd.DataFrame:
    """Monthly imports and exports, million dinars, 2003-2023.

    Table 14.1 prints the twelve months twice, once under each of its two panels. Until
    the panel heading was carried into the row label the second copy was dropped as a
    duplicate row, so the whole exports half of this table was missing from the corpus.
    """
    series = read("tn_yearbook_series")
    rows = series[series.title_fr.str.contains("mensuelle des échanges", na=False)].copy()
    rows["panel"] = rows.row_label.str.rsplit(" / ", n=1).str[0]
    rows["month"] = rows.row_label.str.rsplit(" / ", n=1).str[-1]
    rows = rows[rows.month.isin(MONTH_NAMES)
                & rows.panel.isin(["Importations", "Exportations"])]
    rows["m"] = rows.month.map({name: i + 1 for i, name in enumerate(MONTH_NAMES)})
    rows = rows[rows.year.between(TRADE_FROM, TRADE_TO)]
    flat = rows.groupby(["panel", "year", "m"], as_index=False).value.mean()
    flat["t"] = flat.year + (flat.m - 1) / 12
    return flat.sort_values(["panel", "t"]).reset_index(drop=True)


def trade_series(panel: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Months from January 2011, deseasonalised log level, and the calendar date."""
    g = monthly_trade()
    g = g[g.panel == panel].sort_values("t")
    running = (g.t.to_numpy() - rdit.CUTOFF) * 12
    adjusted = rdit.deseasonalise(running, np.log(g.value.to_numpy()), g.m.to_numpy())
    return running, adjusted, g.t.to_numpy()


def regional_gap() -> tuple[np.ndarray, np.ndarray]:
    """Interior minus coastal pupils per teacher by school year -- figure 29's outcome.

    Dated on the school year's opening: 2011/12 began in September 2011 and is the first
    intake organised after the uprising, so it is the first treated period.
    """
    p = pupils_per_teacher()
    years = np.array(sorted(p.columns), dtype=float)
    interior = p.loc[p.index.isin(INTERIOR)].mean()
    coastal = p.loc[~p.index.isin(INTERIOR)].mean()
    return years - 2011.0, (interior - coastal).reindex(years).to_numpy()


def _side_fit(running, y, bandwidth, treated):
    """Weighted local linear fit on one side; returns the grid, the curve, and the edge."""
    keep = ((running >= 0) == treated) & (np.abs(running) <= bandwidth)
    x, outcome = running[keep], y[keep]
    weights = rdit.triangular(x / bandwidth)
    design = np.column_stack([np.ones_like(x), x])
    gram = design.T @ (design * weights[:, None])
    beta = np.linalg.pinv(gram) @ (design.T @ (outcome * weights))
    grid = np.linspace(x.min(), x.max(), 60)
    return grid, beta[0] + beta[1] * grid, float(beta[0])


def fig_rdit_monthly(t: dict):
    """RDiT where the calendar is dense enough to use it."""
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 5.4))
    fig.subplots_adjust(top=0.68, bottom=0.29, left=0.075, right=0.985, wspace=0.22)

    jumps = {}
    for ax, panel in zip(axes, ["Exportations", "Importations"], strict=True):
        running, adjusted, when = trade_series(panel)
        shown = np.abs(running) <= 40
        ax.scatter(when[shown], np.exp(adjusted[shown]), s=17, color=t["muted"],
                   alpha=0.8, zorder=2, linewidths=0)
        # One colour for both sides: they are the same quantity either side of a break,
        # not two series, and the dashed rule already says where the break is.
        for treated in (False, True):
            grid, curve, _ = _side_fit(running, adjusted, TRADE_BANDWIDTH, treated)
            ax.plot(rdit.CUTOFF + grid / 12, np.exp(curve), color=t["s1"], lw=2.4, zorder=4)
        estimate = rdit.fit(running, adjusted, TRADE_BANDWIDTH)
        # Dropping the month of the uprising itself separates a one-month shock from a
        # step to a new level; the note reports both so the reader can tell which it is.
        without = rdit.fit(running, adjusted, TRADE_BANDWIDTH, donut=1)
        jumps[panel] = (estimate.tau, without.tau)

        ax.axvline(rdit.CUTOFF, color=t["ink2"], lw=1.2, ls=(0, (5, 4)), zorder=1)
        ax.set_yscale("log")
        # A log axis picks its own decade ticks, and this window spans well under one
        # decade, so it leaves the axis unlabelled unless the ticks are set by hand.
        level = np.exp(adjusted[shown])
        ax.set_yticks(np.round(np.linspace(level.min(), level.max(), 4) / 100) * 100)
        ax.get_yaxis().set_major_formatter(mpl.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
        ax.get_yaxis().set_minor_locator(mpl.ticker.NullLocator())
        ax.set_xlim(2007.5, 2014.5)
        ax.set_xticks(range(2008, 2015, 2))
        ax.get_xaxis().set_major_formatter(mpl.ticker.FuncFormatter(lambda v, _: f"{int(v)}"))
        ax.set_title(f"{panel[:-1]}s", color=t["ink2"], loc="left", fontsize=10)
        ax.set_ylabel("million dinars, seasonally adjusted", fontsize=9)

    axes[0].annotate("January 2011", xy=(rdit.CUTOFF, 0.055), xycoords=("data", "axes fraction"),
                     xytext=(6, 0), textcoords="offset points", fontsize=9, color=t["ink2"])
    fig.text(0.075, 0.775,
             f"Jump at the cutoff: exports {100 * jumps['Exportations'][0]:+.1f}%, "
             f"imports {100 * jumps['Importations'][0]:+.1f}%   "
             f"(local linear, {TRADE_BANDWIDTH}-month bandwidth)",
             fontsize=9.5, color=t["ink2"])
    finish(fig, t,
           "At monthly frequency the design can stand right at the cutoff",
           "Monthly trade, seasonally adjusted. Fitted separately on each side of January 2011.",
           "Statistical yearbook table 14.1, editions 2007-2023, 252 months per series. "
           "Seasonal factors estimated once over the whole series from a trend that is "
           "itself allowed to jump at the cutoff, so the discontinuity cannot be absorbed "
           "into a month effect. The estimate rests entirely on January 2011 itself: "
           "dropping that one month reverses it, exports from "
           f"{100 * jumps['Exportations'][0]:+.1f}% to "
           f"{100 * jumps['Exportations'][1]:+.1f}% and imports from "
           f"{100 * jumps['Importations'][0]:+.1f}% to "
           f"{100 * jumps['Importations'][1]:+.1f}%, because the fit then has to "
           "extrapolate the treated side back across a steep recovery. That is the "
           "signature of a one-month disruption, not of a step to a new level. Figure 32 "
           "asks whether even the one-month dip is larger than this series' ordinary "
           "month-to-month movement.")
    return fig


def _placebo_sweep(running, y, bandwidth, dates):
    """The same estimate at every candidate cutoff, so the real one has a yardstick."""
    out = []
    for date in dates:
        shifted = running - (date - rdit.CUTOFF) * 12
        try:
            out.append(rdit.fit(shifted, y, bandwidth).tau)
        except ValueError:
            out.append(np.nan)
    return np.array(out)


def fig_rdit_placebo(t: dict):
    """Point the design at every other month and see how 2011 ranks."""
    fig, ax = plt.subplots(figsize=(10.0, 5.0))
    fig.subplots_adjust(top=0.72, bottom=0.22, left=0.085, right=0.98)

    candidates = np.arange(2004.5, 2021.5 + 1e-9, 1 / 12)
    shares = {}
    for panel, colour in (("Exportations", t["s1"]), ("Importations", t["s2"])):
        running, adjusted, _ = trade_series(panel)
        taus = _placebo_sweep(running, adjusted, PLACEBO_BANDWIDTH, candidates)
        ax.plot(candidates, 100 * taus, color=colour, lw=1.6,
                label=f"{panel[:-1]}s", zorder=3)
        here = float(taus[np.argmin(np.abs(candidates - rdit.CUTOFF))])
        good = np.isfinite(taus)
        shares[panel] = (here, float((np.abs(taus[good]) >= abs(here)).mean()))

    ax.axhline(0, color=t["axis"], lw=1.0, zorder=1)
    ax.axvline(rdit.CUTOFF, color=t["ink2"], lw=1.2, ls=(0, (5, 4)), zorder=2)
    # Every label was landing on the lines; each now sits in clear space with a leader
    # to the feature it names.
    arrow = {"arrowstyle": "-", "color": t["muted"], "lw": 1.0,
             "shrinkA": 2, "shrinkB": 4}
    for text, point, place in (
        ("late 2008\nfinancial crisis", (2008.85, -31), (2006.4, -41)),
        ("March 2020\nCOVID", (2020.15, -47), (2017.5, -44)),
    ):
        ax.annotate(text, xy=point, xytext=place, ha="center", va="center", fontsize=9,
                    color=t["ink2"], linespacing=1.35, arrowprops=arrow, zorder=5)
    ax.annotate("January 2011\nthe revolution", xy=(2011.0, 31), ha="center", va="bottom",
                fontsize=9, color=t["ink2"], linespacing=1.35, zorder=5)
    ax.set_ylim(-58, 46)
    ax.set_xlabel("cutoff the design was pointed at")
    ax.set_ylabel("estimated jump (%)")
    ax.set_xlim(2004.2, 2021.8)
    ax.get_xaxis().set_major_formatter(mpl.ticker.FuncFormatter(lambda v, _: f"{int(v)}"))
    ax.legend(frameon=False, loc="upper left", fontsize=9)

    finish(fig, t,
           "The same design finds 2008 and 2020 loudly, and 2011 not at all",
           "Local linear jump in monthly trade, estimated at every month from 2004 to 2021.",
           "Statistical yearbook table 14.1. Each point re-runs the January 2011 estimator "
           "with the cutoff moved to that month, 12-month bandwidth. "
           f"At the true cutoff the jump is {100 * shares['Exportations'][0]:+.1f}% for "
           f"exports and {100 * shares['Importations'][0]:+.1f}% for imports -- exceeded "
           f"in size by {100 * shares['Exportations'][1]:.0f}% and "
           f"{100 * shares['Importations'][1]:.0f}% of arbitrary cutoffs respectively. "
           "A design that could not detect a shock would find nothing anywhere; this one "
           "finds the two it should.")
    return fig


BANDWIDTH_GRID_MONTHS = np.array([6, 9, 12, 18, 24, 36, 48, 60])
BANDWIDTH_GRID_YEARS = np.array([5, 6, 7, 8, 10, 13])


def _interval_curves(running, y, grid, smoothness):
    """Conventional and honest interval half-widths across a bandwidth grid."""
    taus, conventional, honest = [], [], []
    for bandwidth in grid:
        estimate = rdit.fit(running, y, bandwidth)
        low, high, _ = rdit.honest_interval(estimate, smoothness)
        taus.append(estimate.tau)
        conventional.append(1.96 * estimate.se)
        honest.append((high - low) / 2)
    return np.array(taus), np.array(conventional), np.array(honest)


def fig_rdit_honest(t: dict):
    """What the interval looks like once it has to pay for the curvature it assumed."""
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 5.3))
    fig.subplots_adjust(top=0.68, bottom=0.28, left=0.08, right=0.985, wspace=0.26)

    running, adjusted, _ = trade_series("Exportations")
    monthly = _interval_curves(running, adjusted, BANDWIDTH_GRID_MONTHS,
                               rdit.smoothness_bound(running, adjusted))
    gap_running, gap = regional_gap()
    annual = _interval_curves(gap_running, gap, BANDWIDTH_GRID_YEARS,
                              rdit.smoothness_bound(gap_running, gap))

    panels = (
        (axes[0], BANDWIDTH_GRID_MONTHS, monthly, "Monthly: exports",
         "bandwidth (months)", "jump (log points)"),
        (axes[1], BANDWIDTH_GRID_YEARS, annual, "Annual: interior − coastal gap",
         "bandwidth (years)", "jump (pupils per teacher)"),
    )
    for ax, grid, (taus, conventional, honest), title, xlabel, ylabel in panels:
        ax.fill_between(grid, taus - honest, taus + honest, color=t["s2"], alpha=0.18,
                        zorder=2, linewidth=0, label="honest (bias-aware)")
        ax.fill_between(grid, taus - conventional, taus + conventional, color=t["s1"],
                        alpha=0.42, zorder=3, linewidth=0, label="conventional")
        ax.plot(grid, taus, color=t["ink"], lw=2.0, zorder=4)
        ax.axhline(0, color=t["axis"], lw=1.0, zorder=1)
        ax.set_title(title, color=t["ink2"], loc="left", fontsize=10)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.set_xticks(grid)
        reach = float(np.max(np.abs(taus) + honest))
        ax.set_ylim(-1.08 * reach, 1.08 * reach)
    axes[0].legend(frameon=False, loc="upper left", fontsize=9)

    widest = annual[2][-1] / annual[1][-1]
    finish(fig, t,
           "The annual estimate is precise about a number it cannot pin down",
           "Conventional and bias-aware 95% intervals, across bandwidths.",
           "The conventional interval measures noise only. The honest interval also "
           "covers the worst-case bias of fitting a straight line to a mean that curves, "
           "bounded by the curvature each series actually displays (Kolesár and Rothe "
           "2018; Armstrong and Kolesár 2018). The monthly series can shrink the "
           "bandwidth until that bias is negligible, so the two intervals nearly "
           "coincide. The annual series cannot: at its widest bandwidth the honest "
           f"interval is {widest:.0f} times the conventional one and spans zero at every "
           "bandwidth, including those where the conventional interval excludes it.")
    return fig


def fig_rdit_floor(t: dict):
    """How much calendar time each frequency must spend to buy a usable p-value."""
    from math import comb

    fig, ax = plt.subplots(figsize=(9.8, 5.3))
    fig.subplots_adjust(top=0.70, bottom=0.30, left=0.095, right=0.98)

    # A window of half-width h holds 2h+1 periods, h+1 of them after the cutoff, and
    # admits comb(2h+1, h+1) equally likely arrangements. Only the observed split
    # attains the most extreme statistic -- its complement has a different number of
    # treated periods and so is not in the enumeration -- so no outcome can push the
    # two-sided p below one arrangement's share. That floor is set by the count of
    # periods alone, and the same count costs a month of calendar time in one series
    # and a year in the other, which is the entire difference between them.
    def floor(half: int) -> float:
        return 1.0 / comb(2 * half + 1, half + 1)

    running_months, adjusted, _ = trade_series("Exportations")
    gap_running, gap = regional_gap()
    # Neither curve is drawn past the window its own series can actually fill: the
    # annual panel has only eight school years after 2011, so a wider window would be a
    # claim about data that does not exist.
    reach = {
        "monthly": min(12, int(min((running_months < 0).sum(), (running_months >= 0).sum()))),
        "annual": min(12, int(min((gap_running < 0).sum(), (gap_running >= 0).sum()))),
    }

    needed = next(h for h in range(1, 40) if floor(h) <= 0.05)
    for key, span, colour, marker, name in (
        ("monthly", 1 / 12, t["s1"], "o", "monthly (trade, table 14.1)"),
        ("annual", 1.0, t["s2"], "s", "annual (interior − coastal gap)"),
    ):
        halves = np.arange(1, reach[key] + 1)
        ax.plot(2 * halves * span, [floor(int(h)) for h in halves], color=colour, lw=2.2,
                marker=marker, markersize=6, zorder=3, label=name)

    ax.axhline(0.05, color=t["ink2"], lw=1.2, ls=(0, (2, 3)), zorder=1)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("calendar time the window spans")
    ax.set_ylabel("smallest attainable two-sided p-value")
    ax.set_xticks([1 / 6, 0.5, 1, 2, 4, 8, 16])
    ax.get_xaxis().set_major_formatter(
        mpl.ticker.FuncFormatter(lambda v, _: f"{v:g} yr" if v >= 1 else f"{v * 12:.0f} mo"))
    ax.get_xaxis().set_minor_formatter(mpl.ticker.NullFormatter())
    ax.legend(frameon=False, loc="lower left", fontsize=9)
    ax.annotate("p = 0.05", xy=(1 / 6, 0.05), xytext=(0, 7), textcoords="offset points",
                fontsize=9, color=t["ink2"])

    # What a window of that width costs on the annual series, in its own units.
    window = np.abs(gap_running) <= needed
    moved = float(np.nanmax(gap[window]) - np.nanmin(gap[window]))

    finish(fig, t,
           "Both series need the same number of periods; only one can afford them",
           "Local randomisation inference: the p-value floor a window sets before any "
           "outcome is read.",
           "Permuting which periods fall after the cutoff gives inference that is exact "
           "in finite samples, but a window admits only as many arrangements as it holds "
           "periods, and that caps how small a p-value it can return whatever the "
           f"outcomes are. Reaching 0.05 takes {needed} periods either side of the "
           f"cutoff. For the monthly series that is {needed} months around January 2011, "
           "a neighbourhood over which little else changes. For the annual series it is "
           f"{needed} years, a window across which the interior-coastal gap itself moves "
           f"by {moved:.1f} pupils per teacher -- and local randomisation assumes the "
           "running variable does not move the outcome inside the window, which is "
           "exactly what that movement denies. Neither curve is drawn beyond the window "
           "its own series can fill: the annual panel ends eight years after the cutoff.")
    return fig


BUILDERS = [
    ("01-expenditure-by-quintile", fig_quintiles, True),
    ("02-regional-gap", fig_regional_gap, True),
    ("03-urban-rural", fig_urban_rural, True),
    ("04-expenditure-vs-population-share", fig_share_gap, True),
    ("05-poverty-by-region", fig_poverty, True),
    ("06-distribution-2021", fig_distribution, False),
    ("07-within-region-spread", fig_within_region, False),
    ("08-delegation-dispersion", fig_delegations, False),
    ("09-incidence-vs-share-of-poor", fig_incidence_vs_share, True),
    ("10-deprivation-in-kind", fig_deprivation, False),
    ("11-social-protection-gap", fig_protection, False),
    ("12-literacy-gap", fig_literacy, False),
    ("13-poverty-across-the-revolution", fig_poverty_across, True),
    ("14-regional-gap-two-ways", fig_regional_gap_two_ways, True),
    ("15-urban-rural-poverty", fig_urban_rural_poverty, True),
    ("16-budget-shift-2010-2021", fig_budget_shift, True),
    ("17-prices-since-1999", fig_prices, False),
    ("18-price-against-budget", fig_price_against_budget, True),
    ("19-unemployment-by-education", fig_unemployment, False),
    ("20-out-of-pocket-health", fig_out_of_pocket, False),
    ("21-chronic-illness-and-cover", fig_chronic, False),
    ("22-why-people-left-school", fig_leaving_school, False),
    ("23-distance-to-school", fig_school_distance, False),
    ("24-why-people-are-not-working", fig_not_working, False),
    ("25-where-the-poor-work", fig_where_poor_work, False),
    ("26-where-household-money-goes", fig_where_bought, False),
    ("27-counterfactual-is-an-assumption", fig_counterfactual, False),
    ("28-placebo-break-years", fig_placebo_breaks, False),
    ("29-parallel-trends-fail", fig_parallel_trends, False),
    ("30-regional-dispersion", fig_dispersion, False),
    ("31-rdit-monthly-trade", fig_rdit_monthly, False),
    ("32-rdit-placebo-cutoffs", fig_rdit_placebo, False),
    ("33-honest-vs-conventional", fig_rdit_honest, False),
    ("34-randomisation-floor", fig_rdit_floor, False),
]


def main() -> int:
    FIGURES.mkdir(exist_ok=True)
    p = pd.read_csv(PROCESSED / "tn_consumption_panel.csv")
    for mode, theme in THEMES.items():
        style(theme)
        for name, builder, needs_panel in BUILDERS:
            fig = builder(p, theme) if needs_panel else builder(theme)
            out = FIGURES / f"{name}-{mode}.png"
            fig.savefig(out)
            plt.close(fig)
            print(f"  {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
