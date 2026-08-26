#!/usr/bin/env bash
set -euo pipefail

# Runs sumtraits (the Python CLI, via the sumtraits-dev conda env) on each
# file in test_data/, against both ncbi and gtdb target taxonomies, writing
# results to:
#   ${RESULTS_DIR}/<taxonomy_type>/<profile_type>/
#
# Mapping of test_data files to --taxonomic-profile-type mirrors
# tests/test_e2e.py's DEFAULT_PROFILE_TYPES + EXTENDED_PROFILE_TYPES, so this
# script produces results for every profile_type the e2e tests need
# reference files for.
declare -A PROFILE_TYPE=(
  [test_data/GTDB_genus_enterotype_truncated.tsv]="generic_gtdb"
  [test_data/NCBI_genus_enterotype_truncated.tsv]="generic_ncbi"
  [test_data/motus3_truncated.tsv]="motus"
  [test_data/metaphlan4_default.txt]="metaphlan"
  [test_data/bracken_NCBI.tsv]="bracken"
  [test_data/kaiju_NCBI.txt]="kaiju"
  [test_data/kraken2_GTDB.txt]="kraken2"
  [test_data/krakenuniq_GTDB.txt]="krakenuniq"
)

REFERENCE_DATA_DIR="reference_data"
RESULTS_DIR="test_results_v0.3.0"
TAXONOMY_TYPES=("ncbi" "gtdb")
CONDA_ENV="sumtraits-dev"

for taxonomic_profile in "${!PROFILE_TYPE[@]}"; do
  taxonomic_profile_type="${PROFILE_TYPE[$taxonomic_profile]}"
  for taxonomy_type in "${TAXONOMY_TYPES[@]}"; do
    output_dir="${RESULTS_DIR}/${taxonomy_type}/${taxonomic_profile_type}"
    mkdir -p "$output_dir"
    echo "Running ${taxonomic_profile} (profile_type=${taxonomic_profile_type}, taxonomy_type=${taxonomy_type}) -> ${output_dir}"
    conda run -n "$CONDA_ENV" sumtraits \
      --input-taxonomic-profile "$taxonomic_profile" \
      --taxonomic-profile-type "$taxonomic_profile_type" \
      --taxonomy-type "$taxonomy_type" \
      --sumtraits-reference-data-dir "$REFERENCE_DATA_DIR" \
      --output-dir "$output_dir"
  done
done
