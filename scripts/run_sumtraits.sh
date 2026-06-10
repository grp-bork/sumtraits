#!/usr/bin/env bash
set -euo pipefail

taxonomic_profile="/home/robbani/embl/sumtraits/test_data/GTDB_genus_enterotype.tsv"
taxonomic_profile_type="generic_gtdb"
taxonomy_type="ncbi"
reference_data_dir="/home/robbani/embl/sumtraits/reference_data"
output_dir="/home/robbani/embl/sumtraits/tmp"

# Add --exclude-prediction-based to omit prediction-based trait summaries.
PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}" \
python # -m memray run --native -o memray-sumtraits.bin \
  -m sumtraits.cli \
  --input-taxonomic-profile "$taxonomic_profile" \
  --taxonomic-profile-type "$taxonomic_profile_type" \
  --taxonomy-type "$taxonomy_type" \
  --summtraits-reference-data-dir "$reference_data_dir" \
  --output-dir "$output_dir" \
  --verbose

# python -m memray summary memray-sumtraits.bin
# python -m memray flamegraph -o memray-sumtraits.html memray-sumtraits.bin
# python -m memray table -o memray-sumtraits-table.html memray-sumtraits.bin
