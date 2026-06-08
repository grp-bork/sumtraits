from pathlib import Path
from sumtraits.config import TaxonomicProfileType, TaxonomyType


def run(
    taxonomic_profile: Path,
    taxonomic_profile_type: TaxonomicProfileType,
    taxonomy_type: TaxonomyType,
    exclude_prediction_based: bool,
) -> int:
    """Run the current placeholder command."""

    print("sumtraits CLI test run")
    print(f"taxonomic_profile: {taxonomic_profile}")
    print(f"taxonomic_profile_type: {taxonomic_profile_type}")
    print(f"taxonomy_type: {taxonomy_type}")
    print(f"exclude_prediction_based: {exclude_prediction_based}")

    return 0
