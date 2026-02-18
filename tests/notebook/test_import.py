import textwrap

import pytest

from crunch_convert.notebook import ImportedRequirement, InconsistantLibraryVersionError, RequirementVersionParseError, extract_from_cells

from ._shared import cell


def test_normal():
    flatten = extract_from_cells([
        cell("a", "code", [
            "import hello",
            "import world # == 42",
            "import named # named-python == 42",
            "import extras # [big] >4.2",
        ])
    ])

    assert flatten.requirements == [
        ImportedRequirement(alias="hello"),
        ImportedRequirement(alias="world", specs=["==42"]),
        ImportedRequirement(alias="named", name="named-python", specs=["==42"]),
        ImportedRequirement(alias="extras", extras=["big"], specs=[">4.2"]),
    ]


def test_latest_version():
    flatten = extract_from_cells([
        cell("a", "code", [
            "import hello # @latest",
            "import world # pandas @latest",
        ])
    ])

    assert flatten.requirements == [
        ImportedRequirement(alias="hello"),
        ImportedRequirement(alias="world", name="pandas"),
    ]


def test_ignore_version():
    flatten = extract_from_cells([
        cell("a", "code", [
            "import hello # @ignore",
            "import world # pandas @ignore",
            "import hello2"
        ])
    ])

    assert flatten.requirements == [
        ImportedRequirement(alias="hello2"),
    ]


def test_inconsistant_version():
    with pytest.raises(InconsistantLibraryVersionError):
        extract_from_cells([
            cell("a", "code", [
                "import hello # == 1",
                "import hello # == 2",
            ])
        ])


def test_version_parse():
    with pytest.raises(RequirementVersionParseError):
        extract_from_cells([
            cell("a", "code", [
                "import hello # == aaa",
            ])
        ])


def test_one_specific_and_one_generic():
    flatten = extract_from_cells([
        cell("a", "code", [
            "import hello # == 1",
            "import hello",
        ])
    ])

    assert flatten.requirements == [
        ImportedRequirement(alias="hello", specs=["==1"])
    ]

    flatten = extract_from_cells([
        cell("a", "code", [
            "import hello",
            "import hello # == 1",
        ])
    ])

    assert flatten.requirements == [
        ImportedRequirement(alias="hello", specs=["==1"])
    ]

    flatten = extract_from_cells([
        cell("a", "code", [
            "import hello",
            "import hello # == 1",
            "import hello",
        ])
    ])

    assert flatten.requirements == [
        ImportedRequirement(alias="hello", specs=["==1"])
    ]


def test_import_in_try_except():
    flatten = extract_from_cells([
        cell("a", "code", [
            "try:",
            "    import hello",
            "except ImportError:",
            "    !pip install hello",
            "",
            "import hello",
        ])
    ])

    content = textwrap.dedent("""
        #try:
        #    import hello
        #except ImportError:
        #    pass  #!pip install hello

        import hello
    """).lstrip()

    assert content == flatten.source_code


def test_import_with_commented():
    flatten = extract_from_cells([
        cell("a", "code", [
            "from pandas import DataFrame #, Series",
            "import pandas # Import important tools"
        ])
    ])

    content = textwrap.dedent("""
        from pandas import DataFrame #, Series
        import pandas # Import important tools
    """).lstrip()

    assert content == flatten.source_code
