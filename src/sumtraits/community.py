# metatraits/web/profile_annotation/processing.py

import io
import os
import re
import pandas as pd
import tarfile


from taxonomic_profile_translator.enums import ProfileType, Taxonomy

from typing import IO, Literal, Sequence

ROBUST_THRESHOLD = 0.85
BOOLEAN_TRUE_VALUES = {"true", "yes"}
BOOLEAN_FALSE_VALUES = {"false", "no"}
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


def _normalize_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    token = str(value).strip().lower()
    if token in BOOLEAN_TRUE_VALUES:
        return True
    if token in BOOLEAN_FALSE_VALUES:
        return False
    return None


def _infer_total_count(majority_count: int, majority_pct: float | None) -> int:
    if majority_pct and majority_pct > 0:
        inferred = int(round(majority_count / (majority_pct / 100.0)))
        return max(inferred, majority_count)
    return int(majority_count)


def _classify_trait(values: pd.Series) -> Literal["boolean", "numeric", "factor"]:
    cleaned = values.dropna()
    if cleaned.empty:
        return "factor"
    bool_flags = [_normalize_bool(v) for v in cleaned]
    if bool_flags and all(flag is not None for flag in bool_flags):
        return "boolean"
    numeric = pd.to_numeric(cleaned, errors="coerce")
    if numeric.notna().all():
        return "numeric"
    return "factor"


def _summarize_boolean(group: pd.DataFrame) -> dict:
    true_votes = 0
    false_votes = 0
    total_votes = 0

    for row in group.itertuples():
        majority_value = _normalize_bool(row.majority_value)
        if majority_value is None:
            continue
        majority_count = int(row.majority_count or 0)
        total_count = _infer_total_count(majority_count, row.majority_percentage)
        other_count = max(total_count - majority_count, 0)

        if majority_value:
            true_votes += majority_count
            false_votes += other_count
        else:
            false_votes += majority_count
            true_votes += other_count

        total_votes += total_count

    if total_votes == 0:
        return {
            "value_type": "boolean",
            "consensus_value": "No data",
            "consensus_bool": None,
            "consensus_numeric_value": None,
            "support_count": 0,
            "support_percentage": 0.0,
            "total_evidence": 0,
            "status": "no_data",
        }

    consensus_bool = true_votes >= false_votes
    support_count = true_votes if consensus_bool else false_votes
    support_pct = support_count / total_votes if total_votes else 0.0

    if support_pct < ROBUST_THRESHOLD:
        return {
            "value_type": "boolean",
            "consensus_value": "No robust majority",
            "consensus_bool": None,
            "consensus_numeric_value": None,
            "support_count": support_count,
            "support_percentage": support_pct * 100.0,
            "total_evidence": total_votes,
            "status": "no_robust_majority",
        }

    return {
        "value_type": "boolean",
        "consensus_value": "true" if consensus_bool else "false",
        "consensus_bool": consensus_bool,
        "consensus_numeric_value": None,
        "support_count": support_count,
        "support_percentage": support_pct * 100.0,
        "total_evidence": total_votes,
        "status": "consensus",
    }


def _summarize_non_boolean(group: pd.DataFrame, *, numeric: bool) -> dict:
    total_sources = group["database"].nunique()
    if total_sources == 0:
        return {
            "value_type": "numeric" if numeric else "factor",
            "consensus_value": "No data",
            "consensus_bool": None,
            "consensus_numeric_value": None,
            "support_count": 0,
            "support_percentage": 0.0,
            "total_evidence": 0,
            "status": "no_data",
        }

    if numeric:
        numeric_values = pd.to_numeric(group["majority_value"], errors="coerce")
        valid = numeric_values.notna()

        if not valid.any():
            return {
                "value_type": "numeric",
                "consensus_value": "No data",
                "consensus_bool": None,
                "consensus_numeric_value": None,
                "support_count": 0,
                "support_percentage": 0.0,
                "total_evidence": 0,
                "status": "no_data",
            }

        values = numeric_values[valid].astype(float)
        mean_value = float(values.mean())
        support_count = int(valid.sum())

        return {
            "value_type": "numeric",
            "consensus_value": mean_value,
            "consensus_bool": None,
            "consensus_numeric_value": mean_value,
            "support_count": support_count,
            "support_percentage": 100.0,
            "total_evidence": support_count,
            "status": "consensus",
        }

    counts: dict[str | float, int] = {}
    exemplars: dict[str | float, str | float] = {}

    for value in group["majority_value"]:
        if pd.isna(value):
            continue
        if numeric:
            coerced = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
            if pd.isna(coerced):
                continue
            key = round(float(coerced), 6)
            exemplar = float(coerced)
        else:
            key = str(value).strip()
            exemplar = str(value)
        counts[key] = counts.get(key, 0) + 1
        if key not in exemplars:
            exemplars[key] = exemplar

    if not counts:
        return {
            "value_type": "numeric" if numeric else "factor",
            "consensus_value": "No data",
            "consensus_bool": None,
            "consensus_numeric_value": None,
            "support_count": 0,
            "support_percentage": 0.0,
            "total_evidence": 0,
            "status": "no_data",
        }

    winning_key, support_count = max(
        counts.items(), key=lambda item: (item[1], item[0])
    )
    support_pct = support_count / total_sources

    if support_pct < ROBUST_THRESHOLD:
        return {
            "value_type": "numeric" if numeric else "factor",
            "consensus_value": "No robust majority",
            "consensus_bool": None,
            "consensus_numeric_value": None,
            "support_count": support_count,
            "support_percentage": support_pct * 100.0,
            "total_evidence": total_sources,
            "status": "no_robust_majority",
        }

    consensus_value = exemplars[winning_key]
    numeric_value = float(consensus_value) if numeric else None

    return {
        "value_type": "numeric" if numeric else "factor",
        "consensus_value": consensus_value,
        "consensus_bool": None,
        "consensus_numeric_value": numeric_value,
        "support_count": support_count,
        "support_percentage": support_pct * 100.0,
        "total_evidence": total_sources,
        "status": "consensus",
    }


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

    if summary_df.empty:
        return pd.DataFrame(columns=columns)

    records: list[dict] = []
    for (tax_id, feature), group in summary_df.groupby(
        ["tax_id", "feature"], sort=False
    ):
        trait_type = _classify_trait(group["majority_value"])

        if trait_type == "boolean":
            consensus = _summarize_boolean(group)
        elif trait_type == "numeric":
            consensus = _summarize_non_boolean(group, numeric=True)
        else:
            consensus = _summarize_non_boolean(group, numeric=False)

        record = {
            "taxon_id": int(tax_id),
            "trait": feature,
            "source_databases": group["database"].nunique(),
            "databases": ",".join(sorted(group["database"].unique())),
        }
        record.update(consensus)
        records.append(record)

    consolidated = (
        pd.DataFrame(records)
        .reindex(columns=columns)
        .sort_values(["taxon_id", "trait"])
        .reset_index(drop=True)
    )
    return consolidated


def _normalize_profile(
    profile: pd.DataFrame | pd.Series,
) -> tuple[pd.DataFrame, list[str]]:
    if isinstance(profile, pd.Series):
        abundance = profile.to_frame(name="abundance")
    else:
        abundance = profile.copy()

    if isinstance(abundance.columns, pd.MultiIndex):
        abundance.columns = [
            "_".join(str(level) for level in col if str(level))
            for col in abundance.columns
        ]
    else:
        abundance.columns = [str(c) for c in abundance.columns]

    abundance.index = pd.to_numeric(abundance.index, errors="coerce")
    abundance.index.name = "taxon_id"
    abundance.reset_index(inplace=True)

    if "index" in abundance.columns:
        abundance.rename(columns={"index": "taxon_id"}, inplace=True)
    if "tax_id" in abundance.columns:
        abundance.rename(columns={"tax_id": "taxon_id"}, inplace=True)
    if "taxon_id" not in abundance.columns:
        abundance.rename(columns={abundance.columns[0]: "taxon_id"}, inplace=True)

    sample_columns = [c for c in abundance.columns if c != "taxon_id"]
    for column in sample_columns:
        abundance[column] = pd.to_numeric(abundance[column], errors="coerce").fillna(
            0.0
        )

    return abundance, sample_columns


def _zero_series(columns: list[str]) -> pd.Series:
    return pd.Series(0.0, index=columns, dtype=float)


def _prepare_taxonomy_metadata(taxonomy_df: pd.DataFrame) -> pd.DataFrame:
    if taxonomy_df.empty:
        return taxonomy_df

    taxonomy_df = taxonomy_df.rename(columns={"tax_id": "taxon_id"})
    taxonomy_df = taxonomy_df.drop_duplicates(subset=["taxon_id"]).copy()

    if "taxon_lineage" in taxonomy_df.columns:
        taxonomy_df["taxon_lineage"] = taxonomy_df["taxon_lineage"].replace("", pd.NA)
    else:
        taxonomy_df["taxon_lineage"] = pd.NA

    if (
        "taxon_name" not in taxonomy_df.columns
        or taxonomy_df["taxon_name"].isna().all()
    ):
        taxonomy_df["taxon_name"] = (
            taxonomy_df["taxon_lineage"].fillna("").str.split("|").str[-1]
        )
        taxonomy_df.loc[taxonomy_df["taxon_lineage"].isna(), "taxon_name"] = pd.NA

    taxonomy_df = taxonomy_df[
        [
            col
            for col in ["taxon_id", "taxon_name", "taxon_lineage"]
            if col in taxonomy_df.columns
        ]
    ]

    return taxonomy_df


def _build_sample_matrix(
    consolidated: pd.DataFrame, profile: pd.DataFrame | pd.Series
) -> pd.DataFrame:
    # TODO: sample_columns should just be profile.columns
    # TODO: profile should be used instead of abundance
    abundance, sample_columns = _normalize_profile(profile)
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
        annotated_tax_ids = set(
            merged.loc[merged["status"].isin(ANNOTATED_STATUSES), "taxon_id"]
        )
        unannotated_mask = (~abundance["taxon_id"].isin(annotated_tax_ids)) & (
            abundance["taxon_id"] != -1
        )
        unannotated_sum = abundance.loc[unannotated_mask, sample_columns].sum()
        if unannotated_sum.empty:
            unannotated_sum = zero_values.copy()

        no_majority_sum = merged.loc[
            merged["status"] == "no_robust_majority", sample_columns
        ].sum()
        if no_majority_sum.empty:
            no_majority_sum = zero_values.copy()

        consensus_rows = merged.loc[merged["status"] == "consensus"].copy()

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
    if matrix_df.empty:
        return pd.DataFrame(columns=base_columns + sample_columns)

    matrix_df = matrix_df.reindex(columns=base_columns + sample_columns)
    return matrix_df


def _merge_taxonomy_metadata(
    df: pd.DataFrame, taxonomy_metadata: pd.DataFrame
) -> pd.DataFrame:
    if df.empty or taxonomy_metadata.empty:
        return df

    merged = df.merge(taxonomy_metadata, on="taxon_id", how="left")

    taxonomy_columns = [
        col for col in taxonomy_metadata.columns if col in merged.columns
    ]

    preferred = ["taxon_id"] + [col for col in taxonomy_columns if col != "taxon_id"]
    remaining = [col for col in merged.columns if col not in preferred]

    return merged[preferred + remaining]


def _add_bytes_to_tar(tar: tarfile.TarFile, name: str, data: bytes):
    info = tarfile.TarInfo(name=name)
    info.size = len(data)
    tar.addfile(info, io.BytesIO(data))


def _create_tar_gz_file(
    filename: str,
    taxonomy: str,
    file_bytes: bytes,
    consolidated: pd.DataFrame,
    sample_matrix: pd.DataFrame,
    parsed_profile_df: pd.DataFrame,
) -> io.BytesIO:
    output = io.BytesIO()

    with tarfile.open(fileobj=output, mode="w:gz") as tar:
        # Write TSVs
        consolidated_bytes = consolidated.to_csv(sep="\t", index=False).encode("utf-8")
        _add_bytes_to_tar(tar, "taxon_trait_annotations.tsv", consolidated_bytes)

        sample_bytes = sample_matrix.to_csv(sep="\t", index=False).encode("utf-8")
        _add_bytes_to_tar(tar, "community_trait_annotations.tsv", sample_bytes)

        # Raw input file
        raw_name = filename
        _add_bytes_to_tar(tar, raw_name, file_bytes)

        # Parsed profile
        base, ext = os.path.splitext(raw_name)
        if not ext:
            ext = ".txt"

        parsed_name = f"{base}.{taxonomy.upper()}{ext}"
        parsed_bytes = parsed_profile_df.to_csv(sep="\t", index=False).encode("utf-8")

        _add_bytes_to_tar(tar, parsed_name, parsed_bytes)

    output.seek(0)

    app.logger.info(
        "Generated annotation bundle for %d taxa across %d features.",
        consolidated["taxon_id"].nunique(),
        consolidated["trait"].nunique(),
    )

    return output


def create_output_file(
    file_bytes: bytes,
    taxonomy: Literal["ncbi", "gtdb"],
    filename: str,
    summary_results: Sequence,
    profile: pd.DataFrame,
    taxonomy_metadata_results: Sequence,
) -> io.BytesIO:
    """
    Combine tax_ids, taxonomy_metadata and summary results to create
    the final output
    """
    summary_df = pd.DataFrame([dict(row._mapping) for row in summary_results])

    consolidated = _build_consolidated_table(summary_df)

    sample_matrix = _build_sample_matrix(consolidated.copy(), profile)

    parsed_profile_df, _ = _normalize_profile(profile)

    taxonomy_metadata = _prepare_taxonomy_metadata(
        pd.DataFrame([dict(row._mapping) for row in taxonomy_metadata_results])
    )

    consolidated = _merge_taxonomy_metadata(consolidated, taxonomy_metadata)
    parsed_profile_df = _merge_taxonomy_metadata(parsed_profile_df, taxonomy_metadata)

    output = _create_tar_gz_file(
        filename, taxonomy, file_bytes, consolidated, sample_matrix, parsed_profile_df
    )
    return output


