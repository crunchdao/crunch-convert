from string import whitespace
from textwrap import indent
from typing import TextIO


def list_of_string_factory() -> list[str]:
    return []


def print_indented(text: str, file: TextIO | None = None):
    indented = indent(text, "   | ", lambda x: True)

    if indented.endswith("\n"):
        indented = indented[:-1]

    print(indented, file=file)


def cut_crlf(input: str):
    input = input.replace("\r", "")

    if input.endswith('\n'):
        input = input[:-1]

    return input


def strip_hashes(input: str) -> str:
    return input.strip(whitespace + "#")


def format_requirement_line(name: str, extras: list[str], specs: list[str]) -> str:
    line = name

    if extras:
        line += f"[{','.join(extras)}]"

    if specs:
        line += f"{','.join(specs)}"

    return line
