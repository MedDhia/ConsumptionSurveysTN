# Sources

Every INS artefact this pipeline reads, with the URL it was fetched from, its SHA-256,
and when it was retrieved. `data/raw/manifest.json` is the machine-readable version and
is what `make verify` checks against.

INS reorganises ins.tn periodically — note the `files-ftp3` path segment, which replaced
an earlier scheme. If a URL 404s, the fix belongs in `src/consumptiontn/config.py`, and
the checksum here says whether the replacement file is the same document.

## What INS publishes, and what that allows

**Microdata: 2021 only.** The EBCNV 2021 page carries seven Stata files across three RAR
archives. No earlier wave has microdata on ins.tn. ERF (erfdataportal.com) hosts
harmonised 2005 and 2010 microdata, but behind registration, so it is out of scope for
an open pipeline.

**Aggregate tables: 2005 onward.** Volumes A–C per wave as PDF, plus four Excel annexes
for 2021. The 2021 synthesis note carries retrospective series back to 2005, and the
2005 volume carries them back to 1990 (and a single 1985 figure).

**Nothing at all for 1968, 1975 and 1980.** Those waves were conducted; no volume or
series from them is published online. See `data/processed/tn_wave_coverage.csv`.

## A note on what is committed

Raw downloads (`data/raw`) are not committed — they are 86 MB and re-fetchable, and the
manifest pins exactly which bytes the results came from. Derived microdata files are not
committed either; `make build` rebuilds them in about three minutes. The small reference
datasets — the indicator panel, the product nomenclature, the delegation poverty
estimates, the wave coverage table — are committed as CSV, and the medium files as
Parquet.

## Artefacts


### Microdata archives

| Key | Wave | File | Size | SHA-256 (first 16) | Retrieved |
| --- | --- | --- | --- | --- | --- |
| `ebcnv2021_depenses` | 2021 | [FichiersDepenses.rar](https://www.ins.tn/sites/default/files-ftp3/files/2023-06/FichiersD%C3%A9penses.rar) | 19.0 MB | `c414e158d98d2677` | 2026-08-28 |
| | | EBCNV 2021 expenditure microdata: household poverty/expenditure file, individual roster, product-level expenditure lines, product dictionary. | | | |
| `ebcnv2021_educsante` | 2021 | [EducationSante.rar](https://www.ins.tn/sites/default/files-ftp3/files/2023-11/EducationSante.rar) | 1.7 MB | `cb1bd63062603038` | 2026-08-28 |
| | | EBCNV 2021 individual-level education and health modules. | | | |
| `ebcnv2021_condvie` | 2021 | [microdonnees_condvie.rar](https://www.ins.tn/sites/default/files-ftp3/files/2023-05/microdonnees_condvie.rar) | 0.2 MB | `11ab976b91144848` | 2026-08-28 |
| | | EBCNV 2021 living-conditions module (housing, amenities, durables). | | | |

`FichiersDepenses.rar` contains: `pov_2021.dta`, `donnindiv2021.dta`, `produit2021_plus.dta`, `code_produit.dta`

`EducationSante.rar` contains: `Education2021.dta`, `Sante2021.dta`

`microdonnees_condvie.rar` contains: `microdonnees_condvie.dta`

### Aggregate tables

| Key | Wave | File | Size | SHA-256 (first 16) | Retrieved |
| --- | --- | --- | --- | --- | --- |
| `ebcnv2021_annexe1` | 2021 | [Annexe1_2021_distribution_population_tranches_depenses.xlsx](https://www.ins.tn/sites/default/files-ftp3/files/2023-05/Annexe1_2021_DistributitonPopulationTranchesD%C3%A9penses.xlsx) | 0.1 MB | `020ef6e466bf9a9f` | 2026-08-28 |
| | | Population distribution across expenditure brackets; expenditure structure. | | | |
| `ebcnv2021_annexe2` | 2021 | [Annexe2_2021_niveau_depense_selon_produit.xlsx](https://www.ins.tn/sites/default/files-ftp3/files/2023-05/Annexe2_2021_NiveauD%C3%A9pense%20selon%20le%20produit.xlsx) | 0.1 MB | `8b73901ca07921d7` | 2026-08-28 |
| | | Expenditure level by product group and region. | | | |
| `ebcnv2021_annexe3` | 2021 | [Annexe3_2021_depense_annuelle_moyenne_par_personne.xlsx](https://www.ins.tn/sites/default/files-ftp3/files/2023-05/Annexe3_2021_D%C3%A9pense%20annuelle%20moyenne%20par%20personne%20selon%20le%20produit.xlsx) | 1.0 MB | `cdd279c73999595c` | 2026-08-28 |
| | | Mean annual per-capita expenditure by product, cut by milieu, region, CSP, household size, expenditure bracket and decile, plus a 5-digit product sheet. | | | |
| `ebcnv2021_services` | 2021 | [ENBCNV2021_acces_services_collectifs.xlsx](https://www.ins.tn/sites/default/files-ftp3/files/2023-05/ENBCNV2021_Acc%C3%A8s%20aux%20services%20collectifs.xlsx) | 0.1 MB | `6e94d4bf6123056b` | 2026-08-28 |
| | | 47 Arabic-labelled tables on education, health and social coverage. | | | |
| `ebcnv2021_donnees` | 2021 | [EBCNV2021_donnees.xlsx](https://www.ins.tn/sites/default/files-ftp3/files/publication/pdf/Donn%C3%A9es.xlsx) | 0.5 MB | `43e4afb10f85767f` | 2026-08-28 |
| | | Headline tables accompanying the results release (structure, poverty, Gini). | | | |

### Survey volumes and releases

| Key | Wave | File | Size | SHA-256 (first 16) | Retrieved |
| --- | --- | --- | --- | --- | --- |
| `ebcnv2021_note` | 2021 | [EBCNV2021_note_synthese.pdf](https://www.ins.tn/sites/default/files-ftp3/files/publication/pdf/EBCNV2021_Note_synth%C3%A8se.pdf) | 0.5 MB | `176d467c1803bae7` | 2026-08-28 |
| | | Synthesis note. Source of the headline figures the test suite reproduces. | | | |
| `ebcnv2021_vol_a` | 2021 | [EBCNV2021_volume_A.pdf](https://www.ins.tn/sites/default/files-ftp3/files/publication/pdf/Volume%20A_EBCNV_2021.pdf) | 18.3 MB | `a6ae11389b5c07a7` | 2026-08-28 |
| | | Volume A: household expenditure in level and structure. | | | |
| `ebcnv2021_vol_c` | 2021 | [EBCNV2021_volume_C.pdf](https://www.ins.tn/sites/default/files-ftp3/files/publication/pdf/Volume%20C_EBCNV_2021.pdf) | 5.2 MB | `918fde4d5cd77273` | 2026-08-28 |
| | | Volume C: access to public services and living conditions. | | | |
| `ebcnv2015_vol1` | 2015 | [EBCNV2015_volume_1_budget.pdf](https://www.ins.tn/sites/default/files-ftp3/files/publication/pdf/vol1-budget-2015.pdf) | 2.4 MB | `7b8a8d6ce267a08a` | 2026-08-28 |
| | | EBCNV 2015 Volume 1: household budget. | | | |
| `ebcnv2015_vol2` | 2015 | [EBCNV2015_volume_2.pdf](https://www.ins.tn/sites/default/files-ftp3/files/publication/pdf/consommation-2015%20V2.pdf) | 2.8 MB | `a11614ec7f517997` | 2026-08-28 |
| | | EBCNV 2015 Volume 2: consumption. | | | |
| `ebcnv2015_vol3` | 2015 | [EBCNV2015_volume_3.pdf](https://www.ins.tn/sites/default/files-ftp3/files/publication/pdf/consommation-2015%20V3.pdf) | 3.1 MB | `b75e36851860234b` | 2026-08-28 |
| | | EBCNV 2015 Volume 3: living conditions. | | | |
| `ebcnv2010_vol1` | 2010 | [EBCNV2010_volume_1.pdf](https://www.ins.tn/sites/default/files-ftp3/files/publication/pdf/consommation_2010%20V1.pdf) | 6.3 MB | `0c0f5720576054c3` | 2026-08-28 |
| | | EBCNV 2010 Volume 1: household budget. | | | |
| `ebcnv2010_vol2` | 2010 | [EBCNV2010_volume_2.pdf](https://www.ins.tn/sites/default/files-ftp3/files/publication/pdf/consommation-2010%20V2.pdf) | 1.1 MB | `44f56cb47c558805` | 2026-08-28 |
| | | EBCNV 2010 Volume 2: consumption. | | | |
| `ebcnv2010_vol3` | 2010 | [EBCNV2010_volume_3.pdf](https://www.ins.tn/sites/default/files-ftp3/files/publication/pdf/consommation_2010%20V3.pdf) | 4.7 MB | `fc30747ec6f5c224` | 2026-08-28 |
| | | EBCNV 2010 Volume 3: living conditions. | | | |
| `ebcnv2005_vol1` | 2005 | [EBCNV2005_volume_1.pdf](https://www.ins.tn/sites/default/files-ftp3/files/publication/pdf/consommation-2005%20V1.pdf) | 10.6 MB | `1cbb64e1491b38a3` | 2026-08-28 |
| | | EBCNV 2005 Volume 1: household budget. | | | |
| `ebcnv2005_vol2` | 2005 | [EBCNV2005_volume_2.pdf](https://www.ins.tn/sites/default/files-ftp3/files/publication/pdf/consomation_2005%20V2.pdf) | 1.8 MB | `cb6b2e928daa194e` | 2026-08-28 |
| | | EBCNV 2005 Volume 2: consumption. | | | |

### Reference documents

| Key | Wave | File | Size | SHA-256 (first 16) | Retrieved |
| --- | --- | --- | --- | --- | --- |
| `carte_pauvrete_2020` | — | [carte_pauvrete_tunisie_2020.pdf](https://www.ins.tn/sites/default/files-ftp3/files/publication/pdf/Carte%20de%20la%20pauvret%C3%A9%20en%20Tunisie_final_0.pdf) | 9.4 MB | `069fb50f03dad674` | 2026-08-28 |
| | | Poverty map (Sept 2020). Small-area *modelled* estimates below the region tier -- delegation-level figures here are not survey estimates. | | | |
| `mesure_pauvrete_2000_2010` | — | [mesure_pauvrete_inegalites_2000_2010.pdf](https://www.ins.tn/sites/default/files-ftp3/files/publication/pdf/Mesure_de_la_pauvrete.pdf) | 0.9 MB | `e79f08785f95dd57` | 2026-08-28 |
| | | Poverty, inequality and polarisation in Tunisia, 2000-2010. Retrospective series. | | | |
