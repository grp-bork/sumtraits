import logging

from sumtraits.translate import translate_profile
from sumtraits.processing import get_trait_summary

logger = logging.getLogger(__name__)


def run(
    taxonomic_profile: str,
    taxonomic_profile_type: str,
    taxonomy_type: str,
    exclude_prediction_based: bool,
) -> int:
    """Run the sumtraits workflow."""

    logger.info("Starting sumtraits")

    tax_ids, translated_profile = translate_profile(
        taxonomic_profile,
        taxonomic_profile_type,
        taxonomy_type,
    )

    if not tax_ids:
        logger.error(f"No {taxonomy_type} tax ids found after translating the taxonomic profile. Exiting...")
        return 1
    
    logger.info("Tax IDs identified: %d", len(tax_ids))

    trait_summary = get_trait_summary(tax_ids, taxonomy_type, exclude_prediction_based)
    if trait_summary.empty:
        logger.error("No trait summary rows found for tax IDs. Exiting...")
        return 1

    logger.info("Trait summary rows: %d", trait_summary.shape[0])

    return 0
