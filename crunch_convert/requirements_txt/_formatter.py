from collections import defaultdict
from typing import DefaultDict, Dict, List, Optional, Union, cast

from crunch_convert._model import RequirementLanguage
from crunch_convert.notebook._model import ImportedRequirement
from crunch_convert.requirements_txt._model import NamedRequirement
from crunch_convert.requirements_txt._whitelist import Library, Whitelist

Requirement = Union[NamedRequirement, ImportedRequirement]


def format_files_from_imported(
    requirements: List[ImportedRequirement],
    *,
    header: str,
    whitelist: Whitelist,
) -> Dict[RequirementLanguage, str]:
    return _format_files(
        requirements=cast(List[Requirement], requirements),
        header=header,
        whitelist=whitelist,
    )


def format_files_from_named(
    requirements: List[NamedRequirement],
    *,
    header: str,
    whitelist: Whitelist,
) -> Dict[RequirementLanguage, str]:
    return _format_files(
        requirements=cast(List[Requirement], requirements),
        header=header,
        whitelist=whitelist,
    )


def _format_files(
    *,
    requirements: List[Requirement],
    header: str,
    whitelist: Whitelist,
) -> DefaultDict[RequirementLanguage, str]:
    files: DefaultDict[RequirementLanguage, str] = defaultdict(str)

    requirements_by_language: Dict[RequirementLanguage, List[Requirement]] = defaultdict(list)
    for requirement in requirements:
        requirements_by_language[requirement.language].append(requirement)

    for language, requirements_for_language in requirements_by_language.items():
        files[language] = _format_files_filtered(
            requirements_for_language,
            header=header,
            whitelist=whitelist,
        )

    return files


def _format_files_filtered(
    requirements: List[Requirement],
    *,
    header: str,
    whitelist: Whitelist,
):
    third_party: List[str] = []
    standard: List[str] = []

    for requirement in requirements:
        library = find_library(requirement, whitelist)

        if library is None:
            third_party.append(format_line(
                get_fallback_name(requirement),
                None,
                requirement.extras,
                requirement.specs,
            ))

        elif library.standard:
            standard.append(get_fallback_name(requirement))

        elif isinstance(requirement, ImportedRequirement):
            third_party.append(format_line(
                library.name,
                requirement.alias,
                requirement.extras,
                requirement.specs,
            ))

        else:
            third_party.append(format_line(
                library.name,
                None,
                requirement.extras,
                requirement.specs,
            ))

    third_party.sort(key=str.lower)
    standard.sort(key=str.lower)

    builder = f"# {header}\n"

    if third_party:
        builder += "\n"

        if standard:
            builder += "## third-party\n"

        for requirement_line in third_party:
            builder += f"{requirement_line}\n"

    if standard:
        builder += "\n"

        if third_party:
            builder += "## standard\n"

        for requirement_line in standard:
            builder += f"#{requirement_line}\n"

    return builder


def format_line(
    name: str,
    alias: Optional[str],
    extras: List[str],
    specs: List[str],
) -> str:
    line = name

    if extras:
        line += f"[{','.join(extras)}]"

    if specs:
        line += f"{','.join(specs)}"

    if alias and name != alias:
        line += f"  # alias of {alias}"

    return line


def get_fallback_name(
    requirement: Requirement,
) -> str:
    if isinstance(requirement, ImportedRequirement):
        return requirement.name or requirement.alias

    return requirement.name


def find_library(
    requirement: Requirement,
    whitelist: Whitelist,
) -> Optional[Library]:
    if isinstance(requirement, ImportedRequirement):
        name = requirement.name
        if name:
            return whitelist.find_library(
                language=requirement.language,
                name=name,
            )

        return whitelist.find_library(
            language=requirement.language,
            alias=requirement.alias,
        )
    else:
        assert isinstance(requirement, NamedRequirement)

        return whitelist.find_library(
            language=requirement.language,
            name=requirement.name,
        )
