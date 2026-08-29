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
