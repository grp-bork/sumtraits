# metatraits/web/profile_annotation/processing.py

import re
import pandas as pd
import numpy as np
from pandas._typing import Scalar

import logging

logger = logging.getLogger(__name__)


def _slugify(text: Scalar) -> str:
    slug = re.sub(r"[^0-9A-Za-z]+", "_", str(text).strip().lower())
    return slug.strip("_") or "value"


def _make_matrix_row(
    trait: Scalar,
    feature_slug: str,
    state: str,
    summary_type: str,
    sample_columns: list[str],
    values: pd.Series,
    *,
    fill_value: float | None = 0.0,
) -> dict:
    aligned = values.reindex(sample_columns)
    if fill_value is not None:
        aligned = aligned.fillna(fill_value)

    feature_state_value = f"{feature_slug}.{state}"
    row = {
        "trait": trait,
        "feature": feature_state_value,
        "summary_type": summary_type,
    }

    for column in sample_columns:
        val = aligned[column]
        row[column] = None if pd.isna(val) else float(val)

    return row


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


def _build_boolean_rows(
    trait: Scalar,
    feature_slug: str,
    sample_columns: list[str],
    zero_values: pd.Series,
    consensus_rows: pd.DataFrame,
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
        _make_matrix_row(
            trait, feature_slug, "true", "consensus_true", sample_columns, true_sum
        ),
        _make_matrix_row(
            trait, feature_slug, "false", "consensus_false", sample_columns, false_sum
        ),
    ]


def _build_numeric_rows(
    trait: Scalar,
    feature_slug: str,
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
            feature_slug,
            "mean",
            "numeric_mean",
            sample_columns,
            mean_values,
            fill_value=None,
        )
    ]


def _build_factor_rows(
    trait: Scalar,
    feature_slug: str,
    sample_columns: list[str],
    zero_values: pd.Series,
    consensus_rows: pd.DataFrame,
) -> list[dict]:
    if not consensus_rows.empty:
        totals = consensus_rows[sample_columns].sum(axis=1)
        value_totals = (
            pd.DataFrame({"value": consensus_rows["consensus_value"], "total": totals})
            .groupby("value")["total"]
            .sum()
            .sort_values(ascending=False)
        )
    else:
        value_totals = pd.Series(dtype=float)

    if not value_totals.empty:
        majority_value = value_totals.index[0]
        majority_mask = consensus_rows["consensus_value"] == majority_value
        majority_sum = consensus_rows.loc[majority_mask, sample_columns].sum()
        other_sum = consensus_rows.loc[~majority_mask, sample_columns].sum()
    else:
        majority_value = None
        majority_sum = zero_values
        other_sum = zero_values

    state_slug = _slugify(majority_value) if majority_value is not None else "majority"

    return [
        _make_matrix_row(
            trait,
            feature_slug,
            state_slug,
            "consensus_majority",
            sample_columns,
            majority_sum,
        ),
        _make_matrix_row(
            trait,
            feature_slug,
            "other",
            "consensus_other",
            sample_columns,
            other_sum if not other_sum.empty else zero_values,
        ),
    ]


def _build_sample_matrix(
    trait_summary: pd.DataFrame, profile: pd.DataFrame
) -> pd.DataFrame:
    sample_columns = list(profile.columns[1:])
    base_columns = [
        "trait",
        "summary_type",
        "feature",
    ]

    zero_values = pd.Series(0.0, index=sample_columns, dtype=float)

    matrix_rows: list[dict] = []

    # TODO: figure out how to group the unclassified code
    unclassified_sum = profile.loc[profile["taxon_id"] == -1, sample_columns].sum()
    if unclassified_sum.empty:
        unclassified_sum = zero_values

    merged = trait_summary.merge(profile, on="taxon_id", how="left")
    # TODO: Check if this is needed
    merged[sample_columns] = merged[sample_columns].fillna(0.0)

    grouped = merged.groupby("trait", sort=False)

    for trait, merged_rows in grouped:
        # TODO: remove this later since we'll exclude the column form the output
        feature_slug = _slugify(trait)
        value_type = merged_rows["value_type"].iat[0]

        # Unannotated sum
        annotated_tax_ids = set(merged_rows["taxon_id"])
        unannotated_mask = (~profile["taxon_id"].isin(annotated_tax_ids)) & (
            profile["taxon_id"] != -1
        )
        unannotated_sum = profile.loc[unannotated_mask, sample_columns].sum()
        if unannotated_sum.empty:
            unannotated_sum = zero_values

        # No majority sum
        no_majority_sum = merged_rows.loc[
            ~merged_rows["is_consensus"], sample_columns
        ].sum()
        if no_majority_sum.empty:
            no_majority_sum = zero_values

        consensus_rows = merged_rows.loc[merged_rows["is_consensus"]]
        if value_type == "boolean":
            matrix_rows.extend(
                _build_boolean_rows(
                    trait, feature_slug, sample_columns, zero_values, consensus_rows
                )
            )
        elif value_type == "numeric":
            matrix_rows.extend(
                _build_numeric_rows(trait, feature_slug, sample_columns, consensus_rows)
            )
        else:
            matrix_rows.extend(
                _build_factor_rows(
                    trait, feature_slug, sample_columns, zero_values, consensus_rows
                )
            )

        if value_type != "numeric":
            matrix_rows.append(
                _make_matrix_row(
                    trait,
                    feature_slug,
                    "no_majority",
                    "no_majority",
                    sample_columns,
                    no_majority_sum,
                )
            )
        matrix_rows.append(
            _make_matrix_row(
                trait,
                feature_slug,
                "unannotated",
                "unannotated",
                sample_columns,
                unannotated_sum,
            )
        )
        matrix_rows.append(
            _make_matrix_row(
                trait,
                feature_slug,
                "unclassified",
                "unclassified",
                sample_columns,
                unclassified_sum,
            )
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
