from collections import defaultdict
from typing import cast

from crunch_convert._model import RequirementLanguage
from crunch_convert.notebook._model import ImportedRequirement
from crunch_convert.notebook._utils import format_requirement_line
from crunch_convert.requirements_txt._model import NamedRequirement
from crunch_convert.requirements_txt._whitelist import Library, Whitelist

Requirement = NamedRequirement | ImportedRequirement


def format_files_from_imported(
    requirements: list[ImportedRequirement],
    *,
    header: str,
    whitelist: Whitelist,
) -> dict[RequirementLanguage, str]:
    return _format_files(
        requirements=cast(list[Requirement], requirements),
        header=header,
        whitelist=whitelist,
    )


def format_files_from_named(
    requirements: list[NamedRequirement],
    *,
    header: str,
    whitelist: Whitelist,
) -> dict[RequirementLanguage, str]:
    return _format_files(
        requirements=cast(list[Requirement], requirements),
        header=header,
        whitelist=whitelist,
    )


def _format_files(
    *,
    requirements: list[Requirement],
    header: str,
    whitelist: Whitelist,
) -> defaultdict[RequirementLanguage, str]:
    files: defaultdict[RequirementLanguage, str] = defaultdict(str)

    requirements_by_language: dict[RequirementLanguage, list[Requirement]] = defaultdict(list)
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
    requirements: list[Requirement],
    *,
    header: str,
    whitelist: Whitelist,
):
    third_party: list[str] = []
    standard: list[str] = []

    for requirement in requirements:
        library = find_library(requirement, whitelist)

        if library is None:
            third_party.append(format_line(
                get_fallback_name(requirement),
                None,
                requirement.extras,
                requirement.specs,
                get_marker(requirement),
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
                get_marker(requirement),
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
    alias: str | None,
    extras: list[str],
    specs: list[str],
    marker: str | None = None,
) -> str:
    line = format_requirement_line(name, extras, specs)

    if marker:
        line += f"; {marker}"

    if alias and name != alias:
        line += f"  # alias of {alias}"

    return line


def get_fallback_name(
    requirement: Requirement,
) -> str:
    if isinstance(requirement, ImportedRequirement):
        return requirement.name or requirement.alias

    return requirement.name


def get_marker(
    requirement: Requirement,
) -> str | None:
    if isinstance(requirement, NamedRequirement):
        return requirement.marker

    return None


def find_library(
    requirement: Requirement,
    whitelist: Whitelist,
) -> Library | None:
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
