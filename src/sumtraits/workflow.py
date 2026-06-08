import logging

from sumtraits.translate import translate_profile

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

    return 0
