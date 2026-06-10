import tarfile

import pandas as pd
import pytest

from sumtraits import processing


def test_get_trait_summary_reads_synthetic_reference_data(tmp_path):
    reference_file = tmp_path / "ncbi_no_predictions.tsv"
    pd.DataFrame(
        {
            "taxon_id": [1, 2, 3],
            "trait_name": ["a", "b", "c"],
        }
    ).to_csv(reference_file, sep="\t", index=False)

    result = processing.get_trait_summary({1, 3}, "NCBI", tmp_path, True)

    assert result["taxon_id"].tolist() == [1, 3]
    assert result["trait_name"].tolist() == ["a", "c"]


def test_normalize_profile_moves_index_to_taxon_id_column():
    profile = pd.DataFrame({"sample_a": [0.25, 0.75]}, index=["1", "2"])

    result = processing.normalize_profile(profile)

    assert result.columns.tolist() == ["taxon_id", "sample_a"]
    assert result["taxon_id"].tolist() == [1, 2]
    assert str(result["taxon_id"].dtype) == "int64"


def test_write_output_archive_contains_expected_files(tmp_path):
    input_file = tmp_path / "profile.tsv"
    input_file.write_text("original profile\n", encoding="utf-8")
    output_dir = tmp_path / "out"
    normalized_profile = pd.DataFrame({"taxon_id": [1], "sample_a": [1.0]})
    trait_summary = pd.DataFrame({"taxon_id": [1], "trait_name": ["motility"]})
    community_summary = pd.DataFrame(
        {"trait": ["motility"], "summary_type": ["consensus_true"], "sample_a": [1.0]}
    )

    archive_path = processing.write_output_archive(
        str(output_dir),
        str(input_file),
        "ncbi",
        normalized_profile,
        trait_summary,
        community_summary,
    )

    assert archive_path == output_dir / "profile_summary_ncbi.tar.gz"
    with tarfile.open(archive_path, "r:gz") as tar:
        names = tar.getnames()
        assert names == [
            "profile.ncbi.tsv",
            "taxon_trait_annotations.tsv",
            "community_trait_annotations.tsv",
            "profile.tsv",
        ]
        normalized = tar.extractfile("profile.ncbi.tsv").read().decode("utf-8")
        original = tar.extractfile("profile.tsv").read().decode("utf-8")

    assert "taxon_id\tsample_a" in normalized
    assert original == "original profile\n"


def test_write_output_archive_rejects_output_path_that_is_file(tmp_path):
    input_file = tmp_path / "profile.tsv"
    input_file.write_text("original profile\n", encoding="utf-8")
    output_path = tmp_path / "not-a-directory"
    output_path.write_text("", encoding="utf-8")

    with pytest.raises(NotADirectoryError):
        processing.write_output_archive(
            str(output_path),
            str(input_file),
            "ncbi",
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
        )
