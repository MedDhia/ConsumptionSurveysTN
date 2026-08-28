"""Unpack INS archives and read the Stata files inside.

One gotcha worth stating up front: ``unar`` (and the ``unrar``-backed ``rarfile``
package) truncates ``pov_2021.dta`` out of ``FichiersDepenses.rar`` -- it stops at
1,310,720 of 1,411,290 bytes with "Attempted to read more data than was available",
and the resulting .dta is unreadable. libarchive's ``bsdtar`` extracts the same entry
correctly, so that is what this module uses.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pandas as pd
import pyreadstat

from .config import INTERIM_DIR, RAW_DIR, source

EXTRACTOR = "bsdtar"


def ensure_extractor() -> str:
    path = shutil.which(EXTRACTOR)
    if path is None:
        raise RuntimeError(
            f"{EXTRACTOR} not found. Install libarchive-tools "
            "(apt-get install libarchive-tools). Do not substitute unar/unrar: they "
            "silently truncate pov_2021.dta -- see this module's docstring."
        )
    return path


def unpack(key: str, *, force: bool = False) -> Path:
    """Extract an archive source into ``data/interim/<key>/``. Returns that directory."""
    src = source(key)
    archive = RAW_DIR / src.filename
    if not archive.exists():
        raise FileNotFoundError(f"{archive} not fetched yet; run the fetch step first")
    out = INTERIM_DIR / key
    if out.exists() and not force and any(out.rglob("*.dta")):
        return out
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run([ensure_extractor(), "-xf", str(archive)], cwd=out, check=True)
    extracted = {p.name for p in out.rglob("*") if p.is_file()}
    missing = [m for m in src.members if Path(m).name not in extracted]
    if missing:
        raise RuntimeError(f"{key}: archive did not yield {missing}")
    return out


def find(key: str, member_name: str) -> Path:
    """Locate an extracted member by basename, ignoring the archive's folder nesting."""
    root = unpack(key)
    matches = [p for p in root.rglob(member_name) if p.is_file()]
    if not matches:
        raise FileNotFoundError(f"{member_name} not found under {root}")
    return matches[0]


def read_dta(path: Path, *, apply_labels: bool = False) -> tuple[pd.DataFrame, object]:
    """Read a Stata file, returning the frame and its readstat metadata.

    Value labels are kept out of the data by default: the build steps map codes to
    English explicitly (see ``labels.py``) rather than inheriting French label text.
    """
    return pyreadstat.read_dta(str(path), apply_value_formats=apply_labels)


def value_labels(meta, column: str) -> dict:
    """The {code: French label} mapping Stata attached to ``column`` (empty if none)."""
    label_set = meta.variable_to_label.get(column)
    return dict(meta.value_labels.get(label_set, {})) if label_set else {}
