from textwrap import dedent

import pytest
from parameterized import parameterized  # type: ignore

from crunch_convert import RequirementLanguage
from crunch_convert.requirements_txt import RequirementParseError, parse_from_file, parse_from_line


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


@parameterized.expand([  # type: ignore
    # https://pip.pypa.io/en/stable/reference/requirements-file-format/#global-options
    ("-i https://pypi.org/simple",),
    ("--index-url https://pypi.org/simple",),
    ("--extra-index-url https://pypi.org/simple",),
    ("--no-index",),
    ("-c constraints.txt",),
    ("--constraint constraints.txt",),
    ("-r requirements.txt",),
    ("--requirement requirements.txt",),
    ("-e .",),
    ("--editable .",),
    ("-f https://download.pytorch.org/whl/torch_stable.html",),
    ("--find-links https://download.pytorch.org/whl/torch_stable.html",),
    ("--no-binary :all:",),
    ("--no-binary :none:",),
    ("--no-binary psycopg2,lxml",),
    ("--only-binary :all:",),
    ("--only-binary :none:",),
    ("--only-binary psycopg2,lxml",),
    ("--prefer-binary",),
    ("--require-hashes",),
    ("--no-require-hashes",),
    ("--pre",),
    ("--all-releases",),
    ("--only-final :all:",),
    ("--only-final :none:",),
    ("--only-final psycopg2,lxml",),
    ("--trusted-host download.pytorch.org",),
    ("--use-feature fast-deps",),

    # https://pip.pypa.io/en/stable/reference/requirements-file-format/#per-requirement-options
    ("--hash=sha256:aaaa",),

    # Deprecated: https://github.com/pypa/pip/issues/8408
    ("-Z",),
    ("--always-unzip",),
])
def test_parse_flag(
    flag: str,
):
    line = dedent(f"""
        {flag} pandas
    """)

    with pytest.raises(RequirementParseError) as excinfo:
        parse_from_line(
            requirement_line=line,
        )

    assert "flags are not allowed" in str(excinfo.value)


def test_parse_commented_flag():
    line = dedent(f"""
        # --pre pandas
    """)

    parse_from_line(
        requirement_line=line,
    )


@parameterized.expand([  # type: ignore
    ("pandas@https://github.com/crunchdao/crunch-convert/zipball/master",),
    ("pandas@ https://github.com/crunchdao/crunch-convert/zipball/master",),
    ("pandas @https://github.com/crunchdao/crunch-convert/zipball/master",),
    ("pandas @ https://github.com/crunchdao/crunch-convert/zipball/master",),

    ("pandas@git+https://github.com/crunchdao/crunch-convert.git",),
    ("pandas@ git+https://github.com/crunchdao/crunch-convert.git",),
    ("pandas @git+https://github.com/crunchdao/crunch-convert.git",),
    ("pandas @ git+https://github.com/crunchdao/crunch-convert.git",),

    ("pandas@file:///crunch-convert/",),
    ("pandas @file:///crunch-convert/",),
    ("pandas@ file:///crunch-convert/",),
    ("pandas @ file:///crunch-convert/",),

    ("pandas[hello]@https://github.com/crunchdao/crunch-convert/zipball/master",),
])
def test_parse_url(
    at_expression: str,
):
    with pytest.raises(RequirementParseError) as excinfo:
        parse_from_line(
            requirement_line=at_expression,
        )

    assert "urls are not allowed" in str(excinfo.value)


def test_parse_marker():
    line = dedent(f"""
        pandas; python_version < "3.8"
    """)

    with pytest.raises(RequirementParseError) as excinfo:
        parse_from_line(
            requirement_line=line,
        )

    assert "markers are not allowed" in str(excinfo.value)


def test_parse_specs_r():
    line = dedent(f"""
        pandas>1
    """)

    with pytest.raises(RequirementParseError) as excinfo:
        parse_from_line(
            language=RequirementLanguage.R,
            requirement_line=line,
        )

    assert "extras and/or specs" in str(excinfo.value)


def test_parse_extras_r():
    line = dedent(f"""
        pandas[extra]
    """)

    with pytest.raises(RequirementParseError) as excinfo:
        parse_from_line(
            language=RequirementLanguage.R,
            requirement_line=line,
        )

    assert "extras and/or specs" in str(excinfo.value)
