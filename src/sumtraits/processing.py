import csv
from pathlib import Path

import pandas as pd

from sumtraits.config import REFERENCE_DATA_DIR, RANKS


def _get_summary_path(
    taxonomy_type: str,
    rank: str,
    exclude_prediction_based: bool,
) -> Path:
    prediction_tag = "no_predictions" if exclude_prediction_based else "all"
    return REFERENCE_DATA_DIR / f"{taxonomy_type}_{rank}_summary_{prediction_tag}.tsv"


def _get_summary_header(
    taxonomy_type: str,
    exclude_prediction_based: bool,
) -> list[str]:
    with _get_summary_path(taxonomy_type, RANKS[0], exclude_prediction_based).open(
        newline=""
    ) as f:
        return next(csv.reader(f, delimiter="\t"))


def get_trait_summary(
    tax_ids: set[int],
    taxonomy_type: str,
    exclude_prediction_based: bool,
) -> pd.DataFrame:
    "Fetch summary data"
    taxonomy_type = taxonomy_type.lower()
    columns = _get_summary_header(taxonomy_type, exclude_prediction_based)

    target_ids = {str(tax_id) for tax_id in tax_ids}
    seen_ids = set()
    summary_data = []
    for rank in RANKS:
        data_path = _get_summary_path(taxonomy_type, rank, exclude_prediction_based)
        with data_path.open(newline="") as f:
            reader = csv.reader(f, delimiter="\t")
            next(reader)  # skip header
            for row in reader:
                tax_id = row[0]
                if tax_id in target_ids:
                    summary_data.append(row)
                    seen_ids.add(tax_id)
                elif seen_ids == target_ids:
                    break

        if seen_ids == target_ids:
            break

    return pd.DataFrame(summary_data, columns=columns)
