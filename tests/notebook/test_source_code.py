import textwrap

import pytest
from parameterized import parameterized  # type: ignore

from crunch_convert.notebook import NotebookCellParseError, extract_from_cells

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

    content = textwrap.dedent("""
        # Hello World
        
        
        #a = 42
        def hello(x):
            return x + 1
        
        
        #a += 1
        
        class Model:
            pass
    """).lstrip()

    assert content == flatten.source_code


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
        ignore_bad_cells=True,
    )

    content = textwrap.dedent("""
        def a(): ...
        
        
        #x = 2
    """).lstrip()

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

    content = textwrap.dedent("""
        # @crunch/keep:on
        a = 42
        # @crunch/keep:off
        #b = 42


        # @crunch/keep:on
        c = 42


        #d = 42
    """).lstrip()

    assert content == flatten.source_code


def test_pip_escape():
    flatten = extract_from_cells([
        cell("a", "code", [
            "pip install pandas",
            "pip3 install pandas",
        ]),
    ])

    content = textwrap.dedent("""
        #pip install pandas
        #pip3 install pandas
    """).lstrip()

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
    ("nonlocal x", "#nonlocal x\n",),  # technically not correct
    ("pass", "#pass\n",),
    ("break", "#break\n",),  # technically not correct
    ("continue", "#continue\n",),  # technically not correct

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
    cell_content = textwrap.dedent(cell_content).lstrip()
    expected = textwrap.dedent(expected).lstrip() if expected else cell_content

    flatten = extract_from_cells([
        cell("a", "code", cell_content.splitlines()),
    ])

    assert expected == flatten.source_code
