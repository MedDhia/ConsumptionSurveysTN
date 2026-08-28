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
    fig.text(0.012, 0.018, source, ha="left", va="bottom", fontsize=8, color=t["muted"])


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


# ------------------------------------------------------------------ the six figures

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


BUILDERS = [
    ("01-expenditure-by-quintile", fig_quintiles, True),
    ("02-regional-gap", fig_regional_gap, True),
    ("03-urban-rural", fig_urban_rural, True),
    ("04-expenditure-vs-population-share", fig_share_gap, True),
    ("05-poverty-by-region", fig_poverty, True),
    ("06-distribution-2021", fig_distribution, False),
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
