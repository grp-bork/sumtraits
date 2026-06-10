# Output

The workflow writes one compressed archive to the results directory. For example, an input file named `profile.tsv` and target taxonomy `ncbi`, produces the output archive:

```text
profile_summary_ncbi.tar.gz
```

The archive contains:

- `profile.ncbi.tsv`: taxonomic profile translated to the target taxonomy.
- `taxon_trait_annotations.tsv`: taxon-level trait summary rows matching the translated taxon IDs.
- `community_trait_annotations.tsv`: community-level trait summaries across the samples in the profile.
- `profile.tsv`: the original input profile.

