from dataclasses import dataclass, field

from crunch_convert._model import RequirementLanguage
from crunch_convert.notebook._utils import list_of_string_factory


@dataclass()
class NamedRequirement:
    name: str
    extras: list[str] = field(default_factory=list_of_string_factory)
    specs: list[str] = field(default_factory=list_of_string_factory)
    language: RequirementLanguage = RequirementLanguage.PYTHON
    marker: str | None = None
