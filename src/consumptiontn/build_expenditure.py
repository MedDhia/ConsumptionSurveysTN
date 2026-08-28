"""Product-level expenditure: the long file, the product dictionary, function totals.

The single most important thing to know about ``produit2021_plus.dta``: the recorded
amount ``v407`` is *not* annual. It is the amount observed over the diary/recall window
for that questionnaire table, and ``frequence`` is the annualisation multiplier. Summing
``v407 * frequence`` over a household reproduces ``dep_an_pc * hh_size`` from
``pov_2021.dta`` exactly (correlation 1.0000, median ratio 1.0000 across all 17,394
households). Summing ``v407`` alone gets you roughly a quarter of the right answer.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import labels
from .config import PROCESSED_DIR
from .extract import find, read_dta

MILLIMES_PER_DINAR = 1000


def consumption_function(code: pd.Series) -> pd.Series:
    """Leading digits of the 5-digit product code -> one of the 12 COICOP functions.

    A handful of dictionary entries are 3-digit (e.g. 151, "poissons frais"); for those
    the function is the leading *one* digit rather than the leading two.
    """
    code = code.astype("int64")
    fn = pd.Series(np.where(code < 1000, code // 100, code // 1000), index=code.index)
    override = code.map(labels.PRODUCT_FUNCTION_OVERRIDES)
    return fn.where(override.isna(), override).astype("int64")


def build_products() -> pd.DataFrame:
    """The 5-digit product dictionary, with its consumption function attached."""
    df, _ = read_dta(find("ebcnv2021_depenses", "code_produit.dta"))
    df = df.rename(columns=labels.RENAMES["code_produit"])
    df["product_code"] = df["product_code"].astype("int64")
    df["consumption_function_code"] = consumption_function(df["product_code"])
    df["consumption_function"] = df["consumption_function_code"].map(labels.CONSUMPTION_FUNCTIONS)
    df["consumption_function_fr"] = df["consumption_function_code"].map(labels.CONSUMPTION_FUNCTIONS_FR)
    return df.sort_values("product_code").reset_index(drop=True)


def build_expenditure_long() -> pd.DataFrame:
    """One row per household x observed product acquisition, annualised."""
    df, _ = read_dta(find("ebcnv2021_depenses", "produit2021_plus.dta"))
    df = df.rename(columns=labels.RENAMES["produit2021_plus"])

    # 48,053 of 3,308,405 rows carry no product code and no amount -- questionnaire
    # lines opened but not filled. They contribute nothing and are dropped.
    df = df.dropna(subset=["product_code", "expenditure_millimes"]).copy()
    df["product_code"] = df["product_code"].astype("int64")
    df["hh_id"] = df["hh_id"].astype("int64")

    df["expenditure_annual_dt"] = (
        df["expenditure_millimes"] * df["frequency"] / MILLIMES_PER_DINAR
    )
    df["consumption_function_code"] = consumption_function(df["product_code"])
    df["consumption_function"] = df["consumption_function_code"].map(labels.CONSUMPTION_FUNCTIONS)

    products = build_products()[["product_code", "product_label_fr"]]
    df = df.merge(products, on="product_code", how="left")

    df = labels.decode_frame(df)
    keep = [
        "hh_id",
        "product_code",
        "product_label_fr",
        "consumption_function_code",
        "consumption_function",
        "expenditure_annual_dt",
        "quantity_grams",
        "frequency",
        "purchase_place",
        "production_origin",
        "acquisition_mode",
        "covid_affected",
        "questionnaire_table",
    ]
    return df[keep].reset_index(drop=True)


def build_by_function(long: pd.DataFrame | None = None) -> pd.DataFrame:
    """Household x consumption function: annual expenditure in dinars, plus budget shares."""
    long = build_expenditure_long() if long is None else long
    wide = (
        long.groupby(["hh_id", "consumption_function_code"], observed=True)["expenditure_annual_dt"]
        .sum()
        .unstack(fill_value=0.0)
    )
    wide = wide.reindex(columns=sorted(labels.CONSUMPTION_FUNCTIONS), fill_value=0.0)
    wide.columns = [f"exp_{labels.CONSUMPTION_FUNCTIONS[c].split(' ')[0].lower().strip(',')}_{c:02d}" for c in wide.columns]
    wide["exp_total"] = wide.sum(axis=1)
    for col in [c for c in wide.columns if c != "exp_total"]:
        wide[col.replace("exp_", "share_", 1)] = wide[col] / wide["exp_total"]
    return wide.reset_index()


def run() -> dict[str, pd.DataFrame]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    long = build_expenditure_long()
    return {
        "tn_hbs_2021_products": build_products(),
        "tn_hbs_2021_expenditure": long,
        "tn_hbs_2021_expenditure_by_function": build_by_function(long),
    }
