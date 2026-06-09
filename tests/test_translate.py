import pandas as pd
import pytest
from taxonomic_profile_translator.errors import TranslationError

from sumtraits.translate import (
    _convert_profile_type,
    _get_profile_with_smallest_rank,
    _get_tax_ids,
)


def test_convert_profile_type_handles_generic_profiles():
    profile_type, taxonomy = _convert_profile_type("generic_ncbi")

    assert profile_type.value == "generic"
    assert taxonomy.value == "NCBI"


def test_get_profile_with_smallest_rank_prefers_species_when_useful():
    species = pd.DataFrame({"sample_a": [0.2, 0.8]}, index=[1, 2])
    genus = pd.DataFrame({"sample_a": [1.0]}, index=[10])

    result = _get_profile_with_smallest_rank({"species": species, "genus": genus})

    assert result is species


def test_get_profile_with_smallest_rank_falls_back_from_singleton_species():
    species = pd.DataFrame({"sample_a": [1.0]}, index=[-1])
    genus = pd.DataFrame({"sample_a": [0.4, 0.6]}, index=[10, 20])

    result = _get_profile_with_smallest_rank({"species": species, "genus": genus})

    assert result is genus


def test_get_profile_with_smallest_rank_keeps_singleton_species_if_all_are_singletons():
    species = pd.DataFrame({"sample_a": [1.0]}, index=[-1])
    genus = pd.DataFrame({"sample_a": [1.0]}, index=[-1])

    result = _get_profile_with_smallest_rank({"species": species, "genus": genus})

    assert result is species


def test_get_profile_with_smallest_rank_raises_when_no_rank_is_usable():
    with pytest.raises(TranslationError):
        _get_profile_with_smallest_rank({})


def test_get_tax_ids_ignores_na_index_values():
    profile = pd.DataFrame({"sample_a": [0.5, 0.5]}, index=["42", "NA"])

    assert _get_tax_ids(profile) == {42}
