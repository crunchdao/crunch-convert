from dataclasses import dataclass, field

from crunch_convert._model import RequirementLanguage
from crunch_convert.notebook._utils import format_requirement_line


@dataclass()
class NamedRequirement:
    name: str
    extras: list[str] = field(default_factory=list[str])
    specs: list[str] = field(default_factory=list[str])
    language: RequirementLanguage = RequirementLanguage.PYTHON
    marker: str | None = None

    def __str__(self) -> str:
        return format_requirement_line(self.name, self.extras, self.specs, self.marker)
