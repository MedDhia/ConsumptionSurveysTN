"""Structural checks over the modules themselves. No data, no network, no apt packages.

These are the mistakes that are easiest to make while extending the pipeline and hardest
to notice: a decode rule pointing at a value set that was renamed, a source added to the
registry but never given a codebook title, a translation written for a column that is
never exported. Each currently fails only at build time, or not at all.

This module is the fast CI lane: it must never need `data/raw`.
"""

from __future__ import annotations

import json

import pytest

from consumptiontn import cli, codebook, config, labels

# --------------------------------------------------------------------------- labels

def test_every_decode_rule_names_a_real_value_set():
    unknown = {
        column: set_name
        for column, set_name in labels.COLUMN_VALUE_SET.items()
        if set_name not in labels.VALUE_SETS
    }
    assert not unknown, f"decode rules point at value sets that do not exist: {unknown}"


def test_no_orphan_value_sets():
    """A value set nothing references is dead weight, or a decode rule was dropped."""
    referenced = set(labels.COLUMN_VALUE_SET.values())
    orphans = set(labels.VALUE_SETS) - referenced
    assert not orphans, f"value sets defined but never used: {sorted(orphans)}"


def test_every_decoded_column_is_actually_exported():
    """Decoding a column no builder renames to is a silent no-op."""
    exported = {name for block in labels.RENAMES.values() for name in block.values()}
    dangling = set(labels.COLUMN_VALUE_SET) - exported
    assert not dangling, f"decode rules for columns nothing renames to: {sorted(dangling)}"


def test_value_sets_have_no_not_declared_category():
    """Codes 9 and 99 mean *non déclaré* and must map to missing, never to a category.

    Translating them into a category would turn "did not answer" into a substantive
    answer everywhere the data is grouped.
    """
    leaked = {
        name: value
        for name, mapping in labels.VALUE_SETS.items()
        for code, value in mapping.items()
        if code in (9, 99) and "declar" in value.lower()
    }
    # Code 9 is a legitimate substantive category in a few sets (e.g. "unemployed" in
    # `csp`, "animal dung" in `energy_source`), so this asserts on the *label*, not the
    # code: no exported category may read as a non-response.
    assert not leaked, f"non-response leaked into a category: {leaked}"


def test_product_function_overrides_are_well_formed():
    for code, function in labels.PRODUCT_FUNCTION_OVERRIDES.items():
        assert 10000 <= code <= 99999, f"{code} is not a 5-digit product code"
        assert function in labels.CONSUMPTION_FUNCTIONS, f"{code} -> unknown function {function}"


def test_consumption_function_names_are_complete_in_both_languages():
    assert set(labels.CONSUMPTION_FUNCTIONS) == set(range(1, 13))
    assert set(labels.CONSUMPTION_FUNCTIONS) == set(labels.CONSUMPTION_FUNCTIONS_FR)


# --------------------------------------------------------------------------- config

def test_source_keys_and_filenames_are_unique():
    keys = [s.key for s in config.SOURCES]
    filenames = [s.filename for s in config.SOURCES]
    assert len(keys) == len(set(keys))
    assert len(filenames) == len(set(filenames)), "two sources would overwrite each other"


def test_every_source_url_is_https_from_an_expected_host():
    """Two origins, and the distinction is deliberate rather than incidental.

    Everything INS publishes directly is fetched from ins.tn. The statistical yearbooks
    come from a Drive folder that mirrors them, which is why they are checksummed like
    everything else -- a mirror can be edited by whoever owns it, so the manifest is the
    only thing standing between a swapped file and a wrong figure.
    """
    for source in config.SOURCES:
        expected = config.DRIVE_DOWNLOAD if source.kind == "yearbook" else "https://www.ins.tn/"
        assert source.url.startswith(expected), source.key
        assert source.url.startswith("https://"), source.key


def test_every_source_has_a_description_and_known_kind():
    for source in config.SOURCES:
        assert source.description.strip(), source.key
        assert source.kind in {"microdata", "annex", "report", "reference", "yearbook"}, source.key
        assert source.wave is None or source.wave in config.WAVES, source.key


def test_source_lookup_rejects_typos():
    with pytest.raises(KeyError):
        config.source("ebcnv2021_depense")  # missing trailing s


def test_committed_manifest_covers_every_source():
    """The manifest is committed; a source added without re-fetching would be invisible."""
    manifest = json.loads(config.MANIFEST_PATH.read_text())["sources"]
    missing = {s.key for s in config.SOURCES} - set(manifest)
    assert not missing, f"run `make fetch` to add {sorted(missing)} to the manifest"
    for key, entry in manifest.items():
        assert entry["sha256"] and entry["bytes"] > 0, key
        assert entry["filename"] == config.source(key).filename, key


# ----------------------------------------------------------------------- wiring

def test_codebook_knows_where_every_rename_block_came_from():
    assert set(codebook.SOURCE_FILES) == set(labels.RENAMES)


def test_codebook_source_files_name_real_archive_members():
    for key, member in codebook.SOURCE_FILES.values():
        source = config.source(key)
        assert member in {m.rsplit("/", 1)[-1] for m in source.members}, f"{key}: {member}"


def test_every_dataset_has_both_a_title_and_an_intro():
    """`cli._write` raises KeyError at build time if either is missing."""
    assert set(cli.TITLES) == set(cli.INTROS)
    assert cli.GZIP_CSV <= set(cli.TITLES)


def test_units_and_derived_descriptions_are_non_empty():
    for mapping in (codebook.UNITS, codebook.DERIVED):
        for column, text in mapping.items():
            assert text.strip(), column


# ------------------------------------------------------------------------- yearbooks

def test_yearbook_editions_are_unique_and_plausible():
    years = list(config.YEARBOOK_FILE_IDS)
    assert len(years) == len(set(years))
    assert min(years) == 2001 and max(years) == 2023
    assert 2013 not in years, "2013 was never issued in this collection"


def test_every_parsed_edition_is_actually_registered():
    """`YEARBOOKS_PARSED` names the editions the builders open. A typo there would fail
    at build time with a confusing missing-file error rather than here."""
    registered = set(config.YEARBOOK_FILE_IDS)
    missing = set(config.YEARBOOKS_PARSED) - registered
    assert not missing, f"parsed editions that are not in the registry: {sorted(missing)}"


def test_price_and_labour_builders_only_read_registered_editions():
    from consumptiontn import build_labour, build_prices

    registered = set(config.YEARBOOK_FILE_IDS)
    assert build_prices.EDITION in registered
    assert set(build_labour.EDITIONS) <= registered


def test_labour_editions_overlap_so_the_splice_is_checkable():
    """Each edition carries about five years. If the chosen editions were five or more
    years apart there would be no shared year, and nothing would verify the splice."""
    editions = sorted(build_labour_editions())
    gaps = [b - a for a, b in zip(editions, editions[1:], strict=False)]
    assert gaps and max(gaps) <= 4, f"editions {editions} leave an unverifiable gap"


def build_labour_editions():
    from consumptiontn import build_labour

    return build_labour.EDITIONS


def test_sources_doc_covers_every_registered_source():
    """`docs/SOURCES.md` is generated by `make docs`, and nothing was checking it.

    That is exactly how it went stale: 22 yearbooks were added to the registry and the
    document kept describing 21 artefacts, because no test and no CI step ever looked.
    """
    doc = (config.PROJECT_ROOT / "docs" / "SOURCES.md").read_text()
    missing = [s.key for s in config.SOURCES if s.key not in doc]
    assert not missing, (
        f"{len(missing)} sources are absent from docs/SOURCES.md "
        f"(run `make docs`): {missing[:5]}"
    )
