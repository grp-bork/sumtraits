#!/usr/bin/env bash
set -euo pipefail

taxonomic_profile="/home/robbani/embl/sumtraits/test_data/metaphlan4_default.txt"
taxonomic_profile_type="metaphlan"
taxonomy_type="ncbi"
output_dir="/home/robbani/embl/sumtraits/tmp"

# Add --exclude-prediction-based to omit prediction-based trait summaries.
PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}" python -m sumtraits.cli \
    "$taxonomic_profile" \
    --taxonomic-profile-type "$taxonomic_profile_type" \
    --taxonomy-type "$taxonomy_type" \
    --output-dir "$output_dir" \
    --verbose
