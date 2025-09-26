from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from crunch_convert._model import RequirementLanguage
from crunch_convert.notebook._utils import list_of_string_factory


@dataclass()
class ImportedRequirement:
    alias: str
    name: Optional[str] = None
    extras: List[str] = field(default_factory=list_of_string_factory)
    specs: List[str] = field(default_factory=list_of_string_factory)
    language: RequirementLanguage = RequirementLanguage.PYTHON

    @property
    def extras_and_specs(self):
        return (self.extras, self.specs)

    def merge(self, other: "ImportedRequirement") -> Tuple[bool, Optional[str]]:
        """
        Merge requirements:
        - if name is missing or the same, then use other's name
        - if (extras and specs) are empty or the same, then use other's (extras and specs)

        Alias is ignored.
        """

        if self.language != other.language:
            raise ValueError(
                f"cannot merge requirements with different languages: "
                f"{self.language.name} != {other.language.name}"
            )

        errors: list[str] = []

        different_name = self.name is not None and other.name is not None and self.name != other.name
        if different_name:
            errors.append("name")

        different_extras = len(self.extras) and len(other.extras) and self.extras != other.extras
        if different_extras:
            errors.append("extras")

        different_specs = len(self.specs) and len(other.specs) and self.specs != other.specs
        if different_specs:
            errors.append("specs")

        if len(errors):
            error_count = len(errors)

            if error_count == 1:
                field = errors[0]
                be = "is" if field == "name" else "are"
                message = f"{field} {be} different"
            elif error_count == 2:
                message = f"both {errors[0]} and {errors[1]} are different"
            elif error_count == 3:
                message = f"{errors[0]}, {errors[1]} and {errors[2]} are all different"

            return False, message  # type: ignore

        if not different_name and other.name is not None:
            self.name = other.name

        if not different_extras and not different_specs and (len(other.extras) or len(other.specs)):
            self.extras = other.extras
            self.specs = other.specs

        return True, None


@dataclass()
class EmbeddedFile:
    path: str
    normalized_path: str
    content: str
