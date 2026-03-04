from textwrap import dedent

import pytest

from crunch_convert.requirements_txt import RequirementParseError, parse_from_file


def test_parse():
    content = dedent("""
        pytest==1.0.0
        pandas
    """)

    requirements = parse_from_file(
        file_content=content,
    )

    assert len(requirements) == 2

    assert requirements[0].name == "pytest"
    assert requirements[0].extras == []
    assert requirements[0].specs == ["==1.0.0"]

    assert requirements[1].name == "pandas"
    assert requirements[1].extras == []
    assert requirements[1].specs == []


def test_parse_invalid():
    content = dedent("""
        pandas
        hello}
    """)

    with pytest.raises(RequirementParseError) as excinfo:
        parse_from_file(
            file_content=content,
        )

    assert "semicolon" in str(excinfo.value)
