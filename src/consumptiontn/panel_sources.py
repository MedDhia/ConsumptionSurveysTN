"""Published EBCNV figures, transcribed from the source documents with citations.

Why transcription rather than parsing. The 2021 synthesis note is born-digital French
and parses cleanly, but the pre-2015 volumes are right-to-left Arabic: ``pdftotext``
returns their columns in reversed visual order with headers split across lines, so an
automatic parser would produce numbers that look plausible and are silently mis-assigned.
Every figure below was read off the document and carries its table number, so a reader
can check any row against the PDF in the time it takes to find the page.

Two methodological breaks are recorded rather than smoothed over:

1. **Poverty methodology.** The 2005 volume reports national poverty of 3.8% (2005),
   4.2% (2000) and 6.2% (1995) on the pre-2011 methodology. The 2021 note reports 23.1%
   for the same year 2005 on the revised methodology INS adopted in 2011. These are not
   comparable and are tagged ``methodology`` = ``pre-2011`` / ``revised (2011)``.
   Never plot them on one line.
2. **Milieu definition.** Pre-2011 volumes split "communal / non-communal"; the 2021
   note says "urbain / rural" but defines rural as territory outside the communes of the
   pre-2014 administrative boundaries -- the same partition under a different name. Both
   are recorded as ``urban`` / ``rural``.
"""

from __future__ import annotations

import pandas as pd

REGIONS = [
    "Grand Tunis",
    "North East",
    "North West",
    "Centre East",
    "Centre West",
    "South East",
    "South West",
]

NOTE = "ebcnv2021_note"
VOL2005 = "ebcnv2005_vol1"

REVISED = "revised (2011)"
PRE2011 = "pre-2011"


def _rows(records: list[dict]) -> pd.DataFrame:
    return pd.DataFrame.from_records(records)


def _series(
    *,
    waves: list[int],
    values: list[float | None],
    indicator: str,
    unit: str,
    geography_level: str = "national",
    geography: str = "Tunisia",
    milieu: str | None = None,
    subgroup_type: str | None = None,
    subgroup: str | None = None,
    source_key: str,
    source_table: str,
    methodology: str | None = None,
) -> list[dict]:
    out = []
    for wave, value in zip(waves, values, strict=True):
        if value is None:
            continue
        out.append(
            {
                "wave": wave,
                "geography_level": geography_level,
                "geography": geography,
                "milieu": milieu,
                "subgroup_type": subgroup_type,
                "subgroup": subgroup,
                "indicator": indicator,
                "value": float(value),
                "unit": unit,
                "basis": "published",
                "methodology": methodology,
                "source_key": source_key,
                "source_table": source_table,
            }
        )
    return out


# --------------------------------------------------------------- EBCNV 2021 note tables

_T1 = {  # Tableau 1, p.6 -- mean expenditure by milieu, 2015 and 2021
    "urban": {"expenditure_hh_mean": [17365, 22152], "expenditure_pc_mean": [4465, 6141]},
    "rural": {"expenditure_hh_mean": [11204, 16065], "expenditure_pc_mean": [2585, 4041]},
    None: {"expenditure_hh_mean": [15561, 20328], "expenditure_pc_mean": [3871, 5468]},
}

_T2 = {  # Tableau 2, p.7 -- mean per-capita expenditure by region, 2015 and 2021
    "Grand Tunis": [5312, 6874],
    "North East": [3440, 5057],
    "North West": [2696, 4493],
    "Centre East": [4309, 6130],
    "Centre West": [2466, 3614],
    "South East": [3250, 4675],
    "South West": [3077, 4847],
}

_T3 = {  # Tableau 3, p.7 -- mean per-capita expenditure by quintile, 2015 and 2021
    "Quintile 1": [1392, 2014],
    "Quintile 2": [2228, 3258],
    "Quintile 3": [3014, 4382],
    "Quintile 4": [4176, 5921],
    "Quintile 5": [8548, 11767],
}

# Tableau 4, p.8 -- expenditure level (DT) and budget share (%) by COICOP function,
# 2010 / 2015 / 2021. Keys are the function codes used throughout the project.
_T4 = {
    1: ([763, 1118, 1645], [29.3, 28.9, 30.1]),
    2: ([73, 102, 183], [2.8, 2.6, 3.3]),
    3: ([224, 293, 635], [8.6, 7.6, 11.6]),
    4: ([635, 1030, 1307], [24.4, 26.6, 23.9]),
    5: ([117, 143, 191], [4.5, 3.7, 3.5]),
    6: ([228, 363, 609], [8.8, 9.4, 11.1]),
    7: ([233, 360, 375], [9.0, 9.3, 6.9]),
    8: ([141, 171, 224], [5.4, 4.4, 4.1]),
    9: ([36, 44, 46], [1.4, 1.1, 0.8]),
    10: ([54, 84, 81], [2.1, 2.2, 1.5]),
    11: ([84, 157, 164], [3.2, 4.0, 3.0]),
    12: ([12, 6, 8], [0.5, 0.2, 0.1]),
}

_T5 = {  # Tableau 5, p.9 -- poverty lines, DT per person per year
    "urban": {"poverty_line": [949, 1275, 1801, 2683], "extreme_poverty_line": [567, 761, 1070, 1529]},
    "rural": {"poverty_line": [798, 1070, 1501, 2224], "extreme_poverty_line": [506, 679, 952, 1347]},
    None: {"poverty_line": [897, 1206, 1706, 2536], "extreme_poverty_line": [546, 733, 1032, 1471]},
}

_T6 = {  # Tableau 6, p.10 -- poverty rates by milieu (%)
    "urban": {"poverty_rate": [14.8, 12.6, 10.1, 12.7], "extreme_poverty_rate": [3.0, 2.1, 1.2, 1.7]},
    "rural": {"poverty_rate": [38.8, 36.0, 26.0, 24.8], "extreme_poverty_rate": [15.5, 13.6, 6.6, 5.3]},
    None: {"poverty_rate": [23.1, 20.5, 15.2, 16.6], "extreme_poverty_rate": [7.4, 6.0, 2.9, 2.9]},
}

_T7 = {  # Tableau 7, p.11 -- poverty rates by region (%), 2005 / 2010 / 2015 / 2021
    "Grand Tunis": ([12.3, 11.1, 5.3, 4.7], [1.8, 1.2, 0.3, 0.2]),
    "North East": ([21.8, 15.2, 11.6, 15.2], [4.9, 3.3, 1.6, 2.4]),
    "North West": ([29.6, 36.2, 28.4, 22.5], [8.5, 12.5, 6.4, 4.6]),
    "Centre East": ([12.5, 11.6, 11.5, 13.2], [2.7, 2.3, 1.9, 2.1]),
    "Centre West": ([49.7, 42.3, 30.8, 37.0], [25.0, 17.4, 8.4, 7.2]),
    "South East": ([24.5, 20.7, 18.6, 23.2], [6.9, 6.2, 3.0, 4.3]),
    "South West": ([32.3, 25.9, 17.6, 18.1], [10.8, 7.7, 2.6, 3.4]),
}

# Tableau 8, p.11 and Tableau 9, p.12 -- 2021 poverty incidence and contribution by
# head-of-household education and socio-professional category.
# (incidence %, population share %, absolute contribution %, relative contribution %)
_T8 = {
    "none": (23.5, 17.0, 4.0, 24.1),
    "primary": (20.3, 41.7, 8.5, 51.0),
    "secondary": (11.7, 29.4, 3.4, 20.8),
    "higher": (5.1, 10.7, 0.5, 3.3),
}

_T9 = {
    "senior managers and professionals": (6.2, 8.4, 0.5, 3.2),
    "mid-level managers and professionals": (7.8, 2.9, 0.2, 1.4),
    "other employees": (14.3, 14.0, 2.0, 12.1),
    "employers in industry, trade and services": (5.1, 1.6, 0.1, 0.5),
    "own-account workers and artisans in industry, trade and services": (11.3, 4.1, 0.5, 2.8),
    "non-agricultural workers": (24.4, 22.2, 5.4, 32.7),
    "farm operators": (22.8, 6.6, 1.5, 9.1),
    "agricultural workers": (31.9, 2.4, 0.8, 4.7),
    "unemployed": (41.3, 2.8, 1.2, 7.0),
    "retired": (5.4, 19.1, 1.0, 6.2),
    "other inactive": (21.6, 15.7, 3.4, 20.5),
}

# Tableau 10, p.13 -- Gini index, population share and share of total expenditure,
# 2015 and 2021.
_T10 = {
    "Grand Tunis": ([35.6, 30.4], [24.5, 24.4], [33.7, 30.7]),
    "North East": ([31.2, 31.5], [13.5, 14.1], [12.0, 13.0]),
    "North West": ([32.8, 34.7], [10.2, 10.1], [7.1, 8.3]),
    "Centre East": ([35.1, 36.8], [24.1, 24.0], [26.8, 26.8]),
    "Centre West": ([32.0, 34.4], [12.5, 12.9], [8.0, 8.6]),
    "South East": ([32.0, 32.7], [9.4, 9.1], [7.9, 7.8]),
    "South West": ([29.6, 32.7], [5.8, 5.5], [4.6, 4.8]),
    "Tunisia": ([36.5, 35.3], [100.0, 100.0], [100.0, 100.0]),
}

# ------------------------------------------------- EBCNV 2005 volume 1 (Arabic) tables

_V2005_T2 = {  # Jadwal 2, p.17 -- per-capita expenditure by milieu, 1990-2005
    "urban": [890, 1209, 1604, 2171],
    "rural": [460, 581, 864, 1161],
    None: [716, 966, 1329, 1820],
}

_V2005_T3 = {  # Jadwal 3, p.18 -- per-capita expenditure by region, 1990-2005
    "Grand Tunis": [1007, 1289, 1761, 2390],
    "North East": [760, 958, 1190, 1613],
    "North West": [501, 677, 1103, 1416],
    "Centre West": [502, 586, 909, 1138],
    "Centre East": [806, 1275, 1594, 2084],
    "South East": [600, 739, 1097, 1826],
    "South West": [521, 711, 1017, 1466],
}

# Jadwal 4, p.18 -- 2005 only: per-capita expenditure by region x milieu, and the
# household-level figure. (urban, rural, national, household)
_V2005_T4 = {
    "Grand Tunis": (2475, 1386, 2390, 9982),
    "North East": (1884, 1189, 1613, 6979),
    "North West": (1841, 1162, 1416, 6149),
    "Centre West": (1652, 890, 1138, 5667),
    "Centre East": (2344, 1411, 2084, 9485),
    "South East": (1989, 1424, 1826, 9323),
    "South West": (1702, 965, 1466, 7035),
    "Tunisia": (2171, 1161, 1820, 8211),
}

# Jadwal 8, p.20 -- expenditure structure (%), 1990-2005, on the nine-post nomenclature
# INS used before the 2010 move to COICOP. Not directly comparable to Tableau 4 above.
_V2005_T8 = {
    "Food": [40.0, 37.7, 38.0, 34.8],
    "Housing": [22.0, 22.2, 21.5, 22.8],
    "Clothing": [10.2, 11.8, 11.1, 8.8],
    "Hygiene and care": [8.7, 9.6, 10.0, 10.3],
    "Transport": [7.7, 7.8, 8.6, 10.7],
    "Communication": [0.5, 0.9, 1.1, 3.7],
    "Education": [2.3, 2.7, 2.9, 2.8],
    "Culture and leisure": [6.2, 6.2, 5.8, 5.6],
    "Other": [2.4, 1.1, 1.0, 0.5],
}


def published_rows() -> pd.DataFrame:
    """Every transcribed figure, as tidy panel rows."""
    rows: list[dict] = []
    w2 = [2015, 2021]
    w4 = [2005, 2010, 2015, 2021]
    w_old = [1990, 1995, 2000, 2005]

    # -- 2021 synthesis note ------------------------------------------------------
    for milieu, indicators in _T1.items():
        for indicator, values in indicators.items():
            rows += _series(
                waves=w2, values=values, indicator=indicator, unit="DT per year",
                milieu=milieu, source_key=NOTE, source_table="Tableau 1",
            )
    for region, values in _T2.items():
        rows += _series(
            waves=w2, values=values, indicator="expenditure_pc_mean", unit="DT per year",
            geography_level="region", geography=region, source_key=NOTE, source_table="Tableau 2",
        )
    for quintile, values in _T3.items():
        rows += _series(
            waves=w2, values=values, indicator="expenditure_pc_mean", unit="DT per year",
            subgroup_type="expenditure quintile", subgroup=quintile,
            source_key=NOTE, source_table="Tableau 3",
        )
    for code, (level, share) in _T4.items():
        rows += _series(
            waves=[2010, 2015, 2021], values=level, indicator="expenditure_pc_by_function",
            unit="DT per year", subgroup_type="COICOP function", subgroup=str(code),
            source_key=NOTE, source_table="Tableau 4",
        )
        rows += _series(
            waves=[2010, 2015, 2021], values=share, indicator="budget_share",
            unit="percent", subgroup_type="COICOP function", subgroup=str(code),
            source_key=NOTE, source_table="Tableau 4",
        )
    for milieu, indicators in _T5.items():
        for indicator, values in indicators.items():
            rows += _series(
                waves=w4, values=values, indicator=indicator, unit="DT per person per year",
                milieu=milieu, methodology=REVISED, source_key=NOTE, source_table="Tableau 5",
            )
    for milieu, indicators in _T6.items():
        for indicator, values in indicators.items():
            rows += _series(
                waves=w4, values=values, indicator=indicator, unit="percent",
                milieu=milieu, methodology=REVISED, source_key=NOTE, source_table="Tableau 6",
            )
    for region, (poverty, extreme) in _T7.items():
        for indicator, values in [("poverty_rate", poverty), ("extreme_poverty_rate", extreme)]:
            rows += _series(
                waves=w4, values=values, indicator=indicator, unit="percent",
                geography_level="region", geography=region, methodology=REVISED,
                source_key=NOTE, source_table="Tableau 7",
            )
    for table, subgroup_type, mapping in [
        ("Tableau 8", "head education", _T8),
        ("Tableau 9", "head socio-professional category", _T9),
    ]:
        for subgroup, (incidence, pop_share, abs_contrib, rel_contrib) in mapping.items():
            for indicator, value in [
                ("poverty_rate", incidence),
                ("population_share", pop_share),
                ("poverty_contribution_absolute", abs_contrib),
                ("poverty_contribution_relative", rel_contrib),
            ]:
                rows += _series(
                    waves=[2021], values=[value], indicator=indicator, unit="percent",
                    subgroup_type=subgroup_type, subgroup=subgroup, methodology=REVISED,
                    source_key=NOTE, source_table=table,
                )
    for region, (gini, pop_share, exp_share) in _T10.items():
        level = "national" if region == "Tunisia" else "region"
        for indicator, values, unit in [
            ("gini", gini, "index (0-100)"),
            ("population_share", pop_share, "percent"),
            ("expenditure_share", exp_share, "percent"),
        ]:
            rows += _series(
                waves=w2, values=values, indicator=indicator, unit=unit,
                geography_level=level, geography=region, methodology=REVISED,
                source_key=NOTE, source_table="Tableau 10",
            )
    # Narrative figure, p.10: 2019 poverty estimated from the 2018-19 follow-up panel by
    # imputing expenditure, not from an EBCNV wave. Kept, flagged, and dated 2019.
    rows += _series(
        waves=[2019], values=[13.8], indicator="poverty_rate", unit="percent",
        methodology=f"{REVISED}, modelled from 2018-19 follow-up panel",
        source_key=NOTE, source_table="text, p.10",
    )

    # -- 2005 volume 1 ------------------------------------------------------------
    for milieu, values in _V2005_T2.items():
        rows += _series(
            waves=w_old, values=values, indicator="expenditure_pc_mean", unit="DT per year",
            milieu=milieu, source_key=VOL2005, source_table="Jadwal 2",
        )
    for region, values in _V2005_T3.items():
        rows += _series(
            waves=w_old, values=values, indicator="expenditure_pc_mean", unit="DT per year",
            geography_level="region", geography=region, source_key=VOL2005, source_table="Jadwal 3",
        )
    for region, (urban, rural, national, household) in _V2005_T4.items():
        level = "national" if region == "Tunisia" else "region"
        # Jadwal 4 restates the region and national totals that Jadwal 2 and Jadwal 3
        # already give (identically). Only its two contributions are taken: the
        # region x milieu split, and the household-level figure.
        if region != "Tunisia":
            for milieu, value in [("urban", urban), ("rural", rural)]:
                rows += _series(
                    waves=[2005], values=[value], indicator="expenditure_pc_mean",
                    unit="DT per year", geography_level=level, geography=region,
                    milieu=milieu, source_key=VOL2005, source_table="Jadwal 4",
                )
        rows += _series(
            waves=[2005], values=[household], indicator="expenditure_hh_mean", unit="DT per year",
            geography_level=level, geography=region, source_key=VOL2005, source_table="Jadwal 4",
        )
    for post, values in _V2005_T8.items():
        rows += _series(
            waves=w_old, values=values, indicator="budget_share", unit="percent",
            subgroup_type="pre-2010 expenditure post", subgroup=post,
            source_key=VOL2005, source_table="Jadwal 8",
        )
    # Chart, p.17: the only pre-1990 national figure published in these documents.
    rows += _series(
        waves=[1985], values=[471], indicator="expenditure_pc_mean", unit="DT per year",
        source_key=VOL2005, source_table="chart, p.17",
    )
    # Poverty on the pre-2011 methodology -- deliberately not comparable to Tableau 6.
    rows += _series(
        waves=[1995, 2000, 2005], values=[6.2, 4.2, 3.8], indicator="poverty_rate",
        unit="percent", methodology=PRE2011, source_key=VOL2005, source_table="text, p.24",
    )
    return _rows(rows)


# Waves INS has conducted, and what this project could find published online for each.
WAVE_COVERAGE = pd.DataFrame(
    [
        (1968, "none", "Wave conducted; no volume or series published on ins.tn."),
        (1975, "none", "Wave conducted; no volume or series published on ins.tn."),
        (1980, "none", "Wave conducted; no volume or series published on ins.tn."),
        (1985, "partial", "National mean per-capita expenditure only, from a chart in the 2005 volume."),
        (1990, "aggregate", "Per-capita expenditure by milieu and region, and budget shares, from the 2005 volume."),
        (1995, "aggregate", "As 1990, plus pre-2011-methodology poverty rate."),
        (2000, "aggregate", "As 1995."),
        (2005, "aggregate", "2005 volume tables plus the revised-methodology series in the 2021 note."),
        (2010, "aggregate", "Budget structure and poverty series in the 2021 note; volumes 1-3 as PDF."),
        (2015, "aggregate", "Expenditure, poverty and Gini series in the 2021 note; volumes 1-3 as PDF."),
        (2019, "modelled", "Poverty rate only, imputed from the 2018-19 follow-up panel."),
        (2021, "microdata", "Seven Stata files plus aggregate annexes and volumes A and C."),
    ],
    columns=["wave", "availability", "note"],
)
