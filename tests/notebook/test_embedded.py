import pytest

from crunch_convert.notebook import EmbeddedFile, NotebookCellParseError, extract_from_cells

from ._shared import cell


def test_normal():
    flatten = extract_from_cells([
        cell("a", "markdown", [
            "---",
            "file: ./a.txt",
            "---",
            "",
            "# Hello World",
            "from a embed markdown file",
        ])
    ])

    assert flatten.source_code == ""
    assert flatten.embedded_files == [
        EmbeddedFile(
            path="./a.txt",
            normalized_path="a.txt",
            content="# Hello World\nfrom a embed markdown file"
        )
    ]
    assert flatten.requirements == []


def test_root_not_a_dict():
    with pytest.raises(NotebookCellParseError) as excinfo:
        extract_from_cells([
            cell("a", "markdown", [
                "---",
                "- 42",
                "---",
                "# Hello World",
            ])
        ])

    assert "notebook markdown cell cannot be parsed" == str(excinfo.value)
    assert "root must be a dict" == excinfo.value.parser_error


def test_file_not_specified():
    with pytest.raises(NotebookCellParseError) as excinfo:
        extract_from_cells([
            cell("a", "markdown", [
                "---",
                "file: readme.md",
                "---",
                "# Hello World",
            ]),
            cell("b", "markdown", [
                "---",
                "file: readme.md",
                "---",
                "# Hello World",
            ])
        ])

    assert "file `readme.md` specified multiple time" == str(excinfo.value)


def test_separator():
    flatten = extract_from_cells([
        cell("a", "markdown", [
            "---",
            "<!-- content -->",
        ])
    ])

    assert 0 == len(flatten.embedded_files)
    assert "" == flatten.source_code

    flatten = extract_from_cells([
        cell("a", "markdown", [
            "---",
            "",  # empty line
            "unrelated",
            "---",
        ])
    ])

    assert 0 == len(flatten.embedded_files)
    assert "" == flatten.source_code
