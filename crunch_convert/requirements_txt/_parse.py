from typing import Optional, Tuple, cast

import requirements
from crunch_convert._model import RequirementLanguage
from crunch_convert.requirements_txt._model import NamedRequirement

try:
    from packaging.requirements import InvalidRequirement as _PackagingInvalidRequirement
except ImportError:
    _PackagingInvalidRequirement = Exception

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


def parse_from_file(
    *,
    language: RequirementLanguage = RequirementLanguage.PYTHON,
    file_content: str
):
    try:
        parsed_requirements = list(requirements.parse(file_content))
    except _PackagingInvalidRequirement as error:
        cause = error.__cause__
        if _PackagingParserSyntaxError is not None and isinstance(cause, _PackagingParserSyntaxError):
            raise RequirementParseError(
                cause.message,
                source=cause.source,
                span=cause.span,
            ) from error

        raise RequirementParseError(
            str(error),
            source=file_content,
        ) from error

    return [
        NamedRequirement(
            name=cast(str, parsed_requirement.name),
            extras=parsed_requirement.extras,
            specs=[
                "".join(spec_parts)
                for spec_parts in parsed_requirement.specs
            ],
            language=language,
        )
        for parsed_requirement in parsed_requirements
    ]
