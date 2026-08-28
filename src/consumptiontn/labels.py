"""French/Arabic -> English translation layer.

Rule for the whole project: **English is what gets exported, the original French or
Arabic string is preserved in the codebook.** Nothing is translated at runtime by
guesswork -- every mapping below is written out explicitly against the value labels
INS actually shipped in the .dta files, so a reader can audit the translation.

Two dictionaries do the work:

``RENAMES``   original INS variable name -> exported English column name
``VALUE_SETS``  a named code -> English mapping, reused across variables that share it
``COLUMN_VALUE_SET``  exported column -> which entry of ``VALUE_SETS`` decodes it

``MISSING_CODE`` (9, or 99 where the set runs past 9) means "not declared" throughout
the EBCNV questionnaire and is mapped to ``NA`` rather than to a category.
"""

from __future__ import annotations

import pandas as pd

NOT_DECLARED = "non déclaré"

# --------------------------------------------------------------------------- value sets

VALUE_SETS: dict[str, dict[float, str]] = {
    "region": {
        1: "Grand Tunis",
        2: "North East",
        3: "North West",
        4: "Centre East",
        5: "Centre West",
        6: "South East",
        7: "South West",
    },
    "milieu": {1: "urban", 2: "rural"},
    "yes_no": {1: "yes", 2: "no"},
    "poor_flag": {0: "not poor", 1: "poor"},
    "extreme_poor_flag": {0: "not extremely poor", 1: "extremely poor"},
    "sex": {1: "male", 2: "female"},
    # The head-of-household sex variable splits female by pregnancy/breastfeeding status.
    "sex_head": {
        1: "male",
        2: "female",
        3: "female, pregnant",
        4: "female, breastfeeding",
    },
    "marital_status": {1: "single", 2: "married", 3: "widowed", 4: "divorced"},
    "education_level": {
        1: "none",
        2: "primary",
        3: "secondary",
        4: "higher",
    },
    "education_level_detailed": {
        1: "kouttab (Quranic school)",
        2: "primary (old system)",
        3: "secondary (old system)",
        4: "vocational",
        5: "basic education, first cycle",
        6: "basic education, second cycle",
        7: "secondary (new system)",
        8: "higher",
        9: "literacy programme",
        10: "none",
    },
    "csp": {
        1: "senior managers and professionals",
        2: "mid-level managers and professionals",
        3: "other employees",
        4: "employers in industry, trade and services",
        5: "own-account workers and artisans in industry, trade and services",
        6: "non-agricultural workers",
        7: "farm operators",
        8: "agricultural workers",
        9: "unemployed",
        10: "retired",
        11: "other inactive",
    },
    "relation_to_head": {
        1: "head",
        2: "spouse",
        3: "child",
        4: "grandchild",
        5: "child-in-law",
        6: "parent-in-law",
        7: "other relative",
        8: "not related",
    },
    "age_group": {1: "0-4", 2: "5-14", 3: "15-59", 4: "60+"},
    "household_size_class": {
        1: "1-2 persons",
        2: "3-4 persons",
        3: "5-6 persons",
        4: "7-8 persons",
        5: "9 or more persons",
    },
    # INS bracket labels; note the published set jumps from 4,500 to "above 5,000" --
    # that gap is in the source, not a transcription error.
    "expenditure_bracket": {
        1: "under 500 DT",
        2: "500-750 DT",
        3: "750-1,000 DT",
        4: "1,000-1,500 DT",
        5: "1,500-2,000 DT",
        6: "2,000-3,000 DT",
        7: "3,000-4,500 DT",
        8: "above 5,000 DT",
    },
    # ---------------------------------------------------------------- expenditure module
    "purchase_place": {
        1: "private shop",
        2: "supermarket",
        3: "permanent market",
        4: "weekly market",
        5: "fair or exhibition",
        6: "online",
        7: "other",
    },
    "production_origin": {1: "Tunisia", 2: "imported", 3: "does not know"},
    "acquisition_mode": {
        1: "purchase, cash",
        2: "purchase, credit",
        3: "own production",
        4: "gift",
        5: "other",
    },
    "covid_affected": {1: "normal", 2: "affected by COVID-19"},
    # ------------------------------------------------------------ living-conditions module
    "building_type": {
        1: "apartment block",
        2: "collective dwelling",
        3: "individual dwelling",
        4: "not built as housing",
    },
    "dwelling_type": {
        1: "dar arbi (traditional courtyard house)",
        2: "semi-detached house",
        3: "semi-detached upper floor",
        4: "villa",
        5: "villa upper floor",
        6: "villa ground floor",
        7: "apartment",
        8: "studio",
        9: "oukala (subdivided tenement)",
        10: "houch or borj (rural compound)",
        11: "gourbi (makeshift dwelling)",
        12: "not built as housing",
    },
    "wall_material": {1: "stone or brick", 2: "other material"},
    "roof_material": {1: "concrete slab", 2: "wood, tile or vault", 3: "other material"},
    "floor_material": {1: "tiled, cement or carpeted", 2: "earth or sand"},
    "tenure": {1: "owner", 2: "tenant", 3: "free of charge"},
    "lighting_source": {
        1: "STEG grid, billed",
        2: "STEG grid, not billed",
        3: "STEG grid, included in rent",
        4: "solar",
        5: "generator",
        6: "oil lamp",
        7: "other",
    },
    # v209 / v214 / v218 share one label set: heating, water heating and cooking energy.
    "energy_source": {
        1: "natural gas (STEG)",
        2: "bottled gas",
        3: "kerosene",
        4: "diesel",
        5: "electricity",
        6: "solar",
        7: "charcoal",
        8: "wood",
        9: "animal dung",
        10: "none",
    },
    "water_source": {
        1: "SONEDE mains, billed",
        2: "SONEDE mains, not billed",
        3: "private cistern",
        4: "private well",
        5: "public cistern",
        6: "public well, unmotorised",
        7: "public standpipe on SONEDE mains",
        8: "NGO-provided standpipe",
        9: "uncontrolled spring",
        10: "watercourse",
    },
    "bathroom_type": {
        1: "bathroom with hot water",
        2: "shower with hot water",
        3: "bathroom without hot water",
        4: "none",
    },
    "toilet_type": {
        1: "flush toilet",
        2: "toilet without flush",
        3: "outdoor toilet",
        4: "shared toilet",
    },
    "kitchen_type": {1: "kitchen with sink", 2: "kitchen without sink", 3: "no kitchen"},
    # ------------------------------------------------------------------ education module
    "education_cycle": {
        1: "kindergarten",
        2: "kouttab (Quranic school)",
        3: "preparatory",
        4: "basic education, first cycle",
        5: "basic education, second cycle",
        6: "secondary",
        7: "higher",
        8: "vocational training",
        9: "CAP (vocational aptitude certificate)",
        10: "BTP (vocational technician certificate)",
        11: "BTS (higher technician certificate)",
        12: "apprenticeship",
        13: "other vocational training",
        14: "labour-market insertion",
        15: "retraining",
        16: "literacy programme",
    },
    "institution_type": {
        1: "public school",
        2: "private school",
        3: "public vocational training centre",
        4: "private vocational training centre",
    },
    "school_distance": {1: "under 2 km", 2: "2-4 km", 3: "over 4 km"},
    "transport_mode": {
        1: "on foot",
        2: "bicycle or motorcycle",
        3: "train or metro",
        4: "urban bus",
        5: "intercity bus",
        6: "taxi or rural transport",
        7: "private car, driver",
        8: "private car, passenger",
        9: "other",
        10: "no travel",
    },
    "scholarship": {1: "yes, scholarship", 2: "yes, allowance", 3: "no"},
    "diploma": {
        0: "none",
        1: "pre-baccalaureate diploma",
        2: "baccalaureate or equivalent",
        3: "higher technician or equivalent",
        4: "bachelor's, humanities",
        5: "bachelor's, economics, management or law",
        6: "bachelor's, natural sciences",
        7: "bachelor's, other",
        8: "engineering degree",
        9: "medical or pharmacy degree",
        10: "master's or equivalent",
        11: "doctorate",
        12: "CAP (vocational aptitude certificate)",
        13: "BTP (vocational technician certificate)",
        14: "BTS (higher technician certificate)",
        15: "other training diploma",
        16: "literacy certificate",
    },
    "reason_left_school": {
        1: "completed studies",
        2: "preferred to work",
        3: "expelled",
        4: "school too far",
        5: "school supplies too expensive",
        6: "saw no point in studying",
        7: "other",
    },
    "reason_never_studied": {
        1: "too young",
        2: "school too far",
        3: "had to stay at home",
        4: "health reasons",
        5: "school supplies too expensive",
        6: "saw no benefit in studying",
        7: "other",
    },
    "reason_not_working": {
        1: "sick or on leave",
        2: "weather conditions",
        3: "temporary work stoppage",
        4: "military service",
        5: "about to start a job",
        6: "no work available",
        7: "does not want to work",
        8: "housework",
        9: "pupil or student",
        10: "retired",
        11: "unable to work",
        12: "managing own assets",
        13: "living on unearned income",
        14: "other",
        15: "imprisoned",
    },
    "job_search_method": {
        1: "did not search",
        2: "registered with employment office",
        3: "sat a recruitment competition",
        4: "sent job applications",
        5: "registered with local authorities",
        6: "applied for administrative authorisation",
        7: "consulted government programmes",
        8: "went to hiring points",
        9: "other",
    },
    "employment_status": {
        1: "self-employed with employees",
        2: "self-employed without employees",
        3: "employee",
        4: "apprentice",
        5: "unpaid family worker",
        6: "other",
    },
    "workplace": {
        1: "public administration",
        2: "public enterprise",
        3: "private Tunisian enterprise",
        4: "foreign or joint-venture enterprise",
        5: "private premises",
        6: "own home",
        7: "itinerant",
        8: "farm",
        9: "building site",
        10: "other site",
        11: "other",
    },
    # --------------------------------------------------------------------- health module
    "social_insurance": {
        1: "CNRPS (public sector fund)",
        2: "CNSS (private sector fund)",
        3: "other",
        4: "not affiliated",
    },
    "insurance_scheme": {
        1: "public provider scheme",
        2: "private provider scheme",
        3: "reimbursement of costs",
    },
    "care_card": {
        1: "free care card",
        2: "reduced-tariff care card",
        3: "other card",
        4: "none",
    },
    "difficulty_type": {
        1: "seeing",
        2: "hearing",
        3: "walking",
        4: "concentrating",
        5: "self-care",
        6: "communicating",
    },
    "difficulty_degree": {
        1: "some difficulty",
        2: "a lot of difficulty",
        3: "cannot do at all",
    },
}

# ------------------------------------------------------------------------- column names

RENAMES: dict[str, dict[str, str]] = {
    "pov_2021": {
        "identif_menage": "hh_id",
        "dep_an_pc": "expenditure_pc",
        "conso_an_pc": "consumption_pc",
        "region": "region",
        "milieu": "milieu",
        "hh_size": "hh_size",
        "v700": "weight_hh",
        "v701": "weight_pop",
        "seuilbas_2021": "extreme_poverty_line",
        "seuilhaut_2021": "poverty_line",
        "pauv": "poor",
        "pauv_extreme": "extreme_poor",
        "sexe_chef": "head_sex",
        "age_chef": "head_age",
        "etat_mat_chef": "head_marital_status",
        "niveau_instr_chef": "head_education",
        "csp_chef": "head_csp",
        "quintile": "quintile",
        "decile": "decile",
        "cat_taille": "hh_size_class",
        "tranche_dep": "expenditure_bracket",
    },
    "donnindiv2021": {
        "identif_menage": "hh_id",
        "v050": "person_id",
        "v052": "relation_to_head",
        "sexe": "sex",
        "groupe_age": "age_group",
        "niveau_instr": "education_level",
        "csp": "csp",
    },
    "produit2021_plus": {
        "identifmenage": "hh_id",
        "v400": "questionnaire_table",
        "v403": "purchase_place",
        "v404": "production_origin",
        "v405": "acquisition_mode",
        "v406": "product_code",
        "v407": "expenditure_millimes",
        "v408": "quantity_grams",
        "v409": "covid_affected",
        "frequence": "frequency",
    },
    "code_produit": {"v406": "product_code", "libel_prdt_5": "product_label_fr"},
    "microdonnees_condvie": {
        "identifmenage": "hh_id",
        "v200": "building_type",
        "v201": "dwelling_type",
        "v202": "wall_material",
        "v203": "roof_material",
        "v204": "floor_material",
        "v205": "n_rooms",
        "v206": "tenure",
        "v207": "lighting_source",
        "v208": "has_natural_gas",
        "v209": "heating_energy",
        "v210": "water_source",
        "v211": "distance_to_water_point_m",
        "v212": "travel_time_to_water_point_min",
        "v213": "bathroom_type",
        "v214": "water_heating_energy",
        "v215": "toilet_type",
        "v216": "connected_to_sewerage",
        "v217": "kitchen_type",
        "v218": "cooking_energy",
        "v219": "distance_to_primary_school",
        "v220": "distance_to_middle_school",
        "v221": "distance_to_high_school",
        "v222": "distance_to_health_centre",
        "v223": "distance_to_local_hospital",
        "v228": "keeps_livestock",
        "v245": "has_radio",
        "v249": "has_television",
        "v251": "has_smart_television",
        "v259": "has_satellite_dish",
        "v261": "has_computer",
        "v263": "has_refrigerator",
        "v265": "has_freezer",
        "v267": "has_washing_machine",
        "v269": "has_dishwasher",
        "v275": "has_microwave",
        "v281": "has_air_conditioning",
        "v283": "has_heating",
        "v291": "has_vacuum_cleaner",
    },
    "Education2021": {
        "identifmenage": "hh_id",
        "v050": "person_id",
        "age": "age",
        "v054": "sex",
        "v061": "currently_enrolled",
        "v062": "education_cycle",
        "v064": "institution_type",
        "v065": "school_distance",
        "v066": "transport_mode",
        "v067": "travel_time_to_school_min",
        "v069": "scholarship",
        "v070": "scholarship_amount",
        "v071": "literate",
        "v073": "education_level_detailed",
        "v075": "diploma",
        "v078": "reason_left_school",
        "v080": "reason_never_studied",
        "v082": "uses_computer",
        "v083": "uses_internet",
        "v084": "worked_last_week",
        "v086": "reason_not_working",
        "v087": "job_search_method",
        "v089": "job_search_duration_months",
        "v092": "employment_status",
        "v093": "workplace",
    },
    "Sante2021": {
        "identifmenage": "hh_id",
        "v050": "person_id",
        "age": "age",
        "v600": "social_insurance",
        "v601": "insurance_scheme",
        "v604": "care_card",
        "v605": "covered_via_other_member",
        "v607": "has_chronic_disease",
        "v613": "chronic_disease_expenditure",
        "v614": "n_apci_conditions",
        "v615": "has_functional_difficulty",
        "v616_1": "difficulty_type",
        "v617_1": "difficulty_degree",
        "v647": "illness_in_reference_year",
        "v656": "consultation_expenditure",
        "v657": "medicine_expenditure",
        "v658": "hospital_night_in_reference_year",
        "v660": "n_hospital_nights",
        "v661": "hospital_stay_expenditure",
        "v666": "insurance_reimbursement",
    },
}

# Exported column -> the VALUE_SETS entry that decodes it.
COLUMN_VALUE_SET: dict[str, str] = {
    "region": "region",
    "milieu": "milieu",
    "poor": "poor_flag",
    "extreme_poor": "extreme_poor_flag",
    "head_sex": "sex_head",
    "head_marital_status": "marital_status",
    "head_education": "education_level",
    "head_csp": "csp",
    "hh_size_class": "household_size_class",
    "expenditure_bracket": "expenditure_bracket",
    "relation_to_head": "relation_to_head",
    "sex": "sex",
    "age_group": "age_group",
    "education_level": "education_level",
    "csp": "csp",
    "purchase_place": "purchase_place",
    "production_origin": "production_origin",
    "acquisition_mode": "acquisition_mode",
    "covid_affected": "covid_affected",
    "building_type": "building_type",
    "dwelling_type": "dwelling_type",
    "wall_material": "wall_material",
    "roof_material": "roof_material",
    "floor_material": "floor_material",
    "tenure": "tenure",
    "lighting_source": "lighting_source",
    "heating_energy": "energy_source",
    "water_heating_energy": "energy_source",
    "cooking_energy": "energy_source",
    "water_source": "water_source",
    "bathroom_type": "bathroom_type",
    "toilet_type": "toilet_type",
    "kitchen_type": "kitchen_type",
    "has_natural_gas": "yes_no",
    "connected_to_sewerage": "yes_no",
    "keeps_livestock": "yes_no",
    "currently_enrolled": "yes_no",
    "literate": "yes_no",
    "uses_computer": "yes_no",
    "uses_internet": "yes_no",
    "worked_last_week": "yes_no",
    "covered_via_other_member": "yes_no",
    "has_chronic_disease": "yes_no",
    "has_functional_difficulty": "yes_no",
    "illness_in_reference_year": "yes_no",
    "hospital_night_in_reference_year": "yes_no",
    "education_cycle": "education_cycle",
    "institution_type": "institution_type",
    "school_distance": "school_distance",
    "transport_mode": "transport_mode",
    "scholarship": "scholarship",
    "education_level_detailed": "education_level_detailed",
    "diploma": "diploma",
    "reason_left_school": "reason_left_school",
    "reason_never_studied": "reason_never_studied",
    "reason_not_working": "reason_not_working",
    "job_search_method": "job_search_method",
    "employment_status": "employment_status",
    "workplace": "workplace",
    "social_insurance": "social_insurance",
    "insurance_scheme": "insurance_scheme",
    "care_card": "care_card",
    "difficulty_type": "difficulty_type",
    "difficulty_degree": "difficulty_degree",
}

# Every "has_*" durable/amenity flag shares the yes/no set.
for _col in RENAMES["microdonnees_condvie"].values():
    if _col.startswith("has_"):
        COLUMN_VALUE_SET.setdefault(_col, "yes_no")

# The 12 consumption functions INS reports expenditure structure against, keyed by the
# leading two digits of the 5-digit product code.
CONSUMPTION_FUNCTIONS: dict[int, str] = {
    1: "Food and non-alcoholic beverages",
    2: "Alcohol and tobacco",
    3: "Clothing and footwear",
    4: "Housing and energy",
    5: "Furniture and household equipment",
    6: "Health and personal hygiene",
    7: "Transport",
    8: "Communication",
    9: "Recreation and culture",
    10: "Education",
    11: "Restaurants, cafes and holidays",
    12: "Other goods and services",
}

# INS does not assign every product to the function its code prefix implies. Nine
# ready-to-eat items carry 111xx codes but are counted under food in the published
# structure. The list is read off the "DPA_5Cfiffres" sheet of Annexe 3, where each
# 5-digit product sits under an explicit 2-digit section header; these nine sit under
# section 01 despite their code. Applying the override moves 32.3 DT per person and
# makes all twelve published function totals reproduce exactly.
PRODUCT_FUNCTION_OVERRIDES: dict[int, int] = {
    11171: 1,  # Pâtisserie
    11172: 1,  # Bol de sorgho
    11173: 1,  # Crêpe
    11174: 1,  # Beignet
    11175: 1,  # Fricassé, pâté
    11176: 1,  # Pizza
    11177: 1,  # Brik
    11178: 1,  # Glace, gervais, thelja
    11179: 1,  # Chips, pomme de terre frite
}

CONSUMPTION_FUNCTIONS_FR: dict[int, str] = {
    1: "Produits alimentaires et boissons non alcoolisées",
    2: "Alcool et tabacs",
    3: "Habillement",
    4: "Logement et énergie",
    5: "Meubles et équipement ménager",
    6: "Hygiène et soins",
    7: "Transport",
    8: "Télécommunication",
    9: "Loisirs et culture",
    10: "Éducation et enseignement",
    11: "Vacances, restaurants et cafés",
    12: "Autres",
}


def decode(series: pd.Series, set_name: str) -> pd.Series:
    """Map INS numeric codes to English categories.

    Codes absent from the mapping -- the 9 / 99 "non déclaré" sentinels, and any stray
    value -- become ``NA``, so a missing answer never masquerades as a category.
    """
    mapping = VALUE_SETS[set_name]
    decoded = series.map(mapping)
    return pd.Categorical(decoded, categories=list(mapping.values()))


def decode_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Decode every column of ``df`` that has a registered value set."""
    out = df.copy()
    for col, set_name in COLUMN_VALUE_SET.items():
        if col in out.columns:
            out[col] = decode(out[col], set_name)
    return out


def french_labels(set_name: str, meta, column: str) -> dict[float, tuple[str, str]]:
    """Pair each code's original French label with its English translation.

    Used by the codebook writer so the exported English never stands alone.
    """
    from .extract import value_labels

    original = value_labels(meta, column)
    english = VALUE_SETS[set_name]
    codes = sorted(set(original) | set(english))
    return {code: (original.get(code, ""), english.get(code, "")) for code in codes}
