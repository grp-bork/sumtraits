#!/usr/bin/env bash
set -euo pipefail

taxonomic_profile="/home/robbani/embl/sumtraits/test_data/metaphlan4_default.txt"
taxonomic_profile_type="metaphlan"
taxonomy_type="ncbi"

PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}" python -m sumtraits.cli \
    "$taxonomic_profile" \
    --taxonomic-profile-type "$taxonomic_profile_type" \
    --taxonomy-type "$taxonomy_type" \
    --exclude-prediction-based
