# metatraits/web/profile_annotation/processing.py

import re
import pandas as pd
import numpy as np

import logging

logger = logging.getLogger(__name__)


ANNOTATED_STATUSES = {"consensus", "no_robust_majority"}


def _slugify(text: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z]+", "_", str(text).strip().lower())
    return slug.strip("_") or "value"


def _make_matrix_row(
    trait: str,
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

# TODO: remove after updating _build_sample_matrix 
def _build_consolidated_table(summary_df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "taxon_id",
        "trait",
        "value_type",
        "consensus_value",
        "consensus_bool",
        "consensus_numeric_value",
        "support_count",
        "support_percentage",
        "total_evidence",
        "source_databases",
        "databases",
        "status",
    ]
    summary_df = summary_df.rename(
        columns={
            "trait_name": "trait",
            "mean": "consensus_numeric_value",
            "consensus_count": "support_count",
            "consensus_percentage": "support_percentage",
            "total_observations": "total_evidence",
            "database_count": "source_databases",
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
    summary_df["status"] = np.where(
        summary_df["consensus_value"] == "No robust majority",
        "no_robust_majority",
        "consensus",
    )
    summary_df = summary_df.sort_values(["taxon_id", "trait"]).reset_index(drop=True)

    return summary_df


def _zero_series(columns: list[str]) -> pd.Series:
    return pd.Series(0.0, index=columns, dtype=float)


# TODO refactor to make this more readable
def _build_sample_matrix(
    consolidated: pd.DataFrame, profile: pd.DataFrame
) -> pd.DataFrame:
    abundance = profile
    sample_columns = list(profile.columns[1:])
    base_columns = [
        "trait",
        "summary_type",
        "feature",
    ]

    if consolidated.empty:
        return pd.DataFrame(columns=base_columns + sample_columns)
    zero_values = _zero_series(sample_columns)
    matrix_rows: list[dict] = []
    # TODO: profile.index should be used instead of abundance["taxon_id"]
    unclassified_sum = abundance.loc[abundance["taxon_id"] == -1, sample_columns].sum()
    if unclassified_sum.empty:
        unclassified_sum = zero_values.copy()

    grouped = consolidated.groupby("trait", sort=False)

    for trait, trait_rows in grouped:
        feature_slug = _slugify(trait)
        value_type_candidates = trait_rows["value_type"].dropna().unique()
        value_type = (
            value_type_candidates[0] if len(value_type_candidates) else "factor"
        )
        # TODO: trait_rows.taxon_id should be merged with profile.index
        merged = trait_rows.merge(abundance, on="taxon_id", how="left")
        # TODO: This is impossible. tax ids are used to query the database
        # There can be tax ids with no traits but every trait
        # must have a tax id
        for column in sample_columns:
            merged[column] = merged[column].fillna(0.0)

        # TODO: The only unannotated rows are profile.index = -1
        # Unannotated sum
        annotated_tax_ids = set(
            merged.loc[merged["status"].isin(ANNOTATED_STATUSES), "taxon_id"]
        )
        unannotated_mask = (~abundance["taxon_id"].isin(annotated_tax_ids)) & (
            abundance["taxon_id"] != -1
        )
        unannotated_sum = abundance.loc[unannotated_mask, sample_columns].sum()
        if unannotated_sum.empty:
            unannotated_sum = zero_values.copy()

        # No majority sum
        no_majority_sum = merged.loc[
            merged["status"] == "no_robust_majority", sample_columns
        ].sum()
        if no_majority_sum.empty:
            no_majority_sum = zero_values.copy()

        consensus_rows = merged.loc[merged["status"] == "consensus"].copy()
        # TODO: break into smaller helper functions
        if value_type == "boolean":
            true_sum = consensus_rows.loc[
                consensus_rows["consensus_bool"] == True, sample_columns
            ].sum()
            false_sum = consensus_rows.loc[
                consensus_rows["consensus_bool"] == False, sample_columns
            ].sum()
            if true_sum.empty:
                true_sum = zero_values.copy()
            if false_sum.empty:
                false_sum = zero_values.copy()

            matrix_rows.append(
                _make_matrix_row(
                    trait,
                    feature_slug,
                    "true",
                    "consensus_true",
                    sample_columns,
                    true_sum,
                )
            )
            matrix_rows.append(
                _make_matrix_row(
                    trait,
                    feature_slug,
                    "false",
                    "consensus_false",
                    sample_columns,
                    false_sum,
                )
            )
        elif value_type == "numeric":
            numeric_rows = consensus_rows.loc[
                consensus_rows["consensus_numeric_value"].notna()
            ].copy()
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

            matrix_rows.append(
                _make_matrix_row(
                    trait,
                    feature_slug,
                    "mean",
                    "numeric_mean",
                    sample_columns,
                    mean_values,
                    fill_value=None,
                )
            )
        else:
            if not consensus_rows.empty:
                totals = consensus_rows[sample_columns].sum(axis=1)
                value_totals = (
                    pd.DataFrame(
                        {"value": consensus_rows["consensus_value"], "total": totals}
                    )
                    .groupby("value")["total"]
                    .sum()
                    .sort_values(ascending=False)
                )
                if not value_totals.empty:
                    majority_value = value_totals.index[0]
                    majority_mask = consensus_rows["consensus_value"] == majority_value
                    majority_sum = consensus_rows.loc[
                        majority_mask, sample_columns
                    ].sum()
                    other_sum = consensus_rows.loc[~majority_mask, sample_columns].sum()
                else:
                    majority_value = None
                    majority_sum = zero_values.copy()
                    other_sum = zero_values.copy()
            else:
                majority_value = None
                majority_sum = zero_values.copy()
                other_sum = zero_values.copy()

            state_slug = (
                _slugify(majority_value) if majority_value is not None else "majority"
            )

            matrix_rows.append(
                _make_matrix_row(
                    trait,
                    feature_slug,
                    state_slug,
                    "consensus_majority",
                    sample_columns,
                    majority_sum,
                )
            )
            matrix_rows.append(
                _make_matrix_row(
                    trait,
                    feature_slug,
                    "other",
                    "consensus_other",
                    sample_columns,
                    other_sum if not other_sum.empty else zero_values,
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
    consolidated = _build_consolidated_table(trait_summary)
    sample_matrix = _build_sample_matrix(consolidated, profile)

    return sample_matrix
