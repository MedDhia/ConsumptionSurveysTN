#!/usr/bin/env bash
# System dependencies for the pipeline. Python packages come from requirements.txt.
set -euo pipefail

# libarchive-tools provides bsdtar, the only extractor that reads INS's RAR5 archives
# correctly. unar and unrar truncate pov_2021.dta -- see src/consumptiontn/extract.py.
# poppler-utils provides pdftotext, used for the poverty-map tables.
if command -v apt-get >/dev/null 2>&1; then
    apt-get update -qq
    apt-get install -y -qq libarchive-tools poppler-utils
elif command -v brew >/dev/null 2>&1; then
    brew install libarchive poppler
else
    echo "Install libarchive (bsdtar) and poppler (pdftotext) with your package manager." >&2
    exit 1
fi

python3 -m pip install -r requirements.txt
