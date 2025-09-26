from crunch_convert._model import RequirementLanguage
from crunch_convert.notebook._model import ImportedRequirement
from crunch_convert.requirements_txt._formatter import (
    format_files_from_imported, format_files_from_named, format_line)
from crunch_convert.requirements_txt._model import NamedRequirement
from crunch_convert.requirements_txt._whitelist import LocalWhitelist

from ._libraries import os_library, pandas_library, sklearn_library


def test_format_file_imported():
    whitelist = LocalWhitelist([
        sklearn_library,
        pandas_library,
        os_library,
    ])

    files = format_files_from_imported(
        requirements=[
            ImportedRequirement(alias="sklearn"),
            ImportedRequirement(alias="pandas", name="pandas"),
            ImportedRequirement(alias="xyz"),
            ImportedRequirement(alias="os"),
        ],
        header="header",
        whitelist=whitelist,
    )

    # dedent was not working...
    expected = "" \
        "# header\n" \
        "\n" \
        "## third-party\n" \
        "pandas\n" \
        "scikit-learn  # alias of sklearn\n" \
        "xyz\n" \
        "\n" \
        "## standard\n" \
        "#os\n"

    assert files[RequirementLanguage.PYTHON] == expected


def test_format_file_named():
    whitelist = LocalWhitelist([
        pandas_library,
        os_library,
    ])

    files = format_files_from_named(
        requirements=[
            NamedRequirement("pandas"),
            NamedRequirement("xyz"),
            NamedRequirement("os"),
        ],
        header="header",
        whitelist=whitelist,
    )

    # dedent was not working...
    expected = "" \
        "# header\n" \
        "\n" \
        "## third-party\n" \
        "pandas\n" \
        "xyz\n" \
        "\n" \
        "## standard\n" \
        "#os\n"

    assert files[RequirementLanguage.PYTHON] == expected


def test_format_line():
    assert "scikit-learn" == format_line("scikit-learn", None, [], [])
    assert "scikit-learn  # alias of sklearn" == format_line("scikit-learn", "sklearn", [], [])

    assert "scikit-learn[a]" == format_line("scikit-learn", None, ["a"], [])
    assert "scikit-learn[a]  # alias of sklearn" == format_line("scikit-learn", "sklearn", ["a"], [])

    assert "scikit-learn>1" == format_line("scikit-learn", None, [], [">1"])
    assert "scikit-learn>1  # alias of sklearn" == format_line("scikit-learn", "sklearn", [], [">1"])

    assert "scikit-learn[a]>1" == format_line("scikit-learn", None, ["a"], [">1"])
    assert "scikit-learn[a]>1  # alias of sklearn" == format_line("scikit-learn", "sklearn", ["a"], [">1"])
