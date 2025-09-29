from typing import cast

import requirements
from crunch_convert._model import RequirementLanguage
from crunch_convert.requirements_txt._model import NamedRequirement


def parse_from_file(
    *,
    language: RequirementLanguage = RequirementLanguage.PYTHON,
    file_content: str
):
    return [
        NamedRequirement(
            name=cast(str, requirement.name),
            extras=requirement.extras,
            specs=[
                "".join(spec_parts)
                for spec_parts in requirement.specs
            ],
            language=language,
        )
        for requirement in requirements.parse(file_content)
    ]
