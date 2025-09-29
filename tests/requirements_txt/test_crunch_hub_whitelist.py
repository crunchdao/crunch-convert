import pytest

from crunch_convert import RequirementLanguage
from crunch_convert.requirements_txt import (
    CrunchHubWhitelist, MultipleLibraryAliasCandidateException)

from ._env import api_base_url

whitelist = CrunchHubWhitelist(
    api_base_url=api_base_url,
)


def test_find_by_alias():
    library = whitelist.find_library(alias="sklearn")
    assert library is not None and library.alias == "sklearn"

    library = whitelist.find_library(alias="pandas")
    assert library is not None and library.alias == "pandas"

    library = whitelist.find_library(alias="base", language=RequirementLanguage.R)
    assert library is not None and library.alias == "base"

    assert None is whitelist.find_library(alias="scikit-learn")

    assert None is whitelist.find_library(alias="unknown")
    assert None is whitelist.find_library(alias="unknown", language=RequirementLanguage.R)


def test_find_by_name():
    library = whitelist.find_library(name="scikit-learn")
    assert library is not None and library.name == "scikit-learn"

    library = whitelist.find_library(name="pandas")
    assert library is not None and library.name == "pandas"

    library = whitelist.find_library(name="base", language=RequirementLanguage.R)
    assert library is not None and library.name == "base"

    assert None is whitelist.find_library(name="sklearn")

    assert None is whitelist.find_library(name="unknown")
    assert None is whitelist.find_library(name="unknown", language=RequirementLanguage.R)


@pytest.mark.skip(reason="No real candidate for collision in CrunchHubWhitelist yet.")
def test_find_by_alias_collision():
    with pytest.raises(MultipleLibraryAliasCandidateException) as exc_info:
        whitelist.find_library(alias="pyemd")

    assert exc_info.value.alias == "pyemd"
    assert exc_info.value.names == {"EMD-signal", "pyemd"}
