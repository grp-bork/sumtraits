import pandas as pd
import pytest

from sumtraits.community import create_community_summary


def _trait_row(
    taxon_id,
    trait_name,
    unit,
    consensus_value,
    *,
    mean=pd.NA,
):
    return {
        "taxon_id": taxon_id,
        "taxon_name": f"taxon {taxon_id}",
        "trait_name": trait_name,
        "unit": unit,
        "database_count": 1,
        "total_observations": 1,
        "consensus_value": consensus_value,
        "consensus_count": 1,
        "consensus_percentage": 100.0,
        "minimum": pd.NA,
        "median": pd.NA,
        "mean": mean,
        "maximum": pd.NA,
        "discrete_values": pd.NA,
        "databases": "synthetic",
        "group_1": "group",
        "group_2": "group",
        "ontology_ids": pd.NA,
        "taxon_lineage": "synthetic lineage",
    }


def _row_by_summary_type(summary, summary_type):
    matches = summary.loc[summary["summary_type"] == summary_type]
    assert matches.shape[0] == 1
    return matches.iloc[0]


def test_create_community_summary_handles_boolean_traits():
    profile = pd.DataFrame(
        {
            "taxon_id": [1, 2, 3, -1],
            "sample_a": [0.2, 0.5, 0.1, 0.2],
            "sample_b": [0.3, 0.0, 0.4, 0.3],
        }
    )
    trait_summary = pd.DataFrame(
        [
            _trait_row(1, "oxygen", "boolean", "true"),
            _trait_row(2, "oxygen", "boolean", "false"),
            _trait_row(3, "oxygen", "boolean", "No robust majority"),
        ]
    )

    result = create_community_summary(trait_summary, profile)

    true_row = _row_by_summary_type(result, "consensus_true")
    false_row = _row_by_summary_type(result, "consensus_false")
    no_majority_row = _row_by_summary_type(result, "no_majority")
    unannotated_row = _row_by_summary_type(result, "unannotated")
    unclassified_row = _row_by_summary_type(result, "unclassified")
    assert true_row["feature"] == "oxygen.true"
    assert true_row["sample_a"] == pytest.approx(0.2)
    assert true_row["sample_b"] == pytest.approx(0.3)
    assert false_row["sample_a"] == pytest.approx(0.5)
    assert false_row["sample_b"] == pytest.approx(0.0)
    assert no_majority_row["sample_a"] == pytest.approx(0.1)
    assert no_majority_row["sample_b"] == pytest.approx(0.4)
    assert unannotated_row["sample_a"] == pytest.approx(0.0)
    assert unannotated_row["sample_b"] == pytest.approx(0.0)
    assert unclassified_row["sample_a"] == pytest.approx(0.2)
    assert unclassified_row["sample_b"] == pytest.approx(0.3)


def test_create_community_summary_handles_numeric_traits():
    profile = pd.DataFrame(
        {
            "taxon_id": [1, 2],
            "sample_a": [0.25, 0.75],
            "sample_b": [0.0, 0.0],
        }
    )
    trait_summary = pd.DataFrame(
        [
            _trait_row(1, "genome size", "bp", pd.NA, mean=10.0),
            _trait_row(2, "genome size", "bp", pd.NA, mean=20.0),
        ]
    )

    result = create_community_summary(trait_summary, profile)

    mean_row = _row_by_summary_type(result, "numeric_mean")
    assert mean_row["feature"] == "genome_size.mean"
    assert mean_row["sample_a"] == pytest.approx(17.5)
    assert pd.isna(mean_row["sample_b"])
    assert "no_majority" not in result["summary_type"].tolist()


def test_create_community_summary_handles_factor_traits():
    profile = pd.DataFrame(
        {
            "taxon_id": [1, 2, 3, -1],
            "sample_a": [0.4, 0.3, 0.2, 0.1],
        }
    )
    trait_summary = pd.DataFrame(
        [
            _trait_row(1, "cell shape", "factor", "rod"),
            _trait_row(2, "cell shape", "factor", "coccus"),
            _trait_row(3, "cell shape", "factor", "rod"),
        ]
    )

    result = create_community_summary(trait_summary, profile)

    majority_row = _row_by_summary_type(result, "consensus_majority")
    other_row = _row_by_summary_type(result, "consensus_other")
    assert majority_row["feature"] == "cell_shape.rod"
    assert majority_row["sample_a"] == pytest.approx(0.6)
    assert other_row["feature"] == "cell_shape.other"
    assert other_row["sample_a"] == pytest.approx(0.3)


def test_create_community_summary_returns_expected_columns_for_empty_summary():
    result = create_community_summary(
        pd.DataFrame(columns=_trait_row(1, "trait", "boolean", "true").keys()),
        pd.DataFrame({"taxon_id": [1], "sample_a": [1.0]}),
    )

    assert result.empty
    assert result.columns.tolist() == ["trait", "summary_type", "feature", "sample_a"]
