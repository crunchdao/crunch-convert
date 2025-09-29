from enum import Enum
from typing import Any, cast


class RequirementLanguage(Enum):
    PYTHON = "PYTHON", "requirements.txt", "requirements.original.txt"
    R = "R", "requirements.r.txt", "requirements.r.original.txt"

    # https://stackoverflow.com/questions/12680080/python-enums-with-attributes/19300424#19300424
    def __new__(
        cls,
        *args: Any,
        **kwds: Any,
    ) -> "RequirementLanguage":
        obj = object.__new__(cls)
        obj._value_ = cast(str, args[0])
        return obj

    def __init__(
        self,
        value: str,
        txt_file_name: str,
        original_txt_file_name: str,
    ):
        value; # type: ignore
        self.txt_file_name = txt_file_name
        self.original_txt_file_name = original_txt_file_name
