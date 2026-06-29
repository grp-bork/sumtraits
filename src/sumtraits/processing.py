import io
import shutil
from pathlib import Path

import pandas as pd


def _get_summary_path(
    reference_data_dir: Path,
    taxonomy_type: str,
    exclude_prediction_based: bool,
) -> Path:
    prediction_tag = "no_predictions" if exclude_prediction_based else "all"
    return reference_data_dir / f"{taxonomy_type}_{prediction_tag}.tsv"


def _read_tsv_filtered_by_taxon_id(data_path: Path, tax_ids: set[int]) -> pd.DataFrame:
    """Read a TSV, keeping only rows whose first column matches a tax id.

    Reference data files can have millions of rows while a profile only
    needs a few hundred tax ids, so the matching rows are selected as plain
    text before handing them to pandas. This avoids paying pandas' parsing
    cost for rows that would just be filtered out anyway.
    """
    tax_id_strs = {str(tax_id) for tax_id in tax_ids}

    matching_lines = []
    with open(data_path, "r") as f:
        matching_lines.append(f.readline())
        for line in f:
            taxon_id_str = line[: line.find("\t")]
            if taxon_id_str in tax_id_strs:
                matching_lines.append(line)

    return pd.read_csv(io.StringIO("".join(matching_lines)), sep="\t")


def get_trait_summary(
    tax_ids: set[int],
    taxonomy_type: str,
    reference_data_dir: Path,
    exclude_prediction_based: bool,
) -> pd.DataFrame:
    "Fetch summary data"
    taxonomy_type = taxonomy_type.lower()

    data_path = _get_summary_path(
        reference_data_dir,
        taxonomy_type,
        exclude_prediction_based,
    )
    return _read_tsv_filtered_by_taxon_id(data_path, tax_ids)


def normalize_profile(profile: pd.DataFrame) -> pd.DataFrame:
    normalized = profile.rename_axis("taxon_id").reset_index()
    normalized["taxon_id"] = normalized["taxon_id"].astype("int64")
    return normalized


def _copy_input_profile(taxonomic_profile: Path, destination: Path) -> None:
    profile_source = (
        taxonomic_profile.resolve(strict=True)
        if taxonomic_profile.is_symlink()
        else taxonomic_profile
    )
    shutil.copyfile(profile_source, destination)


def write_output_files(
    output_dir: Path,
    taxonomic_profile: Path,
    taxonomy_type: str,
    normalized_profile: pd.DataFrame,
    trait_summary: pd.DataFrame,
    community_summary: pd.DataFrame,
) -> None:
    input_file_basename = taxonomic_profile.stem

    if output_dir.exists() and not output_dir.is_dir():
        raise NotADirectoryError(f"Output path is not a directory: {output_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    normalized_profile.to_csv(
        output_dir / f"{input_file_basename}.{taxonomy_type}.tsv",
        sep="\t",
        index=False,
    )
    trait_summary.to_csv(
        output_dir / "taxon_trait_annotations.tsv", sep="\t", index=False
    )
    community_summary.to_csv(
        output_dir / "community_trait_annotations.tsv", sep="\t", index=False
    )
    _copy_input_profile(taxonomic_profile, output_dir / taxonomic_profile.name)
