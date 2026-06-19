# Output

The workflow writes the following files directly to the results directory. For example, for an input file named `profile.tsv` and target taxonomy `ncbi`:

- `profile.ncbi.tsv`: taxonomic profile translated to the target taxonomy.
- `taxon_trait_annotations.tsv`: taxon-level trait summary rows matching the translated taxon IDs.
- `community_trait_annotations.tsv`: community-level trait summaries across the samples in the profile.
- `profile.tsv`: the original input profile.

