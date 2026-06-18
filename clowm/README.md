# SumTraits workflow

#### Description

SumTraits is a Nextflow workflow for summarizing microbial trait annotations from taxonomic profiles. The workflow translates and normalizes an input profile to NCBI or GTDB taxon IDs using `taxonomic-profile-translator`, matches the translated taxa against metaTraits reference summaries, and generates taxon-level and community-level trait annotations.

---

# Overview

1. Translate and normalize the input taxonomic profile to the selected target taxonomy using [`taxonomic-profile-translator`](https://git.embl.org/robbani/taxonomic-profile-translator), [`TaxonKit`](https://github.com/shenwei356/taxonkit), and [`PyTaxonKit`](https://github.com/bioforensics/pytaxonkit)
2. Match translated taxon IDs against the selected [metaTraits](https://metatraits.embl.de/) reference summary
3. Generate taxon-level and community-level trait annotations and package the results in a compressed archive

---

# Usage

## Command-Line Interface (CLI)

```bash
nextflow run main.nf \
    --taxonomic_profile <taxonomic_profile> \
    --taxonomic_profile_type <profile_type> \
    --taxonomy_type <ncbi|gtdb> \
    --sumtraits_reference_data_dir <reference_data_directory> \
    --output_dir <output_directory>
```

## Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| `--taxonomic_profile` | Path or S3 URI to the input taxonomic profile | ✅ |
| `--taxonomic_profile_type` | Input profile format: `motus`, `metaphlan`, `kraken2`, `krakenuniq`, `bracken`, `kaiju`, `generic_ncbi`, or `generic_gtdb` | ✅ |
| `--taxonomy_type` | Target taxonomy used for trait lookup: `ncbi` or `gtdb` | ✅ |
| `--sumtraits_reference_data_dir` | Directory containing the SumTraits reference data files; preconfigured when running through Clowm | ✅ |
| `--output_dir` | Path or S3 URI to the output directory | ✅ |
| `--exclude_prediction_based` | Exclude prediction-based trait annotations and use culture-based records only | ❌ |
| `--verbose` | Enable debug logging and runtime tracebacks | ❌ |

## Output files

The workflow writes a compressed archive to `--output_dir`. For an input file named `profile.tsv` and target taxonomy `ncbi`, the archive is named `profile_summary_ncbi.tar.gz`.

| File | Description |
|------|-------------|
| `profile.<taxonomy>.tsv` | Input profile translated and normalized to the target taxonomy |
| `taxon_trait_annotations.tsv` | Taxon-level trait summaries for taxa found in the translated profile |
| `community_trait_annotations.tsv` | Community-level trait summaries across the samples in the profile |
| `<original_profile>` | Original input taxonomic profile |

---

# Citation

If you use this workflow, please cite the tools it depends on:

```text
Shen W, Ren H. TaxonKit: A Practical and Efficient NCBI Taxonomy Toolkit. PLoS Comput Biol. 2021;17(3):e1008647. doi:10.1371/journal.pcbi.1008647

Standage D. PyTaxonKit: Python bindings for the TaxonKit library. https://github.com/bioforensics/pytaxonkit
```
