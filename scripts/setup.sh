#!/usr/bin/env bash
# System dependencies for the pipeline. Python packages come from requirements.txt.
#
# Two binaries are non-negotiable:
#   bsdtar    (libarchive) is the only extractor that reads INS's RAR5 archives
#             correctly -- unar and unrar truncate pov_2021.dta. See extract.py.
#   pdftotext (poppler) reads the poverty-map tables.
set -euo pipefail

SUDO=""
if [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
fi

# Some distributions ship an externally managed Python and need
# PIP_ARGS=--break-system-packages.
PIP_ARGS="${PIP_ARGS:-}"
REQUIREMENTS="${REQUIREMENTS:-requirements.txt}"

if command -v apt-get >/dev/null 2>&1; then
    $SUDO apt-get update -qq
    $SUDO apt-get install -y -qq libarchive-tools poppler-utils
elif command -v brew >/dev/null 2>&1; then
    brew install libarchive poppler
else
    echo "Install libarchive (bsdtar) and poppler (pdftotext) with your package manager." >&2
    exit 1
fi

python3 -m pip install $PIP_ARGS -r "$REQUIREMENTS"

for binary in bsdtar pdftotext; do
    command -v "$binary" >/dev/null 2>&1 || { echo "$binary still missing" >&2; exit 1; }
done
echo "setup complete: $(bsdtar --version | head -1), $(pdftotext -v 2>&1 | head -1)"
