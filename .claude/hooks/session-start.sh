#!/bin/bash
# Bring a fresh Claude Code web session up to where `make test` works.
#
# The pipeline needs two system binaries that are not preinstalled -- bsdtar (the only
# extractor that reads INS's RAR5 archives without truncating pov_2021.dta) and
# pdftotext -- plus the Python requirements. Without them the first thing anyone tries
# fails confusingly.
#
# Deliberately does NOT download the 86 MB of INS artefacts: that is `make fetch`, and
# most sessions do not need it. `make test-fast` works after this hook; `make test`
# needs a fetch first.
set -euo pipefail

# Local machines are already set up by whoever set them up.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
    exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}"

echo 'export PYTHONPATH="src"' >> "${CLAUDE_ENV_FILE:-/dev/null}"

needs_setup=false
for binary in bsdtar pdftotext; do
    command -v "$binary" >/dev/null 2>&1 || needs_setup=true
done
python3 -c "import pandas, pyreadstat, pyarrow, openpyxl, pdfplumber, pytest" 2>/dev/null \
    || needs_setup=true
command -v ruff >/dev/null 2>&1 || needs_setup=true

if [ "$needs_setup" = false ]; then
    echo "session-start: dependencies already present"
    exit 0
fi

PIP_ARGS="--break-system-packages" REQUIREMENTS="requirements-dev.txt" ./scripts/setup.sh
