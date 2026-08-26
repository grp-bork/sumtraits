# metatraits/web/profile_annotation/processing.py

import pandas as pd
import numpy as np
from pandas._typing import Scalar

from typing import Any

import logging

logger = logging.getLogger(__name__)


def _make_matrix_row(
    trait: Scalar,
    annotation_status: str,
    value: Any,
    values: pd.Series,
    *,
    fill_value: float | None = 0.0,
) -> dict:
    aligned = values.fillna(fill_value) if fill_value is not None else values

    return {
        "trait": trait,
        "annotation_status": annotation_status,
        "value": value,
        **{
            column: None if pd.isna(val) else float(val)
            for column, val in aligned.items()
        },
    }


def _prepare_trait_summary(summary_df: pd.DataFrame) -> pd.DataFrame:
    # TODO: do not rename any columns. Only add the new columns required by _build_sample_matrix
    summary_df = summary_df.rename(
        columns={
            "trait_name": "trait",
            "mean": "consensus_numeric_value",
        }
    )

    def _get_value_type_col(value):
        if value == "boolean" or value == "factor":
            return value
        else:
            return "numeric"

    def _get_consensus_bool(value):
        if value == "true":
            return True
        elif value == "false":
            return False
        else:
            return pd.NA

    summary_df["value_type"] = summary_df["unit"].apply(_get_value_type_col)
    summary_df["consensus_value"] = summary_df["consensus_value"].fillna(
        summary_df["consensus_numeric_value"]
    )
    summary_df["consensus_bool"] = summary_df["consensus_value"].apply(
        _get_consensus_bool
    )
    summary_df["is_consensus"] = np.where(
        summary_df["consensus_value"] == "No robust majority",
        False,
        True,
    )
    summary_df = summary_df.sort_values(["taxon_id", "trait"]).reset_index(drop=True)

    return summary_df


def _make_no_majority_row(
    trait: Scalar,
    no_majority_sum: pd.Series,
) -> dict:
    return _make_matrix_row(trait, "no_majority", None, no_majority_sum)


def _build_boolean_rows(
    trait: Scalar,
    sample_columns: list[str],
    zero_values: pd.Series,
    consensus_rows: pd.DataFrame,
    no_majority_sum: pd.Series,
) -> list[dict]:
    true_sum = consensus_rows.loc[
        consensus_rows["consensus_bool"] == True, sample_columns
    ].sum()
    false_sum = consensus_rows.loc[
        consensus_rows["consensus_bool"] == False, sample_columns
    ].sum()
    if true_sum.empty:
        true_sum = zero_values
    if false_sum.empty:
        false_sum = zero_values

    return [
        _make_matrix_row(trait, "consensus", "true", true_sum),
        _make_matrix_row(trait, "consensus", "false", false_sum),
        _make_no_majority_row(trait, no_majority_sum),
    ]


def _build_numeric_rows(
    trait: Scalar,
    sample_columns: list[str],
    consensus_rows: pd.DataFrame,
) -> list[dict]:
    numeric_rows = consensus_rows.loc[consensus_rows["consensus_numeric_value"].notna()]
    if not numeric_rows.empty:
        weighted_sum = (
            numeric_rows[sample_columns]
            .mul(numeric_rows["consensus_numeric_value"].astype(float), axis=0)
            .sum()
        )
        total_weight = numeric_rows[sample_columns].sum()
        denom = total_weight.replace(0.0, pd.NA)
        mean_values = weighted_sum.divide(denom)
    else:
        mean_values = pd.Series(
            [pd.NA] * len(sample_columns), index=sample_columns, dtype="float64"
        )

    return [
        _make_matrix_row(
            trait,
            "weighted_mean",
            None,
            mean_values,
            fill_value=None,
        )
    ]


def _build_factor_rows(
    trait: Scalar,
    sample_columns: list[str],
    consensus_rows: pd.DataFrame,
    no_majority_sum: pd.Series,
) -> list[dict]:
    rows: list[dict] = []

    if not consensus_rows.empty:
        value_sums = consensus_rows.groupby("consensus_value")[sample_columns].sum()
        for value, sums in value_sums.iterrows():
            rows.append(_make_matrix_row(trait, "consensus", value, sums))

    rows.append(_make_no_majority_row(trait, no_majority_sum))

    return rows


def _compute_unclassified_sum(
    profile: pd.DataFrame,
    sample_columns: list[str],
    zero_values: pd.Series,
) -> pd.Series:
    unclassified_sum = profile.loc[profile["taxon_id"] == -1, sample_columns].sum()
    return unclassified_sum if not unclassified_sum.empty else zero_values


def _compute_unannotated_sum(
    merged_rows: pd.DataFrame,
    profile: pd.DataFrame,
    sample_columns: list[str],
    zero_values: pd.Series,
) -> pd.Series:
    annotated_tax_ids = set(merged_rows["taxon_id"])
    unannotated_mask = (~profile["taxon_id"].isin(annotated_tax_ids)) & (
        profile["taxon_id"] != -1
    )
    unannotated_sum = profile.loc[unannotated_mask, sample_columns].sum()
    return unannotated_sum if not unannotated_sum.empty else zero_values


def _compute_no_majority_sum(
    merged_rows: pd.DataFrame,
    sample_columns: list[str],
    zero_values: pd.Series,
) -> pd.Series:
    no_majority_sum = merged_rows.loc[
        ~merged_rows["is_consensus"], sample_columns
    ].sum()
    return no_majority_sum if not no_majority_sum.empty else zero_values


def _build_sample_matrix(
    trait_summary: pd.DataFrame, profile: pd.DataFrame
) -> pd.DataFrame:
    sample_columns = list(profile.columns[1:])
    base_columns = [
        "trait",
        "annotation_status",
        "value",
    ]

    zero_values = pd.Series(0.0, index=sample_columns, dtype=float)

    unclassified_sum = _compute_unclassified_sum(profile, sample_columns, zero_values)

    merged = trait_summary.merge(profile, on="taxon_id", how="left")
    # TODO: Check if this is needed
    merged[sample_columns] = merged[sample_columns].fillna(0.0)
    grouped = merged.groupby("trait", sort=False)

    matrix_rows: list[dict] = []

    for trait, merged_rows in grouped:
        value_type = merged_rows["value_type"].iat[0]

        unannotated_sum = _compute_unannotated_sum(
            merged_rows, profile, sample_columns, zero_values
        )
        no_majority_sum = _compute_no_majority_sum(
            merged_rows, sample_columns, zero_values
        )

        consensus_rows = merged_rows.loc[merged_rows["is_consensus"]]
        if value_type == "boolean":
            matrix_rows.extend(
                _build_boolean_rows(
                    trait,
                    sample_columns,
                    zero_values,
                    consensus_rows,
                    no_majority_sum,
                )
            )
        elif value_type == "factor":
            matrix_rows.extend(
                _build_factor_rows(
                    trait,
                    sample_columns,
                    consensus_rows,
                    no_majority_sum,
                )
            )
        elif value_type == "numeric":
            matrix_rows.extend(
                _build_numeric_rows(trait, sample_columns, consensus_rows)
            )
        else:
            logger.error(f"Invalid value type: {value_type}")

        matrix_rows.append(
            _make_matrix_row(trait, "unannotated", None, unannotated_sum)
        )
        matrix_rows.append(
            _make_matrix_row(trait, "unclassified", None, unclassified_sum)
        )

    matrix_df = pd.DataFrame(matrix_rows)

    matrix_df = matrix_df.reindex(columns=base_columns + sample_columns)
    return matrix_df


def create_community_summary(
    trait_summary: pd.DataFrame,
    profile: pd.DataFrame,
) -> pd.DataFrame:
    processed_trait_summary = _prepare_trait_summary(trait_summary)
    sample_matrix = _build_sample_matrix(processed_trait_summary, profile)

    return sample_matrix
