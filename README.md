# sumtraits

`sumtraits` is a command-line tool for summarizing microbial trait annotations from taxonomic profiles.

It translates an input profile to NCBI or GTDB taxon IDs, looks up matching metaTraits summaries, and writes output files containing the translated profile, taxon-level trait annotations, and community-level trait summaries.

## Requirements

- Python 3.11 or newer
- Local metaTraits reference data files
- `taxonkit` and the NCBI taxonomy database, if they are not already installed on the system

The Python package depends on `numpy`, `pandas`, and `taxonomic-profile-translator`.
Supported profile formats and target taxonomies are defined by `taxonomic-profile-translator`.

## Installation

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

The editable install provides the `sumtraits` command.

## Reference Data

`sumtraits` expects combined metaTraits summary files in the directory passed to `--sumtraits-reference-data-dir`:

- `REFERENCE_DATA_DIR/ncbi_all.tsv`
- `REFERENCE_DATA_DIR/ncbi_no_predictions.tsv`
- `REFERENCE_DATA_DIR/gtdb_all.tsv`
- `REFERENCE_DATA_DIR/gtdb_no_predictions.tsv`

Download the source reference files from the metaTraits downloads page:

https://metatraits.embl.de/documentation#downloads

If the reference data are available as per-rank TSV files, rebuild the combined files with:

```bash
bash scripts/create_reference_files.sh
```

By default the script reads from `reference_data/`. To use another directory:

```bash
BASE_DIR=/path/to/reference_data bash scripts/create_reference_files.sh
```

## Taxonomy Tools

If `taxonkit` or its required NCBI taxonomy database is not installed, run:

```bash
tpt install
```

NOTE: this requires `taxonomic-profile-translator` to be installed.

## Usage

```bash
sumtraits \
  --input-taxonomic-profile TAXONOMIC_PROFILE \
  --taxonomic-profile-type PROFILE_TYPE \
  --taxonomy-type TAXONOMY_TYPE \
  --sumtraits-reference-data-dir REFERENCE_DATA_DIR \
  --output-dir OUTPUT_DIR
```

Example:

```bash
sumtraits \
  --input-taxonomic-profile test_data/bracken_NCBI.tsv \
  --taxonomic-profile-type bracken \
  --taxonomy-type ncbi \
  --sumtraits-reference-data-dir reference_data \
  --output-dir tmp
```

Supported profile types:

- `generic_ncbi`
- `generic_gtdb`
- `motus`
- `metaphlan`
- `krakenuniq`
- `kraken2`
- `bracken`
- `kaiju`

Supported target taxonomies:

- `ncbi`
- `gtdb`

The target taxonomy is the taxonomy used for trait lookup. The source taxonomy is inferred by `taxonomic-profile-translator` from `--taxonomic-profile-type`.

Optional flags:

- `--exclude-prediction-based`: use the `*_no_predictions.tsv` reference summaries instead of the default `*_all.tsv` summaries.
- `--verbose`: enable debug logging and show tracebacks for runtime errors.

## Output

For an input file named `profile.tsv` and `--taxonomy-type ncbi`, `sumtraits` writes the following files to `OUTPUT_DIR`:

- `profile.ncbi.tsv`: translated and normalized taxonomic profile.
- `taxon_trait_annotations.tsv`: taxon-level trait summary rows matching the translated taxon IDs.
- `community_trait_annotations.tsv`: community-level trait summaries across the samples in the profile.
- `profile.tsv`: the original input profile.

The community summary includes rows for consensus trait states, numeric trait means, no-robust-majority annotations, unannotated abundance, and unclassified abundance where applicable.

## Development

Run the test suite with:

```bash
conda run -n sumtraits-dev python -m pytest -q
```

The main modules are:

- `src/sumtraits/cli.py`: command-line interface.
- `src/sumtraits/workflow.py`: end-to-end workflow.
- `src/sumtraits/translate.py`: taxonomic profile translation.
- `src/sumtraits/processing.py`: reference data lookup and archive writing.
- `src/sumtraits/community.py`: community-level summary generation.
