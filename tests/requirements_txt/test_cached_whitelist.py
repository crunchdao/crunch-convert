from typing import Optional

import pytest

from crunch_convert import RequirementLanguage
from crunch_convert.requirements_txt import CachedWhitelist, Library, Whitelist
from crunch_convert.requirements_txt._whitelist import MultipleLibraryAliasCandidateException

from ._libraries import emd_signal_library, pyemd_library, sklearn_library


class DummyWhitelist(Whitelist):

    def __init__(self):
        self.next_library = None
        self.call_count = 0

    def reset(self, library: Optional[Library] = None):
        self.next_library = library
        self.call_count = 0

    def find_library(
        self,
        *,
        language: RequirementLanguage = RequirementLanguage.PYTHON,
        name: Optional[str] = None,
        alias: Optional[str] = None,
    ) -> Optional[Library]:
        self.call_count += 1
        return self.next_library


def test_not_found():
    spy = DummyWhitelist()
    whitelist = CachedWhitelist(spy)

    assert None is whitelist.find_library(alias="sklearn")
    assert None is whitelist.find_library(alias="sklearn")
    assert 2 == spy.call_count


def test_find_by_alias():
    spy = DummyWhitelist()
    whitelist = CachedWhitelist(spy)

    spy.reset(sklearn_library)
    assert sklearn_library is whitelist.find_library(alias="sklearn")
    assert sklearn_library is whitelist.find_library(alias="sklearn")
    assert 1 == spy.call_count


def test_find_by_name():
    spy = DummyWhitelist()
    whitelist = CachedWhitelist(spy)

    spy.reset(sklearn_library)
    assert sklearn_library is whitelist.find_library(name="scikit-learn")
    assert sklearn_library is whitelist.find_library(name="scikit-learn")
    assert 1 == spy.call_count


def test_name_cache_alias():
    spy = DummyWhitelist()
    whitelist = CachedWhitelist(spy)

    spy.reset(sklearn_library)
    assert sklearn_library is whitelist.find_library(name="scikit-learn")
    assert sklearn_library is whitelist.find_library(alias="sklearn")
    assert 1 == spy.call_count


def test_alias_name_cache():
    spy = DummyWhitelist()
    whitelist = CachedWhitelist(spy)

    spy.reset(sklearn_library)
    assert sklearn_library is whitelist.find_library(alias="sklearn")
    assert sklearn_library is whitelist.find_library(name="scikit-learn")
    assert 1 == spy.call_count


def test_find_by_alias_collision():
    spy = DummyWhitelist()
    whitelist = CachedWhitelist(spy)

    spy.reset(emd_signal_library)
    whitelist.find_library(name=emd_signal_library.name)

    spy.reset(pyemd_library)
    whitelist.find_library(name=pyemd_library.name)

    with pytest.raises(MultipleLibraryAliasCandidateException) as exc_info:
        whitelist.find_library(alias="pyemd")

    assert exc_info.value.alias == "pyemd"
    assert exc_info.value.names == {"EMD-signal", "pyemd"}
