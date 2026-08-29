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

# ------------------------------------------------------------- INS statistical yearbooks
#
# The *Annuaire Statistique de la Tunisie*, editions 2001-2023 (2013 was never issued in
# this collection). These are general-statistics volumes rather than consumption surveys:
# they carry the annual CPI and labour-force series that the four-yearly EBCNV cannot.
#
# They are fetched from a Google Drive folder supplied by the repository owner, which
# mirrors documents INS also publishes. Drive is a mirror, not the authority -- so the
# checksum in ``data/raw/manifest.json`` matters more here than for the ins.tn sources,
# because a mirror can be edited by whoever owns it. If a checksum moves, treat the file
# as untrusted until it is re-checked against the INS release.
#
# Two things about these PDFs that any parser must respect, both verified rather than
# assumed:
#   * Table numbers shift between editions. The CPI evolution table is 13.6 in the 2023
#     edition and 13.7 in 2010. Locate tables by their French title, never by number.
#   * The CPI base year changes between editions (2015=100, 2005=100, ...), so division
#     weights are not comparable edition to edition without rebasing.

DRIVE_DOWNLOAD = "https://drive.usercontent.google.com/download"

# edition year -> Drive file id
YEARBOOK_FILE_IDS: dict[int, str] = {
    2001: "1SZJ-rQE-hjN-z-VbQTjxhJp_BdB0QN3K",
    2002: "12Zpre3GQkBTzbTuWXoEBerJqbeJEpl6z",
    2003: "1KziS2PobYx4PoUtDjoyn9fwDUgN0emNK",
    2004: "1AyE-nzhDqFcZJ2kKtgm6ueTIM3dBgcHy",
    2005: "1tOBUSnfLIKdtF3JAr6oLBcbgt3qMCsts",
    2006: "1Dcb2UnB_BJhc0Lw16EAfs88ZN3uk6dp9",
    2007: "1wm8-t3fw43vc4snMPZKhSI4svBU1Agjg",
    2008: "1HI-CSrkWLkm_rWV3-7kXcWnbHGI2MqOu",
    2009: "1CqTdgsC84jbznoWQwOcSBYt48RvTm2mg",
    2010: "1TvRNXFOAC27VkBK8XUe6Ic2QEPXb3588",
    2011: "1miEEzJlB355xcWvp_UuWPn2k9RG5d3a0",
    2012: "1EpiqpiY4TPGqCpWE1XswYPOW3-7Sm7V5",
    2014: "14Cvp4Br9vcsUjg7C-0G0zZLzz_AI-Tr1",
    2015: "1q2eXwBcOtE5bMjx9CWMp3Q0ePJ_WXAj-",
    2016: "1TY96qT7eJnwJCoEVzuTGraEI8u_xGSKp",
    2017: "1fD8qpm6W8bbQaU55RDOpL6iJ3ItUZNdP",
    2018: "1sQZP86YPUwvfQOo32kP4bB_-oStqpTFd",
    2019: "1_Y2X9caVVJYM1bDUCIUsZbwO6ejcynJo",
    2020: "1LrT9bSBYRjKVnMWK8Teq_ZJZuRK1ojhy",
    2021: "1B4By95eopwmMeo86RxMBS5ZB_1lj9QFg",
    2022: "1I9oJLCUq1bvgijiz_VAM_xmwUsouGwEI",
    2023: "1MXVyGEVCrxJNrAcPfNdYm3srvszHHrS3",
}

YEARBOOKS: tuple[Source, ...] = tuple(
    Source(
        key=f"annuaire_{year}",
        url=f"{DRIVE_DOWNLOAD}?id={file_id}&export=download&confirm=t",
        filename=f"annuaire_{year}.pdf",
        wave=None,
        kind="yearbook",
        description=(
            f"Annuaire Statistique de la Tunisie, {year} edition. Each edition carries "
            "roughly five years of annual series; the overlaps between editions are what "
            "makes a spliced series checkable."
        ),
    )
    for year, file_id in sorted(YEARBOOK_FILE_IDS.items())
)

SOURCES = SOURCES + YEARBOOKS

# Editions the price and labour builders actually read. Every edition is fetched and
# checksummed, but parsing all 22 buys nothing: each carries ~5 years, so this set spans
# 2001-2023 with deliberate overlaps used as a cross-check.
YEARBOOKS_PARSED = (2005, 2010, 2015, 2019, 2023)

SOURCES_BY_KEY = {s.key: s for s in SOURCES}


def source(key: str) -> Source:
    """Look up a source, failing loudly on a typo."""
    try:
        return SOURCES_BY_KEY[key]
    except KeyError:
        raise KeyError(f"unknown source {key!r}; known keys: {sorted(SOURCES_BY_KEY)}") from None


def raw_path(key: str) -> Path:
    return RAW_DIR / source(key).filename
