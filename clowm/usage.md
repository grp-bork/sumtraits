# Output

The directories listed below will be created in the results directory after the pipeline has finished. All paths are relative to the top-level results directory.

## HMMER

- `hmm_output.tbl`: Tabular summary of all gene-to-HMM hits, one line per hit, produced by `hmmscan --tblout`.

[HMMER](http://hmmer.org/) searches predicted gene sequences against the provided HMM profile. Only hits passing the profile's gathering threshold (`--cut_ga`) are reported.

## nfixplanet

- `annotations/`: Directory containing annotation output files produced by `nfixplanet annotate`.

[nfixplanet](https://github.com/grp-bork/nfixplanet) interprets the HMMER hits and assigns functional annotations to nitrogen fixation genes.