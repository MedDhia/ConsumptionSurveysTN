# Individuals: demographics, education, health — EBCNV 2021

`data/processed/tn_hbs_2021_individuals.csv` — 65,524 rows × 53 columns

One row per household member (65,524), combining the roster with the education and health modules.

**Coverage differs by module.** The roster and education module cover all 65,524 individuals; the health module covers 54,041, because its questions were not put to the youngest children. Health columns are missing outside that scope — a fact about the survey, not a defect in the extraction.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `hh_id` | int64 | — | `pov_2021.dta` → `identif_menage` | «identifiant menage» |
| `person_id` | int64 | — | `donnindiv2021.dta` → `v050` | «Num ordre individu» |
| `survey_year` | int64 | — | derived | EBCNV wave, added by the pipeline. Always 2021 in the microdata files. |
| `region` | categorical | — | `pov_2021.dta` → `region` | «region» |
| `milieu` | categorical | — | `pov_2021.dta` → `milieu` | «milieu» |
| `weight` | float64 | — | derived | Household extrapolation factor (`v700`), applied to each member of the household. |
| `hh_size` | Int64 | — | `pov_2021.dta` → `hh_size` | «taille du menage» |
| `poor` | categorical | — | `pov_2021.dta` → `pauv` | «pauvre» |
| `extreme_poor` | categorical | — | `pov_2021.dta` → `pauv_extreme` | «pauv_extreme» |
| `relation_to_head` | categorical | — | `donnindiv2021.dta` → `v052` | «lien parente chef menage» |
| `sex` | categorical | — | `donnindiv2021.dta` → `sexe` | «Sexe» |
| `age_group` | categorical | — | `donnindiv2021.dta` → `groupe_age` | «Groupe age» |
| `education_level` | categorical | — | `donnindiv2021.dta` → `niveau_instr` | «niveau instruction» |
| `csp` | categorical | — | `donnindiv2021.dta` → `csp` | «categorie socioprofessionnelle» |
| `age` | Int64 | years | `Education2021.dta` → `age` | «Age Individu» |
| `currently_enrolled` | categorical | — | `Education2021.dta` → `v061` | «frequent scolaire/format» |
| `education_cycle` | categorical | — | `Education2021.dta` → `v062` | «cycle scola/format» |
| `institution_type` | categorical | — | `Education2021.dta` → `v064` | «type etablissement» |
| `school_distance` | categorical | — | `Education2021.dta` → `v065` | «distance domicile etablissement» |
| `transport_mode` | categorical | — | `Education2021.dta` → `v066` | «moyen transport utilisée» |
| `travel_time_to_school_min` | object | minutes | `Education2021.dta` → `v067` | «durée domicile etablissement» |
| `scholarship` | categorical | — | `Education2021.dta` → `v069` | «alloc ou bourse universitaire» |
| `scholarship_amount` | object | dinars per year | `Education2021.dta` → `v070` | «montant annuel alloc ou bourse» |
| `literate` | categorical | — | `Education2021.dta` → `v071` | «lire/ecrire une langue» |
| `education_level_detailed` | categorical | — | `Education2021.dta` → `v073` | «niveau d'instruction» |
| `diploma` | categorical | — | `Education2021.dta` → `v075` | «diplome obtenu» |
| `reason_left_school` | categorical | — | `Education2021.dta` → `v078` | «raison quitter etabli scolaire» |
| `reason_never_studied` | categorical | — | `Education2021.dta` → `v080` | «raison non etudier» |
| `uses_computer` | categorical | — | `Education2021.dta` → `v082` | «utilisation ordinateur» |
| `uses_internet` | categorical | — | `Education2021.dta` → `v083` | «utilisation internet» |
| `worked_last_week` | categorical | — | `Education2021.dta` → `v084` | «travail semaine dernier» |
| `reason_not_working` | categorical | — | `Education2021.dta` → `v086` | «raison non travail» |
| `job_search_method` | categorical | — | `Education2021.dta` → `v087` | «recherche active travail mois preced» |
| `job_search_duration_months` | object | months | `Education2021.dta` → `v089` | «duree recherche travail en mois» |
| `employment_status` | categorical | — | `Education2021.dta` → `v092` | «situation dans la profession» |
| `workplace` | categorical | — | `Education2021.dta` → `v093` | «lieu de travail» |
| `social_insurance` | categorical | — | `Sante2021.dta` → `v600` | «affiliation caisses sociales» |
| `insurance_scheme` | categorical | — | `Sante2021.dta` → `v601` | «Forme d'assurance» |
| `care_card` | categorical | — | `Sante2021.dta` → `v604` | «carte soin» |
| `covered_via_other_member` | categorical | — | `Sante2021.dta` → `v605` | «couvert avec autre membre» |
| `has_chronic_disease` | categorical | — | `Sante2021.dta` → `v607` | «maladie chronique 1» |
| `chronic_disease_expenditure` | object | dinars per year | `Sante2021.dta` → `v613` | «depenses maladie chronique» |
| `n_apci_conditions` | object | — | `Sante2021.dta` → `v614` | «Nombre APCI» |
| `has_functional_difficulty` | categorical | — | `Sante2021.dta` → `v615` | «difficulte physique/mentale» |
| `difficulty_type` | categorical | — | `Sante2021.dta` → `v616_1` | «type 1ere difficulte» |
| `difficulty_degree` | categorical | — | `Sante2021.dta` → `v617_1` | «degre 1ere difficulte» |
| `illness_in_reference_year` | categorical | — | `Sante2021.dta` → `v647` | «maladie annee refer» |
| `consultation_expenditure` | object | dinars per year | `Sante2021.dta` → `v656` | «ddépenses consultation/analyses/radio» |
| `medicine_expenditure` | object | dinars per year | `Sante2021.dta` → `v657` | «dépenses médicaments» |
| `hospital_night_in_reference_year` | categorical | — | `Sante2021.dta` → `v658` | «passer nuit hopital annee refer» |
| `n_hospital_nights` | object | — | `Sante2021.dta` → `v660` | «nb nuitees centre hospitalier» |
| `hospital_stay_expenditure` | object | dinars per year | `Sante2021.dta` → `v661` | «dépenses nuitees passees centre hospitalier» |
| `insurance_reimbursement` | float64 | dinars per year | `Sante2021.dta` → `v666` | «montant remboursé assurance» |

## Categorical codes

Every code INS shipped, its original French label, and the English used in the exported file. Codes 9 and 99 mean *non déclaré* throughout the EBCNV questionnaire and are exported as missing.

### `region`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | Grand Tunis | Grand Tunis |
| 2 | Nord Est | North East |
| 3 | Nord Ouest | North West |
| 4 | Centre Est | Centre East |
| 5 | Centre Ouest | Centre West |
| 6 | Sud Est | South East |
| 7 | Sud ouest | South West |

### `milieu`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | urbain | urban |
| 2 | rural | rural |

### `poor`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 0 | No pauv | not poor |
| 1 | pauv | poor |

### `extreme_poor`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 0 | No pauv_extreme | not extremely poor |
| 1 | pauv_extreme | extremely poor |

### `relation_to_head`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | chef menage | head |
| 2 | conjoint | spouse |
| 3 | fils/fille | child |
| 4 | petit fils/fille | grandchild |
| 5 | gendre/belle fille | child-in-law |
| 6 | beau/lle pere/mere | parent-in-law |
| 7 | autre parent | other relative |
| 8 | non parent | not related |
| 9 | non déclaré | — (mapped to missing) |

### `sex`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | Masculin | male |
| 2 | Féminin | female |
| 9 | Non déclaré | — (mapped to missing) |

### `age_group`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | 0-4 ans | 0-4 |
| 2 | 5-14 ans | 5-14 |
| 3 | 15-59 ans | 15-59 |
| 4 | 60 ans et plus | 60+ |

### `education_level`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | neant | none |
| 2 | niveau primaire | primary |
| 3 | niveau secondaire | secondary |
| 4 | niveau superieur | higher |

### `csp`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | cadres et professions liberales superieurs | senior managers and professionals |
| 2 | cadres et professions liberales moyens | mid-level managers and professionals |
| 3 | autres employes | other employees |
| 4 |  patrons des petits metiers dans l'industrie, commerce et services | employers in industry, trade and services |
| 5 |  artisans et independants des petits metiers dans l'industrie, commerce et services | own-account workers and artisans in industry, trade and services |
| 6 |  ouvriers non agricoles | non-agricultural workers |
| 7 |  exploitants agricoles | farm operators |
| 8 |  ouvriers agricloes | agricultural workers |
| 9 |  chomeurs | unemployed |
| 10 |  retraites | retired |
| 11 |  autres inactifs | other inactive |

### `currently_enrolled`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `education_cycle`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | jardin d'enfants | kindergarten |
| 2 | kotteb | kouttab (Quranic school) |
| 3 | preparatoire | preparatory |
| 4 | premier cycle enseignement de base | basic education, first cycle |
| 5 | deuxième cycle enseignement de base | basic education, second cycle |
| 6 | secondaire | secondary |
| 7 | superieur | higher |
| 8 | formation profession | vocational training |
| 9 | CAP | CAP (vocational aptitude certificate) |
| 10 | BTP | BTP (vocational technician certificate) |
| 11 | BTS | BTS (higher technician certificate) |
| 12 | apprentis profession | apprenticeship |
| 13 | autre format prof | other vocational training |
| 14 | insert prof | labour-market insertion |
| 15 | recyclage | retraining |
| 16 | alphabetis | literacy programme |
| 99 | non déclaré | — (mapped to missing) |

### `institution_type`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | etab scolaire public | public school |
| 2 | etab scolaire privé | private school |
| 3 | etab formation prof public | public vocational training centre |
| 4 | etab formation prof privé | private vocational training centre |
| 9 | non déclaré | — (mapped to missing) |

### `school_distance`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | moins de 2 km | under 2 km |
| 2 | entre 2 et 4 km | 2-4 km |
| 3 | plus que 4 km | over 4 km |
| 9 | non déclaré | — (mapped to missing) |

### `transport_mode`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | A pieds | on foot |
| 2 | bicyclette/moto | bicycle or motorcycle |
| 3 | train/métro | train or metro |
| 4 | bus transport urbain | urban bus |
| 5 | bus transport entre ville | intercity bus |
| 6 | taxi/transport rural | taxi or rural transport |
| 7 | voiture privé/conducteur | private car, driver |
| 8 | voiture privé/passager | private car, passenger |
| 9 | autre moyen | other |
| 10 | sans déplacement | no travel |
| 99 | non déclaré | — (mapped to missing) |

### `scholarship`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui bourse | yes, scholarship |
| 2 | oui allocation | yes, allowance |
| 3 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `literate`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `education_level_detailed`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | kotteb | kouttab (Quranic school) |
| 2 | primaire ancien | primary (old system) |
| 3 | secondaire ancien | secondary (old system) |
| 4 | professionnel | vocational |
| 5 | premier cycle enseignement de base | basic education, first cycle |
| 6 | deuxième cycle enseignement de base | basic education, second cycle |
| 7 | secondaire nouveau | secondary (new system) |
| 8 | superieur | higher |
| 9 | alphabetis | literacy programme |
| 10 | Neant | none |
| 99 | non déclaré | — (mapped to missing) |

### `diploma`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 0 | Neant | none |
| 1 | diplome avant bac | pre-baccalaureate diploma |
| 2 | baccalaureat ou equiv | baccalaureate or equivalent |
| 3 | technicien sup ou equiv | higher technician or equivalent |
| 4 | lettre ou sciences humaines | bachelor's, humanities |
| 5 | economie, gestion, droit | bachelor's, economics, management or law |
| 6 | sciences exactes | bachelor's, natural sciences |
| 7 | autre maitrise | bachelor's, other |
| 8 | diplome d'ingenieur | engineering degree |
| 9 | medecin ou pharmacien | medical or pharmacy degree |
| 10 | mastere ou equiv | master's or equivalent |
| 11 | doctorat | doctorate |
| 12 | CAP | CAP (vocational aptitude certificate) |
| 13 | BTP | BTP (vocational technician certificate) |
| 14 | BTS | BTS (higher technician certificate) |
| 15 | autre diplom format | other training diploma |
| 16 | diplom d'alphabetis | literacy certificate |
| 99 | non déclaré | — (mapped to missing) |

### `reason_left_school`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | fin etude | completed studies |
| 2 | préfère travail | preferred to work |
| 3 | exclu | expelled |
| 4 | école loin | school too far |
| 5 | fournitures scolaires chères | school supplies too expensive |
| 6 | ne vois aucun intérêt d'étudier | saw no point in studying |
| 7 | autre raison | other |
| 9 | non déclaré | — (mapped to missing) |

### `reason_never_studied`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | Jeune âge | too young |
| 2 | école est loin | school too far |
| 3 | Je dois rester à la maison | had to stay at home |
| 4 | Raisons de santé | health reasons |
| 5 | Fournitures scolaires chères | school supplies too expensive |
| 6 | Je ne vois aucun avantage à étudier | saw no benefit in studying |
| 7 | autre | other |
| 9 | non déclaré | — (mapped to missing) |

### `uses_computer`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `uses_internet`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `worked_last_week`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `reason_not_working`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | conge maladie repos | sick or on leave |
| 2 | condts climatiques | weather conditions |
| 3 | arret momentane travail | temporary work stoppage |
| 4 | service militaire | military service |
| 5 | preparat demarrage ou promesse | about to start a job |
| 6 | manque travail | no work available |
| 7 | ne veux pas travailler | does not want to work |
| 8 | travaux menagers | housework |
| 9 | eleve ou etudiant | pupil or student |
| 10 | retraite | retired |
| 11 | incapable de travailler | unable to work |
| 12 | gere ses rentes | managing own assets |
| 13 | rentier | living on unearned income |
| 14 | autre raison | other |
| 15 | prisonnier | imprisoned |
| 99 | non déclaré | — (mapped to missing) |

### `job_search_method`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 0 | non déclaré | — (mapped to missing) |
| 1 | je n'ai pas cherche | did not search |
| 2 | inscript bureau emploi | registered with employment office |
| 3 | particip concours recrut | sat a recruitment competition |
| 4 | envoi demandes emploi | sent job applications |
| 5 | inscript autorites locales | registered with local authorities |
| 6 | demande autorist administratives | applied for administrative authorisation |
| 7 | consult programmes gouvernement | consulted government programmes |
| 8 | points de recrutement | went to hiring points |
| 9 | autre demarche | other |

### `employment_status`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | propre compte avec salaries | self-employed with employees |
| 2 | propre compte sans salaries | self-employed without employees |
| 3 | salarie | employee |
| 4 | apprenti | apprentice |
| 5 | aide familial sans salaire | unpaid family worker |
| 6 | autre | other |
| 9 | non déclaré | — (mapped to missing) |

### `workplace`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | administrat publique | public administration |
| 2 | entreprise publique | public enterprise |
| 3 | entreprise tunisienne privee | private Tunisian enterprise |
| 4 | entreprise etrang/mixte privee | foreign or joint-venture enterprise |
| 5 | local prive | private premises |
| 6 | logement | own home |
| 7 | ambulant | itinerant |
| 8 | exploitat agricole | farm |
| 9 | chantier de batiment | building site |
| 10 | autre chantier | other site |
| 11 | autre lieu | other |
| 99 | non déclaré | — (mapped to missing) |

### `social_insurance`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui CNRPS | CNRPS (public sector fund) |
| 2 | oui CNSS | CNSS (private sector fund) |
| 3 | autre | other |
| 4 | non affilié | not affiliated |
| 9 | non déclaré | — (mapped to missing) |

### `insurance_scheme`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | Forme public | public provider scheme |
| 2 | Forme privé | private provider scheme |
| 3 | Récupération frais | reimbursement of costs |
| 9 | non déclaré | — (mapped to missing) |

### `care_card`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | carte soin gratuit | free care card |
| 2 | carte soin tarif reduit | reduced-tariff care card |
| 3 | autre carte | other card |
| 4 | non | none |
| 9 | non déclaré | — (mapped to missing) |

### `covered_via_other_member`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `has_chronic_disease`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `has_functional_difficulty`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `difficulty_type`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | vision | seeing |
| 2 | audition | hearing |
| 3 | marche | walking |
| 4 | concentration | concentrating |
| 5 | prise en charge de soi | self-care |
| 6 | communication | communicating |

### `difficulty_degree`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | qq difficultes | some difficulty |
| 2 | grandes difficultes | a lot of difficulty |
| 3 | handicap total | cannot do at all |
| 9 | non déclaré | — (mapped to missing) |

### `illness_in_reference_year`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `hospital_night_in_reference_year`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |
