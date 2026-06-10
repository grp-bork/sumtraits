import pandas as pd
import pytest

from sumtraits import workflow


def test_run_writes_archive_on_success(monkeypatch):
    calls = []
    translated_profile = pd.DataFrame({"sample_a": [1.0]}, index=[42])
    normalized_profile = pd.DataFrame({"taxon_id": [42], "sample_a": [1.0]})
    trait_summary = pd.DataFrame({"taxon_id": [42], "trait_name": ["motility"]})
    community_summary = pd.DataFrame({"trait": ["motility"]})

    def fake_translate_profile(path, profile_type, taxonomy_type):
        calls.append(("translate", path, profile_type, taxonomy_type))
        return {42}, translated_profile

    def fake_normalize_profile(profile):
        calls.append(("normalize", profile is translated_profile))
        return normalized_profile

    def fake_get_trait_summary(
        tax_ids, taxonomy_type, reference_data_dir, exclude_prediction_based
    ):
        calls.append(
            (
                "trait_summary",
                tax_ids,
                taxonomy_type,
                reference_data_dir,
                exclude_prediction_based,
            )
        )
        return trait_summary

    def fake_create_community_summary(summary, profile):
        calls.append(
            (
                "community_summary",
                summary is trait_summary,
                profile is normalized_profile,
            )
        )
        return community_summary

    def fake_write_output_archive(
        output_dir,
        taxonomic_profile,
        taxonomy_type,
        normalized,
        trait_rows,
        community_rows,
    ):
        calls.append(
            (
                "archive",
                output_dir,
                taxonomic_profile,
                taxonomy_type,
                normalized is normalized_profile,
                trait_rows is trait_summary,
                community_rows is community_summary,
            )
        )
        return "out/profile_summary_ncbi.tar.gz"

    monkeypatch.setattr(workflow, "translate_profile", fake_translate_profile)
    monkeypatch.setattr(workflow, "normalize_profile", fake_normalize_profile)
    monkeypatch.setattr(workflow, "get_trait_summary", fake_get_trait_summary)
    monkeypatch.setattr(
        workflow, "create_community_summary", fake_create_community_summary
    )
    monkeypatch.setattr(workflow, "write_output_archive", fake_write_output_archive)

    exit_code = workflow.run(
        "profile.tsv",
        "bracken",
        "ncbi",
        "reference_data",
        False,
        "out",
    )

    assert exit_code == 0
    assert calls == [
        ("translate", "profile.tsv", "bracken", "ncbi"),
        ("normalize", True),
        ("trait_summary", {42}, "ncbi", "reference_data", False),
        ("community_summary", True, True),
        (
            "archive",
            "out",
            "profile.tsv",
            "ncbi",
            True,
            True,
            True,
        ),
    ]


def test_run_returns_one_when_translation_finds_no_tax_ids(monkeypatch):
    translated_profile = pd.DataFrame({"sample_a": [1.0]}, index=[-1])

    monkeypatch.setattr(
        workflow,
        "translate_profile",
        lambda *args: (set(), translated_profile),
    )
    monkeypatch.setattr(workflow, "normalize_profile", lambda profile: profile)
    monkeypatch.setattr(
        workflow,
        "get_trait_summary",
        lambda *args: pytest.fail("trait summary should not be queried"),
    )

    assert (
        workflow.run("profile.tsv", "bracken", "ncbi", "reference_data", False, "out")
        == 1
    )


def test_run_returns_one_when_trait_summary_is_empty(monkeypatch):
    translated_profile = pd.DataFrame({"sample_a": [1.0]}, index=[42])
    normalized_profile = pd.DataFrame({"taxon_id": [42], "sample_a": [1.0]})

    monkeypatch.setattr(
        workflow,
        "translate_profile",
        lambda *args: ({42}, translated_profile),
    )
    monkeypatch.setattr(workflow, "normalize_profile", lambda profile: normalized_profile)
    monkeypatch.setattr(workflow, "get_trait_summary", lambda *args: pd.DataFrame())
    monkeypatch.setattr(
        workflow,
        "create_community_summary",
        lambda *args: pytest.fail("community summary should not be created"),
    )
    monkeypatch.setattr(
        workflow,
        "write_output_archive",
        lambda *args: pytest.fail("archive should not be written"),
    )

    assert (
        workflow.run("profile.tsv", "bracken", "ncbi", "reference_data", False, "out")
        == 1
    )
