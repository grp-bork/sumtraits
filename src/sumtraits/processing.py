from pathlib import Path
import io
import tarfile

import pandas as pd


def _get_summary_path(
    reference_data_dir: str | Path,
    taxonomy_type: str,
    exclude_prediction_based: bool,
) -> Path:
    prediction_tag = "no_predictions" if exclude_prediction_based else "all"
    return Path(reference_data_dir) / f"{taxonomy_type}_{prediction_tag}.tsv"


def get_trait_summary(
    tax_ids: set[int],
    taxonomy_type: str,
    reference_data_dir: str | Path,
    exclude_prediction_based: bool,
) -> pd.DataFrame:
    "Fetch summary data"
    taxonomy_type = taxonomy_type.lower()

    data_path = _get_summary_path(
        reference_data_dir,
        taxonomy_type,
        exclude_prediction_based,
    )
    trait_summary = pd.read_csv(data_path, sep="\t")
    return trait_summary[trait_summary["taxon_id"].isin(tax_ids)]

def normalize_profile(profile: pd.DataFrame) -> pd.DataFrame:
    normalized = profile.rename_axis("taxon_id").reset_index()
    normalized["taxon_id"] = normalized["taxon_id"].astype("int64")
    return normalized

def _add_bytes_to_tar(tar: tarfile.TarFile, name: str, data: bytes) -> None:
    info = tarfile.TarInfo(name=name)
    info.size = len(data)
    tar.addfile(info, io.BytesIO(data))


def write_output_archive(
    output_dir: str,
    taxonomic_profile: str,
    taxonomy_type: str,
    normalized_profile,
    trait_summary,
    community_summary,
) -> Path:
    taxonomic_profile_path = Path(taxonomic_profile)
    input_file_basename = taxonomic_profile_path.stem

    output_dir_path = Path(output_dir)
    if output_dir_path.exists() and not output_dir_path.is_dir():
        raise NotADirectoryError(f"Output path is not a directory: {output_dir_path}")
    output_dir_path.mkdir(parents=True, exist_ok=True)

    archive_path = (
        output_dir_path
        / f"{input_file_basename}_summary_{taxonomy_type}.tar.gz"
    )

    with tarfile.open(archive_path, mode="w:gz") as tar:
        _add_bytes_to_tar(
            tar,
            f"{input_file_basename}.{taxonomy_type}.tsv",
            normalized_profile.to_csv(sep="\t", index=False).encode("utf-8"),
        )
        _add_bytes_to_tar(
            tar,
            "taxon_trait_annotations.tsv",
            trait_summary.to_csv(sep="\t", index=False).encode("utf-8"),
        )
        _add_bytes_to_tar(
            tar,
            "community_trait_annotations.tsv",
            community_summary.to_csv(sep="\t", index=False).encode("utf-8"),
        )
        tar.add(taxonomic_profile_path, arcname=taxonomic_profile_path.name)

    return archive_path
