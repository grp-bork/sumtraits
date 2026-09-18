"""Command-line entry point for building reference data indexes."""

import argparse
import logging
from pathlib import Path

from taxonomic_profile_translator.enums import Taxonomy

from sumtraits import reference_index
from sumtraits.cli import _configure_logging
from sumtraits.processing import _get_summary_path

logger = logging.getLogger(__name__)


def _reference_files(reference_data_dir: Path) -> list[Path]:
    """List the reference files `get_trait_summary` can ask for, in a stable order."""
    return [
        _get_summary_path(reference_data_dir, taxonomy.value.lower(), exclude)
        for taxonomy in Taxonomy
        for exclude in (False, True)
    ]


def _needs_index(reference_path: Path) -> bool:
    try:
        reference_index.load_index(reference_path)
    except (FileNotFoundError, ValueError):
        return True
    return False


def _build_indexes(reference_data_dir: Path, force: bool) -> int:
    reference_paths = [
        path for path in _reference_files(reference_data_dir) if path.is_file()
    ]

    if not reference_paths:
        logger.error("No reference data files found in %s", reference_data_dir)
        return 1

    for reference_path in reference_paths:
        if not force and not _needs_index(reference_path):
            logger.info("Index is already up to date: %s", reference_path.name)
            continue

        logger.info("Indexing %s", reference_path.name)
        reference_index.build_index(reference_path)

    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="sumtraits-index",
        description="Build byte-offset indexes for sumtraits reference data files.",
    )
    parser.add_argument(
        "--sumtraits-reference-data-dir",
        dest="reference_data_dir",
        required=True,
        type=Path,
        help="Directory containing sumtraits reference data files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild indexes even if they are already up to date.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse command-line arguments and build the reference data indexes."""
    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.verbose)
    try:
        return _build_indexes(args.reference_data_dir, args.force)
    except Exception as error:
        if args.verbose:
            logger.exception("sumtraits-index failed: %s", error)
        else:
            logger.error("sumtraits-index failed: %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
