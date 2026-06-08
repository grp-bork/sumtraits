from sumtraits.translate import translate_profile


def run(
    taxonomic_profile: str,
    taxonomic_profile_type: str,
    taxonomy_type: str,
    exclude_prediction_based: bool,
) -> int:
    """Run the current placeholder command."""

    print("sumtraits CLI test run")
    print(f"taxonomic_profile: {taxonomic_profile}")
    print(f"taxonomic_profile_type: {taxonomic_profile_type}")
    print(f"taxonomy_type: {taxonomy_type}")
    print(f"exclude_prediction_based: {exclude_prediction_based}")

    tax_ids, translated_profile = translate_profile(
        taxonomic_profile,
        taxonomic_profile_type,
        taxonomy_type,
    )
    print(tax_ids)

    return 0
