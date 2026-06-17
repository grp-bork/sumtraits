process sumtraits {
    input:
    path taxonomic_profile

    output:
    path "output/*"

    publishDir "${params.output_dir}", mode: "copy"

    script:
    def optionalArgs = ""
    if (params.exclude_prediction_based) {
        optionalArgs += " \\\n      --exclude-prediction-based"
    }
    if (params.verbose) {
        optionalArgs += " \\\n      --verbose"
    }
    """
    sumtraits \
      --input-taxonomic-profile "${taxonomic_profile}" \
      --taxonomic-profile-type "${params.taxonomic_profile_type}" \
      --taxonomy-type "${params.taxonomy_type}" \
      --sumtraits-reference-data-dir "${params.sumtraits_reference_data_dir}" \
      --output-dir "output"${optionalArgs}
    """
}

workflow {
    sumtraits(params.taxonomic_profile)
}
