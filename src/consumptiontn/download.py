"""Fetch INS artefacts and record what was fetched.

Every download is checksummed into ``data/raw/manifest.json``. The manifest is the
version-controlled part -- the raw files themselves are not, since they are large and
re-fetchable. If INS silently replaces a file, ``verify()`` will say so.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import requests

from .config import MANIFEST_PATH, RAW_DIR, SOURCES, Source, source

CHUNK = 1 << 20
TIMEOUT = 120
RETRIES = 4  # INS occasionally 503s under load

# First bytes a file of each type must start with. Checked after every download because
# the failure this catches is silent: a host that answers a download with an HTML
# interstitial or an error page still returns 200, and the bytes still hash cleanly. The
# manifest would then record a checksum for a web page and report drift on every
# subsequent run. Relevant for the yearbook mirror in particular, which serves through a
# consent/scan interstitial when it decides to.
MAGIC: dict[str, bytes] = {
    ".pdf": b"%PDF",
    ".xlsx": b"PK\x03\x04",
    ".rar": b"Rar!",
}


def check_looks_right(path: Path) -> None:
    """Fail loudly if a download is not the kind of file its extension claims."""
    expected = MAGIC.get(path.suffix.lower())
    if expected is None:
        return
    with path.open("rb") as fh:
        head = fh.read(len(expected))
    if head != expected:
        raise RuntimeError(
            f"{path.name} does not start with {expected!r} -- got {head!r}. "
            "The server most likely returned an error or interstitial page rather than "
            "the file. Nothing has been written to the manifest."
        )


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def _get(url: str, dest: Path) -> None:
    last: Exception | None = None
    for attempt in range(RETRIES):
        try:
            with requests.get(url, stream=True, timeout=TIMEOUT) as resp:
                resp.raise_for_status()
                tmp = dest.with_suffix(dest.suffix + ".part")
                with tmp.open("wb") as fh:
                    for block in resp.iter_content(CHUNK):
                        fh.write(block)
                tmp.replace(dest)
            return
        except Exception as exc:  # noqa: BLE001 - retried below, re-raised at the end
            last = exc
            if attempt < RETRIES - 1:
                import time

                time.sleep(2**(attempt + 1))
    raise RuntimeError(f"failed to download {url}") from last


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return {"retrieved": {}, "sources": {}}


def save_manifest(manifest: dict) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True)
    MANIFEST_PATH.write_text(text + "\n")


def fetch(src: Source, *, force: bool = False) -> Path:
    """Download one source if it is not already present. Returns the local path."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dest = RAW_DIR / src.filename
    if dest.exists() and not force:
        return dest
    print(f"  fetching {src.key} -> {src.filename}")
    _get(src.url, dest)
    check_looks_right(dest)
    return dest


def fetch_all(
    keys: list[str] | None = None,
    *,
    force: bool = False,
    write_manifest: bool = True,
) -> tuple[dict, list[str]]:
    """Fetch the listed sources (all of them by default).

    Returns the manifest and the keys whose checksum differs from what the manifest
    already recorded -- i.e. the files INS has republished since we last looked. Pass
    ``write_manifest=False`` to compare without overwriting the committed record, which
    is what ``check_upstream`` needs.
    """
    manifest = load_manifest()
    targets = [source(k) for k in keys] if keys else list(SOURCES)
    changed: list[str] = []
    for src in targets:
        path = fetch(src, force=force)
        digest = sha256(path)
        previous = manifest["sources"].get(src.key, {}).get("sha256")
        if previous and previous != digest:
            changed.append(src.key)
            print(f"  ! {src.key} changed upstream (was {previous[:12]}..., now {digest[:12]}...)")
        manifest["sources"][src.key] = {
            "url": src.url,
            "filename": src.filename,
            "wave": src.wave,
            "kind": src.kind,
            "description": src.description,
            "bytes": path.stat().st_size,
            "sha256": digest,
            "retrieved_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    if write_manifest:
        save_manifest(manifest)
    return manifest, changed


def check_upstream() -> list[str]:
    """Re-download everything and report what INS has changed since the manifest was written.

    ``verify()`` cannot do this: it compares local files to the manifest, and ``fetch``
    skips anything already on disk, so a warm cache always agrees with itself. Detecting
    drift means fetching fresh and diffing against the committed record without
    overwriting it.
    """
    _, changed = fetch_all(force=True, write_manifest=False)
    return changed


def verify() -> list[str]:
    """Return the keys whose local file is missing or no longer matches the manifest."""
    manifest = load_manifest()
    problems = []
    for key, entry in manifest["sources"].items():
        path = RAW_DIR / entry["filename"]
        if not path.exists():
            problems.append(f"{key}: missing {entry['filename']}")
        elif sha256(path) != entry["sha256"]:
            problems.append(f"{key}: checksum mismatch")
    return problems


if __name__ == "__main__":
    fetch_all()
