import pytest

from crunch_convert._model import RequirementLanguage
from crunch_convert.requirements_txt import LocalWhitelist
from crunch_convert.requirements_txt._whitelist import \
    MultipleLibraryAliasCandidateException

from ._libraries import (emd_signal_library, pandas_in_r_library,
                         pandas_library, pyemd_library, sklearn_library)

whitelist = LocalWhitelist([
    sklearn_library,
    pandas_library,
    pandas_in_r_library,
])


def test_find_by_alias():
    assert sklearn_library is whitelist.find_library(alias="sklearn")
    assert pandas_library is whitelist.find_library(alias="pandas")
    assert pandas_in_r_library is whitelist.find_library(alias="pandas", language=RequirementLanguage.R)

    assert None is whitelist.find_library(alias="unknown")
    assert None is whitelist.find_library(alias="unknown", language=RequirementLanguage.R)


def test_find_by_name():
    assert sklearn_library is whitelist.find_library(name="scikit-learn")
    assert pandas_library is whitelist.find_library(name="pandas")
    assert pandas_in_r_library is whitelist.find_library(name="pandas", language=RequirementLanguage.R)

    assert None is whitelist.find_library(name="unknown")
    assert None is whitelist.find_library(name="unknown", language=RequirementLanguage.R)


def test_find_by_alias_collision():
    whitelist = LocalWhitelist([
        pyemd_library,
        emd_signal_library,
    ])

    with pytest.raises(MultipleLibraryAliasCandidateException) as exc_info:
        whitelist.find_library(alias="pyemd")

    assert exc_info.value.alias == "pyemd"
    assert exc_info.value.names == {"EMD-signal", "pyemd"}
