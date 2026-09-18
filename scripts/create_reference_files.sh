#!/usr/bin/env bash
set -euo pipefail

# Per-rank metaTraits summaries the combined files are built from.
SOURCE_DIR=${SOURCE_DIR:-reference_sources}
# Combined files sumtraits reads at runtime.
OUTPUT_DIR=${OUTPUT_DIR:-reference_data}

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
    tmp=$(mktemp "$OUTPUT_DIR/.create_reference_files.XXXXXX")

    head -n 1 "${files[0]}" > "$tmp"
    awk 'FNR > 1' "${files[@]}" >> "$tmp"

    mv "$tmp" "$output"
}

if [[ ! -d "$SOURCE_DIR" ]]; then
    echo "Source directory not found: $SOURCE_DIR" >&2
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

shopt -s nullglob

combine_tsvs "$OUTPUT_DIR/ncbi_all.tsv" "$SOURCE_DIR"/ncbi*all.tsv
combine_tsvs "$OUTPUT_DIR/ncbi_no_predictions.tsv" "$SOURCE_DIR"/ncbi*no_predictions.tsv
combine_tsvs "$OUTPUT_DIR/gtdb_all.tsv" "$SOURCE_DIR"/gtdb*all.tsv
combine_tsvs "$OUTPUT_DIR/gtdb_no_predictions.tsv" "$SOURCE_DIR"/gtdb*no_predictions.tsv

# sumtraits needs the sidecar indexes to run
sumtraits-index --sumtraits-reference-data-dir "$OUTPUT_DIR" --force
