"""Shared configuration for the sumtraits command-line interface."""

from enum import StrEnum


class TaxonomyType(StrEnum):
    """Supported target taxonomies."""

    NCBI = "ncbi"
    GTDB = "gtdb"


class TaxonomicProfileType(StrEnum):
    """Supported taxonomic profile formats."""

    MOTUS = "motus"
    METAPHLAN = "metaphlan"
    KRAKEN2 = "kraken2"
    KRAKENUNIQ = "krakenuniq"
    BRACKEN = "bracken"
    KAIJU = "kaiju"
    GENERIC_NCBI = "generic_ncbi"
    GENERIC_GTDB = "generic_gtdb"
