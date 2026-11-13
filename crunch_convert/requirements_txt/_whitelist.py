import warnings
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from io import UnsupportedOperation
from typing import Any, cast, overload

import requests

from crunch_convert._model import RequirementLanguage


class MultipleLibraryAliasCandidateException(Exception):

    def __init__(self, alias: str, names: set[str]):
        super().__init__(f"multiple library match the alias")
        self.alias = alias
        self.names = names


@dataclass()
class Library:
    language: RequirementLanguage
    name: str
    aliases: list[str]
    standard: bool
    freeze: bool

    @property
    def alias(self):
        warnings.warn(
            "alias is deprecated and will be removed in a future version. Use aliases instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.aliases[0] if len(self.aliases) else None


class Whitelist(ABC):

    @overload
    def find_library(
        self,
        *,
        language: RequirementLanguage = RequirementLanguage.PYTHON,
        name: str,
    ) -> Library | None:
        ...  # pragma: no cover

    @overload
    def find_library(
        self,
        *,
        language: RequirementLanguage = RequirementLanguage.PYTHON,
        alias: str,
    ) -> Library | None:
        ...  # pragma: no cover

    @abstractmethod
    def find_library(
        self,
        *,
        language: RequirementLanguage = RequirementLanguage.PYTHON,
        name: str | None = None,
        alias: str | None = None,
    ) -> Library | None:
        pass  # pragma: no cover


CacheCompositeKey = tuple[RequirementLanguage, str]


class CachedWhitelist(Whitelist):

    def __init__(
        self,
        delegate: Whitelist,
    ):
        super().__init__()

        self._delegate = delegate

        self._name_cache: dict[CacheCompositeKey, Library] = {}
        self._alias_cache: defaultdict[CacheCompositeKey, dict[str, Library]] = defaultdict(dict)

    def find_library(
        self,
        *,
        language: RequirementLanguage = RequirementLanguage.PYTHON,
        name: str | None = None,
        alias: str | None = None,
    ) -> Library | None:
        if name is not None:
            cached = self._name_cache.get((language, name.lower()))
            if cached is not None:
                return cached

            library = self._delegate.find_library(
                language=language,
                name=name,
            )

        elif alias is not None:
            cached = self._alias_cache.get((language, alias.lower()), None)
            if cached is not None:
                libraries = list(cached.values())

                if len(libraries) > 1:
                    raise MultipleLibraryAliasCandidateException(
                        alias=alias,
                        names={
                            library.name
                            for library in libraries
                        },
                    )

                return libraries[0]

            library = self._delegate.find_library(
                language=language,
                alias=alias,
            )

        else:
            raise UnsupportedOperation("find_library() must be called with either 'name' or 'alias'.")  # pragma: no cover

        self._store_in_cache(library)
        return library

    def _store_in_cache(
        self,
        library: Library | None,
    ) -> None:
        if library is None:
            return
    
        name = library.name.lower()

        self._name_cache[(library.language, name)] = library

        for alias in library.aliases:
            self._alias_cache[(library.language, alias.lower())][name] = library


class CrunchHubWhitelist(Whitelist):

    def __init__(
        self,
        *,
        api_base_url: str = "https://api.hub.crunchdao.com/",
    ):
        super().__init__()

        self._api_base_url = api_base_url

    def find_library(
        self,
        *,
        language: RequirementLanguage = RequirementLanguage.PYTHON,
        name: str | None = None,
        alias: str | None = None,
    ) -> Library | None:
        response = requests.get(
            f"{self._api_base_url}/v2/libraries",
            params={
                "language": language.value,
                # TODO Use dedicated parameter for alias
                "name": name or alias
            },
        )

        if response.status_code != 200:
            return None

        content = response.json().get("content", [])
        if not content:
            return None

        alias_conflicting_names: set[str] = set()
        library: Library | None = None

        if name is not None:
            name = name.lower()  # used for case-insensitive comparison

        for item in content:
            library = self._map_library(item)

            if name is not None and name == library.name.lower():
                return library

            elif alias is not None and alias in library.aliases:
                alias_conflicting_names.add(library.name)

            else:
                library = None

        if len(alias_conflicting_names) > 1:
            raise MultipleLibraryAliasCandidateException(
                alias=cast(str, alias),
                names=alias_conflicting_names,
            )

        return library

    def _map_library(
        self,
        item: dict[str, Any],
    ) -> Library:
        return Library(
            language=RequirementLanguage(item["language"]),
            name=item["name"],
            aliases=item["aliases"],
            standard=item["standard"],
            freeze=item["freeze"],
        )


class LocalWhitelist(Whitelist):

    def __init__(
        self,
        libraries: list[Library]
    ):
        super().__init__()

        self._library_by_name: dict[CacheCompositeKey, Library] = {}
        self._libraries_by_alias: dict[CacheCompositeKey, list[Library]] = defaultdict(list)

        for library in libraries:
            self._library_by_name[(library.language, library.name.lower())] = library

            for alias in library.aliases:
                self._libraries_by_alias[(library.language, alias)].append(library)

    def find_library(
        self,
        *,
        language: RequirementLanguage = RequirementLanguage.PYTHON,
        name: str | None = None,
        alias: str | None = None,
    ) -> Library | None:
        if name is not None:
            return self._library_by_name.get((language, name.lower()))

        elif alias is not None:
            libraries = self._libraries_by_alias.get((language, alias))
            if not libraries:
                return None

            if len(libraries) > 1:
                names = set(
                    library.name
                    for library in libraries
                )

                raise MultipleLibraryAliasCandidateException(
                    alias=alias,
                    names=names,
                )

            return libraries[0]

        else:
            raise UnsupportedOperation("find_library() must be called with either 'name' or 'alias'.")  # pragma: no cover
