from typing import Optional

from crunch_convert import RequirementLanguage
from crunch_convert.requirements_txt import CachedWhitelist, Library, Whitelist

from ._libraries import sklearn_library


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
