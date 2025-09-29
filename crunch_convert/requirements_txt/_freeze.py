from abc import ABC, abstractmethod
from typing import List, Literal, Optional, overload

import requests

from crunch_convert._model import RequirementLanguage
from crunch_convert.requirements_txt._model import NamedRequirement
from crunch_convert.requirements_txt._whitelist import Whitelist


@overload
def freeze(
    requirements: List[NamedRequirement],
    *,
    freeze_only_if_required: Literal[True] = True,
    whitelist: Whitelist,
    version_finder: "VersionFinder",
) -> List[NamedRequirement]:
    ...  # pragma: no cover


@overload
def freeze(
    requirements: List[NamedRequirement],
    *,
    freeze_only_if_required: Literal[False] = False,
    version_finder: "VersionFinder",
) -> List[NamedRequirement]:
    ...  # pragma: no cover


def freeze(
    requirements: List[NamedRequirement],
    *,
    version_finder: "VersionFinder",
    whitelist: Optional[Whitelist] = None,
    freeze_only_if_required: bool = True,
) -> List[NamedRequirement]:
    frozen_requirements: List[NamedRequirement] = []

    for requirement in requirements:
        latest_version = _get_latest_version(
            whitelist=whitelist,
            requirement=requirement,
            version_finder=version_finder,
            freeze_only_if_required=freeze_only_if_required,
        )

        if latest_version is not None:
            requirement = NamedRequirement(
                name=requirement.name,
                extras=requirement.extras,
                specs=[f"=={latest_version}"],
                language=requirement.language,
            )

        frozen_requirements.append(requirement)

    return frozen_requirements


def _get_latest_version(
    *,
    whitelist: Optional[Whitelist] = None,
    requirement: NamedRequirement,
    version_finder: "VersionFinder",
    freeze_only_if_required: bool = True,
) -> Optional[str]:
    # don't overwrite existing specs
    if requirement.specs:
        return None

    if freeze_only_if_required:
        assert whitelist is not None

        library = whitelist.find_library(
            language=requirement.language,
            name=requirement.name,
        )

        # not whitelisted?
        if library is None:
            return None

        # not required to be frozen
        if not library.freeze:
            return None

    return version_finder.find_latest(
        name=requirement.name,
    )


class VersionFinder(ABC):

    @abstractmethod
    def find_latest(
        self,
        *,
        language: RequirementLanguage = RequirementLanguage.PYTHON,
        name: str
    ) -> Optional[str]:
        ...  # pragma: no cover


class CrunchHubVersionFinder(VersionFinder):

    def __init__(
        self,
        *,
        api_base_url: str = "https://api.hub.crunchdao.com/",
    ):
        super().__init__()

        self._api_base_url = api_base_url

    def find_latest(
        self,
        *,
        language: RequirementLanguage = RequirementLanguage.PYTHON,
        name: str
    ) -> Optional[str]:
        response = requests.get(
            f"{self._api_base_url}/v1/libraries/{language.name}/{name}/latest",
            params={
                "language": language.value,
                "name": name
            },
        )

        if response.status_code != 200:
            return None

        body = response.json()
        return body.get("version")


class LocalSitePackageVersionFinder(VersionFinder):

    def find_latest(
        self,
        *,
        language: RequirementLanguage = RequirementLanguage.PYTHON,
        name: str
    ) -> Optional[str]:
        if language != RequirementLanguage.PYTHON:
            return None

        from importlib.metadata import (PackageNotFoundError,  # late import
                                        distribution)

        try:
            return distribution(name).version
        except PackageNotFoundError:
            return None
