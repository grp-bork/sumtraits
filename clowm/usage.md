# Usage

`sumtraits` summarizes microbial trait annotations from a taxonomic profile.

Provide an input taxonomic profile, select the profile format, select the target taxonomy, and choose an output directory. The workflow translates the profile to the selected taxonomy, looks up matching metaTraits summaries, and writes a compressed result archive.

Supported profile formats:

- `motus`
- `metaphlan`
- `kraken2`
- `krakenuniq`
- `bracken`
- `kaiju`
- `generic_ncbi`
- `generic_gtdb`

Supported target taxonomies:

- `ncbi`
- `gtdb`

Optional settings:

- `exclude_prediction_based`: use only culture-based records rather than culture and prediction based.
- `verbose`: enable debug logging and show tracebacks for runtime errors.
