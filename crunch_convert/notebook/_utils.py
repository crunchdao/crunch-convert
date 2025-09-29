from string import whitespace
from textwrap import indent
from typing import List


def list_of_string_factory() -> List[str]:
    return []


def print_indented(text: str):
    indented = indent(text, "   | ", lambda x: True)

    if indented.endswith("\n"):
        indented = indented[:-1]

    print(indented)


def cut_crlf(input: str):
    input = input.replace("\r", "")

    if input.endswith('\n'):
        input = input[:-1]

    return input


def strip_hashes(input: str) -> str:
    return input.strip(whitespace + "#")


def format_requirement_line(name: str, extras: List[str], specs: List[str]) -> str:
    line = name

    if extras:
        line += f"[{','.join(extras)}]"

    if specs:
        line += f"{','.join(specs)}"

    return line
