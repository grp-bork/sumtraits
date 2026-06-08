"""Command-line entry point for sumtraits."""

from __future__ import annotations

import argparse
from pathlib import Path

from sumtraits.config import TaxonomicProfileType, TaxonomyType


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="sumtraits",
        description="Summarize traits from a taxonomic profile.",
    )
    parser.add_argument(
        "taxonomic_profile",
        type=Path,
        help="Path to the taxonomic profile file.",
    )
    parser.add_argument(
        "--taxonomic-profile-type",
        required=True,
        choices=[profile_type.value for profile_type in TaxonomicProfileType],
        help="Type of taxonomic profile parser to use.",
    )
    parser.add_argument(
        "--taxonomy-type",
        required=True,
        choices=[taxonomy_type.value for taxonomy_type in TaxonomyType],
        help="Target taxonomy to use.",
    )
    parser.add_argument(
        "--exclude-prediction-based",
        action="store_true",
        help="Exclude prediction-based trait summaries. They are included by default.",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    """Run the current placeholder command."""

    print("sumtraits CLI test run")
    print(f"taxonomic_profile: {args.taxonomic_profile}")
    print(f"taxonomic_profile_type: {args.taxonomic_profile_type}")
    print(f"taxonomy_type: {args.taxonomy_type}")
    print(f"exclude_prediction_based: {args.exclude_prediction_based}")

    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse command-line arguments and run sumtraits."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
