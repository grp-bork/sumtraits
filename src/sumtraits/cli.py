"""Command-line entry point for sumtraits."""

import argparse
import logging

from sumtraits.config import TaxonomicProfileType, TaxonomyType


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(funcName)s | %(lineno)d | %(message)s",
        force=True,
    )


def _run_workflow(
    taxonomic_profile: str,
    taxonomic_profile_type: str,
    taxonomy_type: str,
    reference_data_dir: str,
    exclude_prediction_based: bool,
    output_dir: str,
) -> int:
    from sumtraits.workflow import run

    return run(
        taxonomic_profile,
        taxonomic_profile_type,
        taxonomy_type,
        reference_data_dir,
        exclude_prediction_based,
        output_dir,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="sumtraits",
        description="Summarize traits from a taxonomic profile.",
    )
    parser.add_argument(
        "--input-taxonomic-profile",
        dest="taxonomic_profile",
        required=True,
        type=str,
        help="Path to the input taxonomic profile file.",
    )
    parser.add_argument(
        "--taxonomic-profile-type",
        required=True,
        choices=[profile_type.value for profile_type in TaxonomicProfileType],
        help="Type of the input taxonomic profile file.",
    )
    parser.add_argument(
        "--taxonomy-type",
        required=True,
        choices=[taxonomy_type.value for taxonomy_type in TaxonomyType],
        help="Target taxonomy to use.",
    )
    parser.add_argument(
        "--summtraits-reference-data-dir",
        dest="reference_data_dir",
        required=True,
        help="Directory containing sumtraits reference data files.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where the output tarball will be written.",
    )
    parser.add_argument(
        "--exclude-prediction-based",
        action="store_true",
        help="Exclude prediction-based trait summaries. They are included by default.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse command-line arguments and run sumtraits."""
    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.verbose)
    try:
        return _run_workflow(
            args.taxonomic_profile,
            args.taxonomic_profile_type,
            args.taxonomy_type,
            args.reference_data_dir,
            args.exclude_prediction_based,
            args.output_dir,
        )
    except Exception as error:
        logger = logging.getLogger(__name__)
        if args.verbose:
            logger.exception("sumtraits failed: %s", error)
        else:
            logger.error("sumtraits failed: %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
