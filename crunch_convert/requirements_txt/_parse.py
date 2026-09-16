import re
from typing import List, Optional, Tuple

from packaging.requirements import InvalidRequirement as _PackagingInvalidRequirement
from packaging.requirements import Requirement as _PackagingRequirements

from crunch_convert._model import RequirementLanguage
from crunch_convert.requirements_txt._model import NamedRequirement

try:
    from packaging._tokenizer import ParserSyntaxError as _PackagingParserSyntaxError
except ImportError:
    _PackagingParserSyntaxError = None


class RequirementParseError(ValueError):

    def __init__(
        self,
        message: str,
        source: str,
        span: Optional[Tuple[int, int]] = None,
    ) -> None:
        super().__init__()

        self.message = message
        self.source = source
        self.span = span

    # taken from original packaging's ParserSyntaxError
    def __str__(self) -> str:
        span = self.span
        if span is None:
            return self.message

        marker = " " * span[0] + "~" * (span[1] - span[0]) + "^"
        return "\n    ".join([self.message, self.source, marker])


def parse_from_line(
    *,
    language: RequirementLanguage = RequirementLanguage.PYTHON,
    requirement_line: str,
) -> Optional[NamedRequirement]:
    line = re.sub('#.*', '', requirement_line).strip()
    if not line:
        return None

    if line.startswith('-'):
        flag_name = line.split()[0]
        raise RequirementParseError(
            f"flags are not allowed: {flag_name}",
            source=requirement_line,
            span=(0, 0)
        )

    try:
        requirement = _PackagingRequirements(line)
    except _PackagingInvalidRequirement as error:
        cause = error.__cause__
        if _PackagingParserSyntaxError is not None and isinstance(cause, _PackagingParserSyntaxError):
            raise RequirementParseError(
                f"invalid syntax: {cause.message}",
                source=cause.source,
                span=cause.span,
            ) from error

        raise RequirementParseError(
            f"invalid requirement: {error}",
            source=line,
        ) from error

    if requirement.url is not None:
        start_index = line.find("@")

        raise RequirementParseError(
            f"urls are not allowed: {requirement.url}",
            source=line,
            span=(start_index, start_index) if start_index != -1 else None,
        )

    if requirement.marker is not None:
        start_index = line.find(";")

        raise RequirementParseError(
            f"markers are not allowed: {requirement.marker}",
            source=line,
            span=(start_index, start_index) if start_index != -1 else None,
        )

    name = requirement.name
    extras = [x.lower() for x in list(requirement.extras)]
    specs = [str(x) for x in requirement.specifier]

    return NamedRequirement(
        name=name,
        extras=extras,
        specs=specs,
        language=language,
    )


def parse_from_file(
    *,
    file_content: str,
    language: RequirementLanguage = RequirementLanguage.PYTHON,
):
    named_requirements: List[NamedRequirement] = []

    for line in file_content.splitlines():
        named_requirement = parse_from_line(
            language=language,
            requirement_line=line,
        )

        if named_requirement is not None:
            named_requirements.append(named_requirement)

    return named_requirements
