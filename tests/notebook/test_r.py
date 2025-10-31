import textwrap

from crunch_convert.notebook import ImportedRequirement, ImportedRequirementLanguage, extract_from_cells

from ._shared import cell


def test_normal():
    flatten = extract_from_cells([
        cell("a", "code", [
            "from rpy2.robjects.packages import importr",
            "base = importr('base')",
            "utils = importr('utils', d={})",
        ])
    ])

    assert flatten.requirements == [
        ImportedRequirement(alias="rpy2"),
        ImportedRequirement(alias="base", language=ImportedRequirementLanguage.R),
        ImportedRequirement(alias="utils", language=ImportedRequirementLanguage.R),
    ]


def test_normal_with_type():
    flatten = extract_from_cells([
        cell("a", "code", [
            "from rpy2.robjects.packages import importr",
            "base: dict = importr('base')",
            "utils: str = importr('utils', d={})",
        ])
    ])

    assert flatten.requirements == [
        ImportedRequirement(alias="rpy2"),
        ImportedRequirement(alias="base", language=ImportedRequirementLanguage.R),
        ImportedRequirement(alias="utils", language=ImportedRequirementLanguage.R),
    ]


def test_importr_not_commented():
    flatten = extract_from_cells([
        cell("a", "code", [
            "from rpy2.robjects.packages import importr",
            "a = 42",
            "base: dict = importr('base')",
            "utils: str = importr('utils', d={})",
        ]),
    ])

    content = textwrap.dedent("""
        from rpy2.robjects.packages import importr
        #a = 42
        base: dict = importr('base')
        utils: str = importr('utils', d={})
    """).lstrip()

    assert content == flatten.source_code


def test_not_right_function_name():
    flatten = extract_from_cells([
        cell("a", "code", [
            "from rpy2.robjects.packages import importr as r_import",
            "base = r_import('base')",
        ]),
    ])

    assert flatten.requirements == [
        ImportedRequirement(alias="rpy2"),
    ]


def test_not_call():
    _test_no_rimport_found("'base'")


def test_not_call_direct():
    _test_no_rimport_found("locals()['importr']('base')")


def test_not_call_value_string():
    _test_no_rimport_found("importr(base_name)")


def test_call_no_arguments():
    _test_no_rimport_found("importr()")


def test_call_argument_name_empty_string():
    _test_no_rimport_found("importr('')")
    _test_no_rimport_found("importr(\"\")")


def _test_no_rimport_found(line: str):
    flatten = extract_from_cells([
        cell("a", "code", [
            "from rpy2.robjects.packages import importr",
            f"base = {line}",
        ]),
    ])

    assert flatten.requirements == [
        ImportedRequirement(alias="rpy2"),
    ]
