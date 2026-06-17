from pathlib import Path

import pandas as pd

from taxonomic_profile_translator import factory
from taxonomic_profile_translator.enums import ProfileType, Taxonomy
from taxonomic_profile_translator.errors import TranslationError


def _get_profile_with_smallest_rank(
    rank_to_translation: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    lengths = set()
    for rank in ["species", "genus", "family"]:
        profile = rank_to_translation.get(rank)
        # skip missing profiles
        if profile is None:
            continue
        # skip profiles wit only -1 values
        lengths.add(profile.shape[0])
        if profile.shape[0] == 1:
            continue
        return profile
    # If all ranks have 1 value, just return species
    if lengths == {1} and rank_to_translation.get("species") is not None:
        return rank_to_translation["species"]
    raise TranslationError("No results found for family, genus or species.")


def _get_tax_ids(profile: pd.DataFrame) -> set[int]:
    tax_ids = profile.index
    tax_ids = tax_ids[tax_ids != "NA"]
    tax_ids = {int(id) for id in tax_ids}
    return tax_ids


def translate_profile(
    file_path: Path,
    taxonomic_profile_type: str,
    taxonomy_type: str,
) -> tuple[set[int], pd.DataFrame]:
    """
    Use the taxonomic profile translator to convert to tax IDs.
    Also return the species level profile
    """
    profile_type = ProfileType(taxonomic_profile_type)
    translate_to = Taxonomy[taxonomy_type.upper()]

    profile = factory.ProfileFactory.create(
        file_path=str(file_path),
        profile_type=profile_type,
        translate_to=translate_to,
    )
    rank_to_translation = profile.process()
    profile_with_smallest_rank = _get_profile_with_smallest_rank(rank_to_translation)
    tax_ids = _get_tax_ids(profile_with_smallest_rank)
    return tax_ids, profile_with_smallest_rank
