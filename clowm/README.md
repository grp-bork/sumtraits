# sumTraits: a metaTraits workflow

<table>
  <tr width="100%">
    <td width="150px">
      <a href="https://www.bork.embl.de/"><img src="https://www.bork.embl.de/assets/img/normal_version.png" alt="Bork Group Logo" width="150px" height="auto"></a>
    </td>
    <td width="425px" align="center">
      <b>Developed by the <a href="https://www.bork.embl.de/">Bork Group</a></b><br>
      Raise an <a href="https://github.com/grp-bork/sumtraits/issues">issue</a> or <a href="mailto:N4M@embl.de">contact us</a><br><br>
      See our <a href="https://www.bork.embl.de/services.html">other Software & Services</a>
    </td>
    <td width="500px">
      Contributors:<br>
      <ul>
        <li>
          <a href="https://github.com/mahdi-robbani/">Mahdi Robbani</a> <a href="https://orcid.org/0000-0003-0161-0559"><img src="https://orcid.org/assets/vectors/orcid.logo.icon.svg" alt="ORCID icon" width="20px" height="20px"></a><br>
        </li>
        <li>
          <a href="https://github.com/danielpodlesny/">Daniel Podlesny</a> <a href="https://orcid.org/0000-0002-5685-0915"><img src="https://orcid.org/assets/vectors/orcid.logo.icon.svg" alt="ORCID icon" width="20px" height="20px"></a><br>
        </li>
      </ul>
    </td>
  </tr>
  <tr>
    <td colspan="4" align="center">The development of this workflow was supported by <a href="https://www.nfdi4microbiota.de/">NFDI4Microbiota <img src="https://github.com/user-attachments/assets/1e78f65e-9828-46c0-834c-0ed12ca9d5ed" alt="NFDI4Microbiota icon" width="20px" height="20px"></a> 
</td>
  </tr>
</table>
        
---
#### Description

The `sumTraits workflow` is a nextflow workflow for summarizing microbial trait annotations from taxonomic profiles.
It translates an input taxonomic profile to NCBI or GTDB taxon IDs, looks up matching metaTraits summaries, and writes output files containing the translated profile, taxon-level trait annotations, and community-level trait summaries.

#### Citation
This workflow: TBD

metaTraits:
```
Podlesny, Kim et al (2025) metaTraits: a large-scale integration of microbial phenotypic trait information, Nucleic Acids Research, 2025;, gkaf1241, https://doi.org/10.1093/nar/gkaf1241
```

Also cite:
```
Shen W, Ren H. TaxonKit: A Practical and Efficient NCBI Taxonomy Toolkit. PLoS Comput Biol. 2021;17(3):e1008647. doi:10.1371/journal.pcbi.1008647
Standage D. PyTaxonKit: Python bindings for the TaxonKit library. https://github.com/bioforensics/pytaxonkit
```


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

The workflow writes a set of output files directly to `--output_dir`.

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
