#!/usr/bin/env bash
set -euo pipefail

# Builds gzipped copies of the two reference output files (per
# taxonomy_type/profile_type combo) used by tests/test_e2e.py, from the
# full test_results/ directory produced by scripts/run_test_data.sh.
#
# test_results/ is never modified; only compressed copies are written
# to RESULTS_REFERENCE_DIR, which is small enough to commit to git.

RESULTS_DIR="test_results"
RESULTS_REFERENCE_DIR="tests/data/e2e_reference"
FILES_TO_COPY=("taxon_trait_annotations.tsv" "community_trait_annotations.tsv")

for taxonomy_dir in "$RESULTS_DIR"/*/; do
  taxonomy_type=$(basename "$taxonomy_dir")
  for profile_dir in "$taxonomy_dir"*/; do
    profile_type=$(basename "$profile_dir")
    output_dir="${RESULTS_REFERENCE_DIR}/${taxonomy_type}/${profile_type}"
    mkdir -p "$output_dir"
    for file_name in "${FILES_TO_COPY[@]}"; do
      source_file="${profile_dir}${file_name}"
      if [[ -f "$source_file" ]]; then
        echo "Compressing ${source_file} -> ${output_dir}/${file_name}.gz"
        gzip -c "$source_file" > "${output_dir}/${file_name}.gz"
      else
        echo "Missing ${source_file}, skipping" >&2
      fi
    done
  done
done
