from textwrap import dedent

from crunch_convert.requirements_txt import parse_from_file


def test_parse():
    content = dedent("""
    pytest==1.0.0
    pandas
    """)

    requirements = parse_from_file(
        file_content=content,
    )

    assert requirements[0].name == "pytest"
    assert requirements[0].extras == []
    assert requirements[0].specs == ["==1.0.0"]

    assert requirements[1].name == "pandas"
    assert requirements[1].extras == []
    assert requirements[1].specs == []
