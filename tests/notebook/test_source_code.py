import textwrap
from typing import List, Tuple

import pytest
from parameterized import parameterized  # type: ignore

from crunch_convert import Warning, WarningCategory, WarningLocation
from crunch_convert.notebook import BadCellHandling, ImportedRequirement, NotebookCellParseError, extract_from_cells

from ._shared import cell


def test_normal():
    flatten = extract_from_cells([
        cell("a", "code", [
            "# Hello World",
        ]),
        cell("b", "code", [
            "a = 42",
            "def hello(x):",
            "    return x + 1",
        ]),
        cell("c", "code", [
            "a += 1",
            "",
            "class Model:",
            "    pass",
        ])
    ])

    content = _dedent("""
        # Hello World
        
        
        #a = 42
        def hello(x):
            return x + 1
        
        
        #a += 1
        
        class Model:
            pass
    """)

    assert content == flatten.source_code


def test_warning():
    flatten = extract_from_cells([
        cell("a", "code", [
            "# Hello World",
        ]),
        cell("b", "code", [
            "try:",
            "    import a",
            "except:",
            "    import b",
        ]),
        cell("c", "code", [
            "if True:",
            "    import c",
            "else:",
            "    import d",
            "    import e",
        ])
    ])

    content = _dedent("""
        # Hello World


        #try:
        #    import a
        #except:
        #    import b


        #if True:
        #    import c
        #else:
        #    import d
        #    import e
    """)

    assert content == flatten.source_code

    assert 2 == len(flatten.warnings)
    assert flatten.warnings[0] == Warning(
        category=WarningCategory.NESTED_IMPORT,
        message="found 2 nested imports in Try statement",
        location=WarningLocation(
            file="b",
            line=1,
            column=0,
        ),
    )
    assert flatten.warnings[1] == Warning(
        category=WarningCategory.NESTED_IMPORT,
        message="found 3 nested imports in If statement",
        location=WarningLocation(
            file="c",
            line=1,
            column=0,
        ),
    )


def test_ignore_error():
    flatten = extract_from_cells(
        [
            cell("a", "code", [
                "def a(): ...",
            ]),
            cell("b", "code", [
                "defhello(x):",
                "    return x + 1",
            ]),
            cell("c", "code", [
                "x = 2",
            ])
        ],
        bad_cell_handling=BadCellHandling.IGNORE,
    )

    content = _dedent("""
        def a(): ...


        #x = 2
    """)

    assert content == flatten.source_code


def test_comment_error():
    flatten = extract_from_cells(
        [
            cell("a", "code", [
                "def a(): ...",
            ]),
            cell("b", "code", [
                "defhello(x):",
                "    return x + 1",
            ]),
            cell("c", "code", [
                "x = 2",
            ])
        ],
        bad_cell_handling=BadCellHandling.COMMENT,
    )

    content = _dedent("""
        def a(): ...


        # bad cell: parser error: error at 1:12: expected one of !=, %, &, (, *, **, +, ,, -, ., /, //, ;, <, <<, <=, ==, >, >=, >>, @, NEWLINE, [, ^, and, if, in, is, not, or, |
        #defhello(x):
        #    return x + 1


        #x = 2
    """)

    assert content == flatten.source_code


def test_keep_commands():
    flatten = extract_from_cells([
        cell("a", "code", [
            "# @crunch/keep:on",
            "a = 42",
            "# @crunch/keep:off",
            "b = 42",
        ]),
        cell("b", "code", [
            "# @crunch/keep:on",
            "c = 42",
        ]),
        cell("b", "code", [
            "d = 42",
        ]),
    ])

    content = _dedent("""
        # @crunch/keep:on
        a = 42
        # @crunch/keep:off
        #b = 42


        # @crunch/keep:on
        c = 42


        #d = 42
    """)

    assert content == flatten.source_code


def test_keep_none_command():
    flatten = extract_from_cells([
        cell("a", "code", [
            "# @crunch/keep:none",
            "import a",
            "b = 42",
            "def c(): ...",
        ]),
        cell("b", "code", [
            "# @crunch/keep:none",
            "import d",
            "def e(): ...",
            "# @crunch/keep:off",
            "import f",
            "g = 42",
            "def h(): ...",
        ]),
    ])

    content = _dedent("""
        # @crunch/keep:none
        #import a
        #b = 42
        #def c(): ...


        # @crunch/keep:none
        #import d
        #def e(): ...
        # @crunch/keep:off
        import f
        #g = 42
        def h(): ...
    """)

    assert content == flatten.source_code
    assert flatten.requirements == [
        ImportedRequirement(alias="f")
    ]


def test_pip_escape():
    flatten = extract_from_cells([
        cell("a", "code", [
            "pip install pandas",
            "pip3 install pandas",
        ]),
    ])

    content = _dedent("""
        #pip install pandas
        #pip3 install pandas
    """)

    assert content == flatten.source_code


def test_invalid_syntax():
    with pytest.raises(NotebookCellParseError) as excinfo:
        extract_from_cells([
            cell("a", "code", [
                "invalid code",
            ]),
        ])

    assert "notebook code cell cannot be parsed" == str(excinfo.value)
    assert excinfo.value.parser_error is not None


@parameterized.expand([  # type: ignore
    (
        """

        """,
        None,
    ),

    (
        """
        def foo(x):
            if x > 0:
                return x
        """,
        None,
    ),

    (
        """
        class Foo:
            def bar(x):
                if x > 0:
                    return x
        """,
        None,
    ),

    ("del foo", "#del foo\n", ),
    ("foo = 42", "#foo = 42\n",),
    ("foo += 42", "#foo += 42\n",),
    ("foo: int = 42", "#foo: int = 42\n",),

    (
        """
        for x in range(10):
            if x > 0:
                print(x)
        """,
        """
        #for x in range(10):
        #    if x > 0:
        #        print(x)
        """,
    ),
    (
        """
        while True:
            if x > 0:
                print(x)
        """,
        """
        #while True:
        #    if x > 0:
        #        print(x)
        """,
    ),
    (
        """
        if x > 0:
            print(x)
        """,
        """
        #if x > 0:
        #    print(x)
        """,
    ),
    (
        """
        with open("file.txt") as f:
            print(f.read())
        """,
        """
        #with open("file.txt") as f:
        #    print(f.read())
        """,
    ),

    (
        """
        match x:
            case 42:
                print(x)
        """,
        """
        #match x:
        #    case 42:
        #        print(x)
        """,
    ),

    ("raise ValueError('x')", "#raise ValueError('x')\n",),
    (
        """
        try:
            pass
        except ValueError as e:
            print(e)
        """,
        """
        #try:
        #    pass
        #except ValueError as e:
        #    print(e)
        """,
    ),
    (
        """
        try:
            pass
        except* ValueError as e:
            print(e)
        """,
        """
        #try:
        #    pass
        #except* ValueError as e:
        #    print(e)
        """,
    ),
    ("assert False, 'oops'", "#assert False, 'oops'\n",),

    ("import a", "import a\n",),
    ("from a import b", "from a import b\n",),

    ("global x", "#global x\n",),
    ("pass", "#pass\n",),
    ("...", "#...\n",),

    ("x & y", "#x & y\n",),
    ("x - y", "#x - y\n",),
    ("-x", "#-x\n",),
    ("lambda x: ...", "#lambda x: ...\n",),
    ("x if y else z", "#x if y else z\n",),
    ("{ 'x': 'y' }", "#{ 'x': 'y' }\n",),
    (
        """
        {
            'x': 'y'
        }
        """,
        """
        #{
        #    'x': 'y'
        #}
        """,
    ),
    ("{ 'x', 'y' }", "#{ 'x', 'y' }\n",),
    (
        """
        {
            'x',
            'y'
        }
        """,
        """
        #{
        #    'x',
        #    'y'
        #}
        """,
    ),
    ("[ x for x in range(42) if x > 0 ]", "#[ x for x in range(42) if x > 0 ]\n",),
    (
        """
        [
            x
            for x in range(42)
            if x > 0
        ]
        """,
        """
        #[
        #    x
        #    for x in range(42)
        #    if x > 0
        #]
        """,
    ),
    ("{ x for x in range(42) if x > 0 }", "#{ x for x in range(42) if x > 0 }\n",),
    (
        """
        {
            x
            for x in range(42)
            if x > 0
        }
        """,
        """
        #{
        #    x
        #    for x in range(42)
        #    if x > 0
        #}
        """,
    ),
    ("{ x: x * 2 for x in range(42) if x > 0 }", "#{ x: x * 2 for x in range(42) if x > 0 }\n",),
    (
        """
        {
            x: x * 2
            for x in range(42)
            if x > 0
        }
        """,
        """
        #{
        #    x: x * 2
        #    for x in range(42)
        #    if x > 0
        #}
        """,
    ),
    ("(x for x in range(42) if x > 0)", "#(x for x in range(42) if x > 0)\n",),
    (
        """
        (
            x
            for x in range(42)
            if x > 0
        )
        """,
        """
        #(
        #    x
        #    for x in range(42)
        #    if x > 0
        #)
        """,
    ),
    ("await x", "#await x\n",),  # technically not correct
    ("yield x", "#yield x\n",),  # technically not correct
    ("yield from x", "#yield from x\n",),  # technically not correct

    ("x > y", "#x > y\n",),
    ("x(y)", "#x(y)\n",),
    ("f'hello {world!s}'", "#f'hello {world!s}'\n",),
    ("'hello ' 'world'", "#'hello ' 'world'\n",),
    ("'hello '\n'world'", "#'hello '\n#'world'\n",),

    ("x.y", "#x.y\n",),
    ("x[y]", "#x[y]\n",),
    ("x, *y = z", "#x, *y = z\n",),
    ("x", "#x\n",),
    ("[ 'x', 'y' ]", "#[ 'x', 'y' ]\n",),
    (
        """
        [
            'x',
            'y'
        ]
        """,
        """
        #[
        #    'x',
        #    'y'
        #]
        """,
    ),
    ("( 'x', 'y' )", "#( 'x', 'y' )\n",),
    (
        """
        (
            'x',
            'y'
        )
        """,
        """
        #(
        #    'x',
        #    'y'
        #)
        """,
    ),

    ("x[y:z]", "#x[y:z]\n",),

    ("x and y", "#x and y\n",),
    ("x or y", "#x or y\n",),

    ("not x", "#not x\n",),

    ("x in y", "#x in y\n",),
    ("x not in y", "#x not in y\n",),

    ("import a as b", "import a as b\n",),

    (
        """
        print(x(1
                + y))
        print()
        """,
        """
        #print(x(1
        #        + y))
        #print()
        """,
    ),
])
def test_syntax(cell_content: str, expected: str):
    cell_content = _dedent(cell_content)
    expected = _dedent(expected) if expected else cell_content

    flatten = extract_from_cells([
        cell("a", "code", cell_content.splitlines()),
    ])

    assert expected == flatten.source_code


@parameterized.expand([  # type: ignore
    (
        """
        def foo():
            return real_constant
        """,
        [],
    ),
    (
        """
        def foo():
            not_a_constant = a
            return not_a_constant
        """,
        [],
    ),
    (
        """
        def foo(not_a_constant):
            return not_a_constant
        """,
        [],
    ),
    (
        """
        class Foo:
            value = real_constant
        """,
        [],
    ),
    (
        """
        class Foo:
            not_a_constant = 1
            value = real_constant
        """,
        [],
    ),
    (
        """
        def foo():
            bar(not_a_constant=42)

        def foo():
            bar(not_a_constant=real_constant)
        """,
        [],
    ),
    (
        """
        def foo():
            return not_a_constant
        """,
        [
            (2, 11),
        ],
    ),
    (
        """
        def foo():
            return not_a_constant.a
        """,
        [
            (2, 11),
        ],
    ),
    (
        """
        def foo():
            a[not_a_constant] = 42
            a[not_a_constant] += 42
        """,
        [
            (2, 6),
            (3, 6),
        ],
    ),
    (
        """
        def foo():
            not_a_constant[a] = 42
            not_a_constant[a] += 42
        """,
        [
            (2, 4),
            (3, 4),
        ],
    ),
    (
        # technically do not works...
        """
        def foo():
            not_a_constant += 42
        """,
        [],
    ),
    (
        """
        class Foo:
            value = not_a_constant
        """,
        [
            (2, 12),
        ],
    ),
    (
        """
        def foo():
            global not_a_constant
            return not_a_constant
        """,
        [
            (3, 11),
        ],
    ),
    (
        """
        class Foo:
            def bar():
                return not_a_constant
        """,
        [
            (3, 15),
        ],
    ),
    (
        """
        def foo():
            return not_a_constant + not_a_constant + real_constant
        """,
        [
            (2, 11),
            (2, 28),
        ],
    ),
])
def test_scope(cell_content: str, expected_locations: List[Tuple[int, int]]):
    cell_content = _dedent(cell_content)

    initializer = _dedent("""
        not_a_constant = 42

        # @crunch/keep:on
        real_constant = 43
        # @crunch/keep:off

        not_a_constant_2 = 44
    """)

    flatten = extract_from_cells([
        cell("a", "code", initializer.splitlines()),
        cell("b", "code", cell_content.splitlines()),
    ])

    expected = (
        []
        if not expected_locations else
        [
            Warning(
                category=WarningCategory.GLOBAL_VARIABLE,
                message="found potential use of global variable `not_a_constant` that will be commented out",
                location=WarningLocation(
                    file="b",
                    line=expected_location[0],
                    column=expected_location[1],
                )
            )
            for expected_location in expected_locations
        ]
    )

    assert expected == flatten.warnings


def _dedent(text: str) -> str:
    return textwrap.dedent(text).lstrip()
