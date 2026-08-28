"""Regenerate docs/SOURCES.md from the download manifest.

Keeping this generated means the checksums and retrieval dates in the documentation can
never drift from what was actually fetched.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from consumptiontn.config import PROJECT_ROOT, SOURCES  # noqa: E402
from consumptiontn.download import load_manifest  # noqa: E402

HEADER = """# Sources

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
"""


def main() -> None:
    manifest = load_manifest()["sources"]
    lines = [HEADER]
    for kind, title in [
        ("microdata", "Microdata archives"),
        ("annex", "Aggregate tables"),
        ("report", "Survey volumes and releases"),
        ("reference", "Reference documents"),
    ]:
        lines.append(f"\n### {title}\n")
        lines.append("| Key | Wave | File | Size | SHA-256 (first 16) | Retrieved |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for src in SOURCES:
            if src.kind != kind:
                continue
            entry = manifest.get(src.key)
            if entry is None:
                lines.append(f"| `{src.key}` | {src.wave or '—'} | [{src.filename}]({src.url}) | not fetched | — | — |")
                continue
            size = f"{entry['bytes'] / 1e6:.1f} MB"
            lines.append(
                f"| `{src.key}` | {src.wave or '—'} | [{src.filename}]({src.url}) | {size} "
                f"| `{entry['sha256'][:16]}` | {entry['retrieved_utc'][:10]} |"
            )
            lines.append(f"| | | {src.description} | | | |")
        for src in SOURCES:
            if src.kind == kind and src.members:
                lines.append("")
                lines.append(f"`{src.filename}` contains: " + ", ".join(f"`{Path(m).name}`" for m in src.members))

    out = PROJECT_ROOT / "docs" / "SOURCES.md"
    out.write_text("\n".join(lines).rstrip() + "\n")
    print(f"wrote {out.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
