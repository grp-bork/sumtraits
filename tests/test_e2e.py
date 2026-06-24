"""End-to-end tests that run the sumtraits CLI against test_data/ inputs and
compare two output files (taxon_trait_annotations.tsv,
community_trait_annotations.tsv) to the reference copies generated from
test_results/ by scripts/build_e2e_reference.sh.

These tests need the (large, gitignored) test_data/ and reference_data/
fixture directories to be present locally; they are skipped otherwise.
"""

from pathlib import Path

import pandas as pd
import pytest

from sumtraits import cli

REPO_ROOT = Path(__file__).resolve().parent.parent
TEST_DATA_DIR = Path(__file__).resolve().parent / "data" / "input"
REFERENCE_DATA_DIR = REPO_ROOT / "reference_data"
E2E_REFERENCE_DIR = Path(__file__).resolve().parent / "data" / "e2e_reference"

TAXONOMY_TYPES = ["ncbi", "gtdb"]
OUTPUT_FILE_NAMES = ["taxon_trait_annotations.tsv", "community_trait_annotations.tsv"]

# Run regularly: cheap enough for routine test runs.
DEFAULT_PROFILE_TYPES = {
    "metaphlan": "metaphlan4_default.txt",
    "motus": "motus3_truncated.tsv",
    "generic_ncbi": "NCBI_genus_enterotype_truncated.tsv",
    "generic_gtdb": "GTDB_genus_enterotype_truncated.tsv",
}

# Only run on demand (`pytest -m e2e`): redundant translator code paths that
# are slower without adding meaningfully different coverage.
EXTENDED_PROFILE_TYPES = {
    "bracken": "bracken_NCBI.tsv",
    "kaiju": "kaiju_NCBI.txt",
    "kraken2": "kraken2_GTDB.txt",
    "krakenuniq": "krakenuniq_GTDB.txt",
}

FIXTURES_AVAILABLE = TEST_DATA_DIR.is_dir() and REFERENCE_DATA_DIR.is_dir()
skip_unless_fixtures_available = pytest.mark.skipif(
    not FIXTURES_AVAILABLE,
    reason="test_data/ and reference_data/ fixtures are not available locally",
)


def _combo_params(profile_types: dict[str, str]) -> list[tuple[str, str, str]]:
    return [
        (taxonomy_type, profile_type, input_file_name)
        for taxonomy_type in TAXONOMY_TYPES
        for profile_type, input_file_name in profile_types.items()
    ]


def _combo_id(combo: tuple[str, str, str]) -> str:
    taxonomy_type, profile_type, _ = combo
    return f"{taxonomy_type}-{profile_type}"


def _run_sumtraits(
    input_file: Path, profile_type: str, taxonomy_type: str, output_dir: Path
) -> None:
    exit_code = cli.main(
        [
            "--input-taxonomic-profile",
            str(input_file),
            "--taxonomic-profile-type",
            profile_type,
            "--taxonomy-type",
            taxonomy_type,
            "--sumtraits-reference-data-dir",
            str(REFERENCE_DATA_DIR),
            "--output-dir",
            str(output_dir),
        ]
    )
    assert exit_code == 0


def _assert_output_matches_reference(
    output_dir: Path, reference_dir: Path, file_name: str
) -> None:
    actual = pd.read_csv(output_dir / file_name, sep="\t")
    expected = pd.read_csv(reference_dir / f"{file_name}.gz", sep="\t")
    pd.testing.assert_frame_equal(actual, expected)


@skip_unless_fixtures_available
@pytest.mark.parametrize(
    "combo", _combo_params(DEFAULT_PROFILE_TYPES), ids=_combo_id
)
def test_pipeline_matches_reference(combo: tuple[str, str, str], tmp_path: Path):
    taxonomy_type, profile_type, input_file_name = combo
    input_file = TEST_DATA_DIR / input_file_name
    reference_dir = E2E_REFERENCE_DIR / taxonomy_type / profile_type

    _run_sumtraits(input_file, profile_type, taxonomy_type, tmp_path)

    for file_name in OUTPUT_FILE_NAMES:
        _assert_output_matches_reference(tmp_path, reference_dir, file_name)


@pytest.mark.e2e
@skip_unless_fixtures_available
@pytest.mark.parametrize(
    "combo", _combo_params(EXTENDED_PROFILE_TYPES), ids=_combo_id
)
def test_pipeline_matches_reference_extended(
    combo: tuple[str, str, str], tmp_path: Path
):
    taxonomy_type, profile_type, input_file_name = combo
    input_file = TEST_DATA_DIR / input_file_name
    reference_dir = E2E_REFERENCE_DIR / taxonomy_type / profile_type

    _run_sumtraits(input_file, profile_type, taxonomy_type, tmp_path)

    for file_name in OUTPUT_FILE_NAMES:
        _assert_output_matches_reference(tmp_path, reference_dir, file_name)
