"""Registry of every INS artefact the pipeline consumes.

INS reorganises ins.tn periodically -- note the ``files-ftp3`` path segment, which
replaced an earlier scheme. Keeping every URL in one place (with a checksum recorded
in ``data/raw/manifest.json``) means a site move is a one-file fix, and means a reader
can always tell which published document a number came from.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
INTERIM_DIR = PROJECT_ROOT / "data" / "interim"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CODEBOOK_DIR = PROJECT_ROOT / "docs" / "codebooks"
MANIFEST_PATH = RAW_DIR / "manifest.json"

INS_BASE = "https://www.ins.tn/sites/default/files-ftp3/files"

# EBCNV waves. Only 2021 has open microdata; see docs/SOURCES.md for the rest.
WAVES = (1968, 1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2021)
MICRODATA_WAVES = (2021,)


@dataclass(frozen=True)
class Source:
    """One downloadable INS artefact."""

    key: str
    url: str
    filename: str
    wave: int | None
    kind: str  # microdata | annex | report | reference
    description: str
    members: tuple[str, ...] = field(default=())  # files inside an archive


SOURCES: tuple[Source, ...] = (
    # ------------------------------------------------------------------ 2021 microdata
    Source(
        key="ebcnv2021_depenses",
        url=f"{INS_BASE}/2023-06/FichiersD%C3%A9penses.rar",
        filename="FichiersDepenses.rar",
        wave=2021,
        kind="microdata",
        description=(
            "EBCNV 2021 expenditure microdata: household poverty/expenditure file, "
            "individual roster, product-level expenditure lines, product dictionary."
        ),
        members=(
            "FichiersDépenses/FichiersDépenses/pov_2021.dta",
            "FichiersDépenses/FichiersDépenses/donnindiv2021.dta",
            "FichiersDépenses/FichiersDépenses/produit2021_plus.dta",
            "FichiersDépenses/FichiersDépenses/code_produit.dta",
        ),
    ),
    Source(
        key="ebcnv2021_educsante",
        url=f"{INS_BASE}/2023-11/EducationSante.rar",
        filename="EducationSante.rar",
        wave=2021,
        kind="microdata",
        description="EBCNV 2021 individual-level education and health modules.",
        members=("EducationSante/Education2021.dta", "EducationSante/Sante2021.dta"),
    ),
    Source(
        key="ebcnv2021_condvie",
        url=f"{INS_BASE}/2023-05/microdonnees_condvie.rar",
        filename="microdonnees_condvie.rar",
        wave=2021,
        kind="microdata",
        description="EBCNV 2021 living-conditions module (housing, amenities, durables).",
        members=("microdonnees_condvie.dta",),
    ),
    # -------------------------------------------------------------- 2021 aggregate annexes
    Source(
        key="ebcnv2021_annexe1",
        url=f"{INS_BASE}/2023-05/Annexe1_2021_DistributitonPopulationTranchesD%C3%A9penses.xlsx",
        filename="Annexe1_2021_distribution_population_tranches_depenses.xlsx",
        wave=2021,
        kind="annex",
        description="Population distribution across expenditure brackets; expenditure structure.",
    ),
    Source(
        key="ebcnv2021_annexe2",
        url=f"{INS_BASE}/2023-05/Annexe2_2021_NiveauD%C3%A9pense%20selon%20le%20produit.xlsx",
        filename="Annexe2_2021_niveau_depense_selon_produit.xlsx",
        wave=2021,
        kind="annex",
        description="Expenditure level by product group and region.",
    ),
    Source(
        key="ebcnv2021_annexe3",
        url=f"{INS_BASE}/2023-05/Annexe3_2021_D%C3%A9pense%20annuelle%20moyenne%20par%20personne%20selon%20le%20produit.xlsx",
        filename="Annexe3_2021_depense_annuelle_moyenne_par_personne.xlsx",
        wave=2021,
        kind="annex",
        description=(
            "Mean annual per-capita expenditure by product, cut by milieu, region, CSP, "
            "household size, expenditure bracket and decile, plus a 5-digit product sheet."
        ),
    ),
    Source(
        key="ebcnv2021_services",
        url=f"{INS_BASE}/2023-05/ENBCNV2021_Acc%C3%A8s%20aux%20services%20collectifs.xlsx",
        filename="ENBCNV2021_acces_services_collectifs.xlsx",
        wave=2021,
        kind="annex",
        description="47 Arabic-labelled tables on education, health and social coverage.",
    ),
    # ------------------------------------------------------------------- reports, by wave
    Source(
        key="ebcnv2021_note",
        url=f"{INS_BASE}/publication/pdf/EBCNV2021_Note_synth%C3%A8se.pdf",
        filename="EBCNV2021_note_synthese.pdf",
        wave=2021,
        kind="report",
        description="Synthesis note. Source of the headline figures the test suite reproduces.",
    ),
    Source(
        key="ebcnv2021_vol_a",
        url=f"{INS_BASE}/publication/pdf/Volume%20A_EBCNV_2021.pdf",
        filename="EBCNV2021_volume_A.pdf",
        wave=2021,
        kind="report",
        description="Volume A: household expenditure in level and structure.",
    ),
    Source(
        key="ebcnv2021_vol_c",
        url=f"{INS_BASE}/publication/pdf/Volume%20C_EBCNV_2021.pdf",
        filename="EBCNV2021_volume_C.pdf",
        wave=2021,
        kind="report",
        description="Volume C: access to public services and living conditions.",
    ),
    Source(
        key="ebcnv2021_donnees",
        url=f"{INS_BASE}/publication/pdf/Donn%C3%A9es.xlsx",
        filename="EBCNV2021_donnees.xlsx",
        wave=2021,
        kind="annex",
        description="Headline tables accompanying the results release (structure, poverty, Gini).",
    ),
    Source(
        key="ebcnv2015_vol1",
        url=f"{INS_BASE}/publication/pdf/vol1-budget-2015.pdf",
        filename="EBCNV2015_volume_1_budget.pdf",
        wave=2015,
        kind="report",
        description="EBCNV 2015 Volume 1: household budget.",
    ),
    Source(
        key="ebcnv2015_vol2",
        url=f"{INS_BASE}/publication/pdf/consommation-2015%20V2.pdf",
        filename="EBCNV2015_volume_2.pdf",
        wave=2015,
        kind="report",
        description="EBCNV 2015 Volume 2: consumption.",
    ),
    Source(
        key="ebcnv2015_vol3",
        url=f"{INS_BASE}/publication/pdf/consommation-2015%20V3.pdf",
        filename="EBCNV2015_volume_3.pdf",
        wave=2015,
        kind="report",
        description="EBCNV 2015 Volume 3: living conditions.",
    ),
    Source(
        key="ebcnv2010_vol1",
        url=f"{INS_BASE}/publication/pdf/consommation_2010%20V1.pdf",
        filename="EBCNV2010_volume_1.pdf",
        wave=2010,
        kind="report",
        description="EBCNV 2010 Volume 1: household budget.",
    ),
    Source(
        key="ebcnv2010_vol2",
        url=f"{INS_BASE}/publication/pdf/consommation-2010%20V2.pdf",
        filename="EBCNV2010_volume_2.pdf",
        wave=2010,
        kind="report",
        description="EBCNV 2010 Volume 2: consumption.",
    ),
    Source(
        key="ebcnv2010_vol3",
        url=f"{INS_BASE}/publication/pdf/consommation_2010%20V3.pdf",
        filename="EBCNV2010_volume_3.pdf",
        wave=2010,
        kind="report",
        description="EBCNV 2010 Volume 3: living conditions.",
    ),
    Source(
        key="ebcnv2005_vol1",
        url=f"{INS_BASE}/publication/pdf/consommation-2005%20V1.pdf",
        filename="EBCNV2005_volume_1.pdf",
        wave=2005,
        kind="report",
        description="EBCNV 2005 Volume 1: household budget.",
    ),
    Source(
        key="ebcnv2005_vol2",
        url=f"{INS_BASE}/publication/pdf/consomation_2005%20V2.pdf",
        filename="EBCNV2005_volume_2.pdf",
        wave=2005,
        kind="report",
        description="EBCNV 2005 Volume 2: consumption.",
    ),
    # ---------------------------------------------------------------- reference documents
    Source(
        key="carte_pauvrete_2020",
        url=f"{INS_BASE}/publication/pdf/Carte%20de%20la%20pauvret%C3%A9%20en%20Tunisie_final_0.pdf",
        filename="carte_pauvrete_tunisie_2020.pdf",
        wave=None,
        kind="reference",
        description=(
            "Poverty map (Sept 2020). Small-area *modelled* estimates below the region "
            "tier -- delegation-level figures here are not survey estimates."
        ),
    ),
    Source(
        key="mesure_pauvrete_2000_2010",
        url=f"{INS_BASE}/publication/pdf/Mesure_de_la_pauvrete.pdf",
        filename="mesure_pauvrete_inegalites_2000_2010.pdf",
        wave=None,
        kind="reference",
        description=(
            "Poverty, inequality and polarisation in Tunisia, 2000-2010. Retrospective series."
        ),
    ),
)

SOURCES_BY_KEY = {s.key: s for s in SOURCES}


def source(key: str) -> Source:
    """Look up a source, failing loudly on a typo."""
    try:
        return SOURCES_BY_KEY[key]
    except KeyError:
        raise KeyError(f"unknown source {key!r}; known keys: {sorted(SOURCES_BY_KEY)}") from None


def raw_path(key: str) -> Path:
    return RAW_DIR / source(key).filename
