from pathlib import Path

import pandas as pd

from sumtraits.config import REFERENCE_DATA_DIR


def _get_summary_path(
    taxonomy_type: str,
    rank: str,
    exclude_prediction_based: bool,
) -> Path:
    prediction_tag = "no_predictions" if exclude_prediction_based else "all"
    return REFERENCE_DATA_DIR / f"{taxonomy_type}_{prediction_tag}.tsv"


def get_trait_summary(
    tax_ids: set[int],
    taxonomy_type: str,
    exclude_prediction_based: bool,
) -> pd.DataFrame:
    "Fetch summary data"
    taxonomy_type = taxonomy_type.lower()

    data_path = _get_summary_path(taxonomy_type, "", exclude_prediction_based)
    trait_summary = pd.read_csv(data_path, sep="\t")
    return trait_summary[trait_summary["taxon_id"].isin(tax_ids)]

def normalize_profile(profile: pd.DataFrame) -> pd.DataFrame:
    normalized = profile.rename_axis("taxon_id").reset_index()
    normalized["taxon_id"] = normalized["taxon_id"].astype("int64", copy=False)
    return normalized
