# Dwelling, amenities and durables — EBCNV 2021

`data/processed/tn_hbs_2021_dwelling.csv` — 17,394 rows × 46 columns

One row per household: dwelling type and materials, tenure, water, sanitation, energy, distance to public services, and ownership of 15 durable goods.

Despite sitting with the individual education and health modules on the INS download page, `microdonnees_condvie.dta` is household-level.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `hh_id` | int64 | — | `pov_2021.dta` → `identif_menage` | «identifiant menage» |
| `survey_year` | int64 | — | derived | EBCNV wave, added by the pipeline. Always 2021 in the microdata files. |
| `region` | categorical | — | `pov_2021.dta` → `region` | «region» |
| `milieu` | categorical | — | `pov_2021.dta` → `milieu` | «milieu» |
| `weight_hh` | float64 | — | `pov_2021.dta` → `v700` | «extrapolation menage» |
| `weight_pop` | float64 | — | `pov_2021.dta` → `v701` | «extrapolation individu» |
| `hh_size` | Int64 | — | `pov_2021.dta` → `hh_size` | «taille du menage» |
| `poor` | categorical | — | `pov_2021.dta` → `pauv` | «pauvre» |
| `building_type` | categorical | — | `microdonnees_condvie.dta` → `v200` | «type construction» |
| `dwelling_type` | categorical | — | `microdonnees_condvie.dta` → `v201` | «type logement principal» |
| `wall_material` | categorical | — | `microdonnees_condvie.dta` → `v202` | «materiau construction mur» |
| `roof_material` | categorical | — | `microdonnees_condvie.dta` → `v203` | «materiau construction toit» |
| `floor_material` | categorical | — | `microdonnees_condvie.dta` → `v204` | «materiau construction sol» |
| `n_rooms` | object | — | `microdonnees_condvie.dta` → `v205` | «nb pieces logement» |
| `tenure` | categorical | — | `microdonnees_condvie.dta` → `v206` | «mode occupation logement» |
| `lighting_source` | categorical | — | `microdonnees_condvie.dta` → `v207` | «mode eclairage» |
| `has_natural_gas` | categorical | — | `microdonnees_condvie.dta` → `v208` | «gaz naturel (steg)» |
| `heating_energy` | categorical | — | `microdonnees_condvie.dta` → `v209` | «energie chauffage» |
| `water_source` | categorical | — | `microdonnees_condvie.dta` → `v210` | «source eau potable» |
| `distance_to_water_point_m` | object | metres | `microdonnees_condvie.dta` → `v211` | «distance domicile point d'eau» |
| `travel_time_to_water_point_min` | object | minutes | `microdonnees_condvie.dta` → `v212` | «duree trajet domicile point d'eau» |
| `bathroom_type` | categorical | — | `microdonnees_condvie.dta` → `v213` | «type salle de bain» |
| `water_heating_energy` | categorical | — | `microdonnees_condvie.dta` → `v214` | «energie eau chaude» |
| `toilet_type` | categorical | — | `microdonnees_condvie.dta` → `v215` | «type toilettes» |
| `connected_to_sewerage` | categorical | — | `microdonnees_condvie.dta` → `v216` | «raccordement reseau assainissement» |
| `kitchen_type` | categorical | — | `microdonnees_condvie.dta` → `v217` | «type cuisine» |
| `cooking_energy` | categorical | — | `microdonnees_condvie.dta` → `v218` | «energie cuisson» |
| `distance_to_primary_school` | object | — | `microdonnees_condvie.dta` → `v219` | «distance domicile ecole primaire» |
| `distance_to_middle_school` | object | — | `microdonnees_condvie.dta` → `v220` | «college» |
| `distance_to_high_school` | object | — | `microdonnees_condvie.dta` → `v221` | «lycee» |
| `distance_to_health_centre` | object | — | `microdonnees_condvie.dta` → `v222` | «centre de sante» |
| `distance_to_local_hospital` | object | — | `microdonnees_condvie.dta` → `v223` | «hopital local» |
| `keeps_livestock` | categorical | — | `microdonnees_condvie.dta` → `v228` | «elevage pour autoconsommation» |
| `has_radio` | categorical | — | `microdonnees_condvie.dta` → `v245` | «radio» |
| `has_television` | categorical | — | `microdonnees_condvie.dta` → `v249` | «televiseur normal» |
| `has_smart_television` | categorical | — | `microdonnees_condvie.dta` → `v251` | «televiseur smart» |
| `has_satellite_dish` | categorical | — | `microdonnees_condvie.dta` → `v259` | «antenne parabolique» |
| `has_computer` | categorical | — | `microdonnees_condvie.dta` → `v261` | «ordinateur» |
| `has_refrigerator` | categorical | — | `microdonnees_condvie.dta` → `v263` | «refrigerateur» |
| `has_freezer` | categorical | — | `microdonnees_condvie.dta` → `v265` | «congelateur» |
| `has_washing_machine` | categorical | — | `microdonnees_condvie.dta` → `v267` | «lave-linge» |
| `has_dishwasher` | categorical | — | `microdonnees_condvie.dta` → `v269` | «lave-vaisselle» |
| `has_microwave` | categorical | — | `microdonnees_condvie.dta` → `v275` | «micro-ondes» |
| `has_air_conditioning` | categorical | — | `microdonnees_condvie.dta` → `v281` | «climatiseur» |
| `has_heating` | categorical | — | `microdonnees_condvie.dta` → `v283` | «chauffage» |
| `has_vacuum_cleaner` | categorical | — | `microdonnees_condvie.dta` → `v291` | «aspirateur» |

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

### `building_type`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | immeuble | apartment block |
| 2 | habitation collective | collective dwelling |
| 3 | logement individuel | individual dwelling |
| 4 | non destinee habitation | not built as housing |
| 9 | non déclaré | — (mapped to missing) |

### `dwelling_type`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | dar arbi | dar arbi (traditional courtyard house) |
| 2 | logement jumele | semi-detached house |
| 3 | etage jumele | semi-detached upper floor |
| 4 | villa | villa |
| 5 | etage villa superieur | villa upper floor |
| 6 | RDC villa | villa ground floor |
| 7 | appartement | apartment |
| 8 | studio | studio |
| 9 | oukala | oukala (subdivided tenement) |
| 10 | houch, borj | houch or borj (rural compound) |
| 11 | gorbi maamra kib | gourbi (makeshift dwelling) |
| 12 | non destine habitation | not built as housing |
| 99 | non déclaré | — (mapped to missing) |

### `wall_material`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | pierre brique | stone or brick |
| 2 | autre materiau | other material |
| 9 | non déclaré | — (mapped to missing) |

### `roof_material`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | dalle, beton | concrete slab |
| 2 | bois, tuile, voute | wood, tile or vault |
| 3 | autre materiau | other material |
| 9 | non déclaré | — (mapped to missing) |

### `floor_material`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | plancher parterre ciment moquette | tiled, cement or carpeted |
| 2 | Terre, Sable | earth or sand |
| 9 | non déclaré | — (mapped to missing) |

### `tenure`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | proprietaire | owner |
| 2 | locataire | tenant |
| 3 | gratuitement | free of charge |
| 9 | non déclaré | — (mapped to missing) |

### `lighting_source`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | STEG avec facture | STEG grid, billed |
| 2 | STEG sans facture | STEG grid, not billed |
| 3 | STEG avec loyer | STEG grid, included in rent |
| 4 | energie solaire | solar |
| 5 | generateur electrique | generator |
| 6 | lampe a petrole | oil lamp |
| 7 | autre moyen | other |
| 9 | non déclaré | — (mapped to missing) |

### `has_natural_gas`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `heating_energy`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | gaz naturel (STEG) | natural gas (STEG) |
| 2 | gaz bouteille | bottled gas |
| 3 | petrole bleu | kerosene |
| 4 | gazoil | diesel |
| 5 | electricite | electricity |
| 6 | energie solaire | solar |
| 7 | charbon | charcoal |
| 8 | bois | wood |
| 9 | animaux | animal dung |
| 10 | pas de chauffage | none |
| 99 | non déclaré | — (mapped to missing) |

### `water_source`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | SONEDE avec facture | SONEDE mains, billed |
| 2 | SONEDE sans facture | SONEDE mains, not billed |
| 3 | citerne privee | private cistern |
| 4 | puits prive | private well |
| 5 | citerne publique | public cistern |
| 6 | puits public non equipe moteur | public well, unmotorised |
| 7 | fontaine publique liee SONEDE | public standpipe on SONEDE mains |
| 8 | fontaine ONG | NGO-provided standpipe |
| 9 | source non controlee | uncontrolled spring |
| 10 | cours d'eau | watercourse |
| 99 | non déclaré | — (mapped to missing) |

### `bathroom_type`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | salle de bain avec eau chaude | bathroom with hot water |
| 2 | douche avec eau chaude | shower with hot water |
| 3 | salle de bain sans eau chaude | bathroom without hot water |
| 4 | ne possede pas de SDB | none |
| 9 | non déclaré | — (mapped to missing) |

### `water_heating_energy`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | gaz naturel (STEG) | natural gas (STEG) |
| 2 | gaz bouteille | bottled gas |
| 3 | petrole bleu | kerosene |
| 4 | gazoil | diesel |
| 5 | electricite | electricity |
| 6 | energie solaire | solar |
| 7 | charbon | charcoal |
| 8 | bois | wood |
| 9 | animaux | animal dung |
| 10 | pas de chauffage | none |
| 99 | non déclaré | — (mapped to missing) |

### `toilet_type`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | toilettes avec chasse d'eau | flush toilet |
| 2 | toilettes sans chasse d'eau | toilet without flush |
| 3 | toilettes a l'exterieur | outdoor toilet |
| 4 | toilettes communes | shared toilet |
| 9 | non déclaré | — (mapped to missing) |

### `connected_to_sewerage`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `kitchen_type`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | cuisine avec evier | kitchen with sink |
| 2 | cuisine sans evier | kitchen without sink |
| 3 | pas de cuisine | no kitchen |
| 9 | non déclaré | — (mapped to missing) |

### `cooking_energy`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | gaz naturel (STEG) | natural gas (STEG) |
| 2 | gaz bouteille | bottled gas |
| 3 | petrole bleu | kerosene |
| 4 | gazoil | diesel |
| 5 | electricite | electricity |
| 6 | energie solaire | solar |
| 7 | charbon | charcoal |
| 8 | bois | wood |
| 9 | animaux | animal dung |
| 10 | pas de chauffage | none |
| 99 | non déclaré | — (mapped to missing) |

### `keeps_livestock`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `has_radio`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `has_television`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `has_smart_television`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `has_satellite_dish`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `has_computer`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `has_refrigerator`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `has_freezer`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `has_washing_machine`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `has_dishwasher`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `has_microwave`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `has_air_conditioning`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `has_heating`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |

### `has_vacuum_cleaner`

| Code | French (INS) | English (exported) |
| --- | --- | --- |
| 1 | oui | yes |
| 2 | non | no |
| 9 | non déclaré | — (mapped to missing) |
