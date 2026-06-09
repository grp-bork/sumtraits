#!/usr/bin/env bash
set -euo pipefail

BASE_DIR=${BASE_DIR:-reference_data}

combine_tsvs() {
    local output=$1
    shift

    local files=()
    local file
    for file in "$@"; do
        if [[ -f "$file" && "$file" != "$output" ]]; then
            files+=("$file")
        fi
    done

    if ((${#files[@]} == 0)); then
        echo "No input files found for $output" >&2
        return 1
    fi

    local tmp
    tmp=$(mktemp "$BASE_DIR/.create_reference_files.XXXXXX")

    head -n 1 "${files[0]}" > "$tmp"
    awk 'FNR > 1' "${files[@]}" >> "$tmp"

    mv "$tmp" "$output"
}

shopt -s nullglob

combine_tsvs "$BASE_DIR/ncbi_all.tsv" "$BASE_DIR"/ncbi*all.tsv
combine_tsvs "$BASE_DIR/ncbi_no_predictions.tsv" "$BASE_DIR"/ncbi*no_predictions.tsv
combine_tsvs "$BASE_DIR/gtdb_all.tsv" "$BASE_DIR"/gtdb*all.tsv
combine_tsvs "$BASE_DIR/gtdb_no_predictions.tsv" "$BASE_DIR"/gtdb*no_predictions.tsv
