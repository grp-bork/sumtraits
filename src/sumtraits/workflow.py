import logging

from sumtraits.translate import translate_profile
from sumtraits.processing import (
    get_trait_summary,
    normalize_profile,
    write_output_archive,
)
from sumtraits.community import create_community_summary

logger = logging.getLogger(__name__)


def run(
    taxonomic_profile: str,
    taxonomic_profile_type: str,
    taxonomy_type: str,
    exclude_prediction_based: bool,
    output_dir: str,
) -> int:
    """Run the sumtraits workflow."""

    logger.info("Starting sumtraits")

    tax_ids, translated_profile = translate_profile(
        taxonomic_profile,
        taxonomic_profile_type,
        taxonomy_type,
    )

    normalized_profile = normalize_profile(translated_profile)

    if not tax_ids:
        logger.error(
            f"No {taxonomy_type} tax ids found after translating the taxonomic profile. Exiting..."
        )
        return 1

    logger.info("Tax IDs identified: %d", len(tax_ids))

    trait_summary = get_trait_summary(tax_ids, taxonomy_type, exclude_prediction_based)
    if trait_summary.empty:
        logger.error("No trait summary rows found for tax IDs. Exiting...")
        return 1

    logger.info("Trait summary rows: %d", trait_summary.shape[0])

    community_summary = create_community_summary(trait_summary, normalized_profile)

    logger.info("Created community summary file")

    archive_path = write_output_archive(
        output_dir,
        taxonomic_profile,
        taxonomy_type,
        normalized_profile,
        trait_summary,
        community_summary,
    )
    logger.info("Wrote output archive: %s", archive_path)

    return 0
