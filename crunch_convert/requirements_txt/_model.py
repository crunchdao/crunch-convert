from dataclasses import dataclass, field

from crunch_convert._model import RequirementLanguage


@dataclass()
class NamedRequirement:
    name: str
    extras: list[str] = field(default_factory=list[str])
    specs: list[str] = field(default_factory=list[str])
    language: RequirementLanguage = RequirementLanguage.PYTHON
    marker: str | None = None
