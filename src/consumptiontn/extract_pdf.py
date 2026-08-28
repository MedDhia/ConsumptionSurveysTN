"""Table extraction from the INS PDF volumes.

Only one table family is machine-extracted: the 23 per-governorate delegation tables in
the 2020 poverty map, which have a clean text layer and a fixed five-column shape. The
older EBCNV volumes are right-to-left Arabic with column order reversed and headers
split across lines; their numbers are transcribed by hand in ``panel_sources.py`` with a
page citation instead, which is auditable in a way a fragile RTL parser is not.
"""

from __future__ import annotations

import re
import subprocess

import pandas as pd

from .config import RAW_DIR, source

# "Tableau 19.Taux d'abandon scolaire et taux de pauvreté des délégations de Kasserine"
_TABLE_HEADER = re.compile(
    r"Tableau\s+\d+\s*\.?\s*Taux d’abandon scolaire et taux de pauvreté des délégations "
    r"(?:du|de la|de l’|de)\s+(.+)"
)
# "HASSI FRID   3,5   25,6   7,4   53,5"  -- name, then exactly four French-decimal numbers
_ROW = re.compile(r"^(.+?)\s{2,}([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s*$")


def pdf_text(key: str) -> str:
    """Layout-preserving text of a fetched PDF (requires poppler's ``pdftotext``)."""
    path = RAW_DIR / source(key).filename
    if not path.exists():
        raise FileNotFoundError(f"{path} not fetched yet")
    out = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True,
        capture_output=True,
    )
    return out.stdout.decode("utf-8", errors="replace")


def _num(token: str) -> float:
    return float(token.replace(",", ".").replace(" ", ""))


def delegation_poverty() -> pd.DataFrame:
    """Delegation-level poverty and school-dropout rates from the 2020 poverty map.

    These are **modelled small-area estimates** built on EBCNV 2015 and the 2014 census,
    not direct survey estimates -- EBCNV is designed to be representative at the region
    x milieu level, not below it. The ``estimate_type`` column says so on every row.
    """
    text = pdf_text("carte_pauvrete_2020")
    records: list[dict] = []
    governorate: str | None = None
    rows_since_header = 0

    for line in text.splitlines():
        header = _TABLE_HEADER.search(line)
        if header:
            governorate = header.group(1).strip().rstrip(".")
            rows_since_header = 0
            continue
        if governorate is None:
            continue
        match = _ROW.match(line.rstrip())
        if not match:
            # Tables are contiguous; a run of non-matching lines ends the current one.
            if rows_since_header:
                rows_since_header += 1
                if rows_since_header > 6:
                    governorate = None
            continue
        name = match.group(1).strip()
        if not name or name.lower().startswith(("délégation", "source")):
            continue
        records.append(
            {
                "governorate": governorate,
                "delegation": name,
                "dropout_primary_pct": _num(match.group(2)),
                "dropout_secondary_pct": _num(match.group(3)),
                "dropout_both_cycles_pct": _num(match.group(4)),
                "poverty_rate_pct": _num(match.group(5)),
            }
        )
        rows_since_header = 1

    df = pd.DataFrame.from_records(records)
    # Seliana is the one governorate whose table in this report carries dropout rates
    # only, with no poverty column, so it has no rows here.
    df["governorate"] = df["governorate"].str.replace("l’Ariana", "Ariana", regex=False)
    df["reference_year"] = 2015
    df["estimate_type"] = "modelled small-area estimate"
    df["source_document"] = "Carte de la pauvreté en Tunisie (INS, September 2020)"
    return df.drop_duplicates(subset=["governorate", "delegation"]).reset_index(drop=True)
