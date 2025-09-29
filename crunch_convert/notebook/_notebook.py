import ast
import json
import os
import py_compile
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import (Any, Callable, DefaultDict, Dict, List, Match, NamedTuple,
                    Optional, Set, Tuple, Union, cast)

import libcst
import yaml

import requirements
from crunch_convert._model import RequirementLanguage
from crunch_convert.notebook._model import EmbeddedFile, ImportedRequirement
from crunch_convert.notebook._r import is_r_import
from crunch_convert.notebook._utils import (cut_crlf, format_requirement_line,
                                            strip_hashes)

_FAKE_PACKAGE_NAME = "x__fake_package_name__"
_PACKAGE_NAME_PATTERN = r"[a-zA-Z_][a-zA-Z0-9_-]*[a-zA-Z0-9]"
_LAST_VERSION = "@latest"

_DOT = "."
_KV_DIVIDER = "---"

_CRUNCH_KEEP_ON = "@crunch/keep:on"
_CRUNCH_KEEP_OFF = "@crunch/keep:off"

JUPYTER_MAGIC_COMMAND_PATTERN = r"^(\s*?)(!|%|pip3? )"

_EMPTY_EXTRAS_AND_SPECS: Tuple[List[str], List[str]] = ([], [])


LogFunction = Callable[[str], None]


def strip_packages(name: str):
    if name.startswith(_DOT):
        return None  # just in case, but should not happen

    if _DOT not in name:
        return name

    index = name.index(_DOT)
    return name[:index]


class ConverterError(ValueError):
    pass


class NotebookCellParseError(ConverterError):

    def __init__(
        self,
        message: str,
        parser_error: Optional[str],
        cell_source: str,
        cell_index: Optional[int] = None,
        cell_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.parser_error = parser_error
        self.cell_index = cell_index
        self.cell_id = cell_id
        self.cell_source = cell_source


class RequirementVersionParseError(ConverterError):

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ImportInfo(NamedTuple):
    name: Optional[str]
    extras: List[str]
    specs: List[str]

    def __str__(self) -> str:
        return format_requirement_line(self.name or "", self.extras, self.specs)


class InconsistantLibraryVersionError(ConverterError):

    def __init__(
        self,
        message: str,
        package_name: str,
        old: ImportInfo,
        new: ImportInfo,
    ) -> None:
        super().__init__(message)
        self.package_name = package_name
        self.old = old
        self.new = new


def _extract_import_version(
    log: LogFunction,
    comment_node: Optional[libcst.Comment]
) -> Optional[ImportInfo]:
    if comment_node is None:
        log(f"skip version: no comment")
        return None

    line = strip_hashes(comment_node.value)
    if not line:
        log(f"skip version: comment empty")
        return None

    match = re.match(r"^(" + _PACKAGE_NAME_PATTERN + r")?\s*([@\[><=~])", line)
    if not match:
        log(f"skip version: line not matching: `{line}`")
        return None

    user_package_name = match.group(1)
    test_package_name = user_package_name or _FAKE_PACKAGE_NAME

    version_part: str = line[match.start(2):]
    if version_part == _LAST_VERSION:
        return ImportInfo(user_package_name or None, [], [])

    line = f"{test_package_name} {version_part}"

    try:
        requirement = next(requirements.parse(line), None)
        if requirement is None:
            log(f"skip version: parse returned nothing: `{line}`")
            return None
    except Exception as error:
        raise RequirementVersionParseError(
            f"version cannot be parsed: {error}"
        ) from error

    if requirement.name != test_package_name:
        # package has been modified somehow
        raise RequirementVersionParseError(
            f"name must be `{test_package_name}` and not `{requirement.name}`"
        )

    return ImportInfo(
        user_package_name or None,
        list(requirement.extras),
        [
            f"{operator}{semver}"
            for operator, semver in requirement.specs
        ]
    )


ImportNodeType = Union[libcst.Import, libcst.ImportFrom]


def _evaluate_name(node: libcst.CSTNode) -> str:
    if isinstance(node, libcst.Name):
        return node.value
    elif isinstance(node, libcst.Attribute):
        return f"{_evaluate_name(node.value)}.{node.attr.value}"
    else:
        raise Exception("Logic error!")


def _convert_python_import(
    log: LogFunction,
    import_node: ImportNodeType,
    comment_node: Optional[libcst.Comment]
) -> List[ImportedRequirement]:
    if isinstance(import_node, libcst.Import):
        paths = [
            _evaluate_name(alias.name)
            for alias in import_node.names
        ]
    elif isinstance(import_node, libcst.ImportFrom) and import_node.module is not None:  # type: ignore
        paths = [_evaluate_name(import_node.module)]
    else:
        return []

    (
        package_name,
        extras,
        specs,
    ) = _extract_import_version(
        log,
        comment_node
    ) or (None, [], [])

    names: Set[str] = set()
    for path in paths:
        name = strip_packages(path)
        if name:
            names.add(name)

    return [
        ImportedRequirement(
            alias=name,
            name=package_name,
            extras=extras,
            specs=specs,
            language=RequirementLanguage.PYTHON
        )
        for name in names
    ]


def _add_to_packages(
    imported_requirements: Dict[str, ImportedRequirement],
    new_requirements: List[ImportedRequirement],
    log: LogFunction,
):
    for new in new_requirements:
        package_name = new.alias

        if package_name in imported_requirements:
            current = imported_requirements[package_name]

            success, message = current.merge(new)
            if not success:
                raise InconsistantLibraryVersionError(
                    f"inconsistant requirements for the same package: {message}",
                    package_name,
                    ImportInfo(current.name, current.extras, current.specs),
                    ImportInfo(new.name, new.extras, new.specs),
                )
        else:
            imported_requirements[package_name] = new

        if new.extras_and_specs != _EMPTY_EXTRAS_AND_SPECS:
            log(f"found version: {package_name}: {new}")


_IMPORT = (
    libcst.Import,
    libcst.ImportFrom,
)

_KEEP = (
    libcst.Module,

    libcst.FunctionDef,
    libcst.ClassDef,

    libcst.Comment,
    libcst.EmptyLine,
    libcst.TrailingWhitespace,

    libcst.SimpleStatementLine,
)


class Comment(libcst.Comment):

    semicolon = False

    def _codegen_impl(self, state, default_semicolon=None) -> None:  # type: ignore
        super()._codegen_impl(state)  # type: ignore


class EmptyLine(libcst.EmptyLine):

    semicolon = False

    def _codegen_impl(self, state, default_semicolon=None) -> None:  # type: ignore
        super()._codegen_impl(state)  # type: ignore


class CommentTransformer(libcst.CSTTransformer):

    METHOD_GROUP = "group"
    METHOD_LINE = "line"

    def __init__(self, tree: libcst.Module):
        self.tree = tree

        self.import_and_comment_nodes: List[Tuple[ImportNodeType, Optional[libcst.Comment]]] = []
        self.r_import_names: List[str] = []

        self._method_stack: List[str] = []
        self._previous_import_node: Optional[ImportNodeType] = None
        self._auto_comment = True

    def on_visit(
        self,
        node: libcst.CSTNode,
    ) -> bool:
        # print("visit", type(node), "\\n".join(self._to_lines(node)))

        if isinstance(node, (libcst.Module, libcst.SimpleStatementLine)):
            self._method_stack.append(self.METHOD_GROUP)
            return True
        elif isinstance(node, libcst.BaseCompoundStatement):
            self._method_stack.append(self.METHOD_GROUP)
            return False
        else:
            self._method_stack.append(self.METHOD_LINE)
            return False

    def on_leave(
        self,
        original_node: libcst.CSTNode,
        updated_node: libcst.CSTNode
    ) -> Union[libcst.CSTNode, libcst.RemovalSentinel, libcst.FlattenSentinel[libcst.CSTNode]]:
        method = self._method_stack.pop()
        # print("leave", type(original_node), method)

        if isinstance(original_node, _IMPORT):
            self._previous_import_node = original_node
            return updated_node

        r_requirement = is_r_import(original_node)
        if r_requirement is not None:
            self.r_import_names.append(r_requirement)
            self._previous_import_node = cast(ImportNodeType, original_node)
            return updated_node

        if self._previous_import_node is not None:
            import_node, self._previous_import_node = self._previous_import_node, None

            if isinstance(original_node, libcst.TrailingWhitespace) and original_node.comment:
                self.import_and_comment_nodes.append(
                    (import_node, original_node.comment)
                )
            else:
                self.import_and_comment_nodes.append(
                    (import_node, None)
                )

        if isinstance(original_node, libcst.EmptyLine) and original_node.comment:
            comment = strip_hashes(original_node.comment.value)
            if comment == _CRUNCH_KEEP_ON:
                self._auto_comment = False
            elif comment == _CRUNCH_KEEP_OFF:
                self._auto_comment = True

            return updated_node

        if not self._auto_comment or isinstance(original_node, _KEEP):
            return updated_node

        nodes: List[libcst.CSTNode] = []

        # control flow blocks have their comment attached to them
        if isinstance(original_node, libcst.BaseCompoundStatement) and original_node.leading_lines:
            nodes.extend(original_node.leading_lines)

            original_node = original_node.with_changes(
                leading_lines=libcst.FlattenSentinel([])
            )

        if method == self.METHOD_GROUP:
            nodes.extend(
                EmptyLine(comment=Comment(f"#{line}"))
                for line in self._to_lines(original_node)
            )

        elif method == self.METHOD_LINE:
            if isinstance(original_node, libcst.BaseSmallStatement):
                lines = self._to_lines(original_node)

                if len(lines) == 1:
                    nodes.append(Comment(f"#{lines[0]}"))
                else:
                    nodes.extend(
                        EmptyLine(comment=Comment(f"#{line}"))
                        for line in lines[:-1]
                    )
                    nodes.append(Comment(f"#{lines[-1]}"))
            else:
                nodes.extend(
                    Comment(f"#{line}")
                    for line in self._to_lines(original_node)
                )

        else:
            raise NotImplementedError(f"method: {method}")

        return libcst.FlattenSentinel(nodes)

    def _to_lines(self, node: libcst.CSTNode) -> List[str]:
        return self.tree.code_for_node(node).splitlines()


def _jupyter_replacer(match: Match[str]) -> str:
    spaces = match.group(1)
    command = match.group(2)

    if len(spaces):
        return f"{spaces}pass  #{command}"

    return f"#{command}"


def _extract_code_cell(
    cell_source: List[str],
    log: LogFunction,
    module: List[str],
    imported_requirements: DefaultDict[RequirementLanguage, Dict[str, ImportedRequirement]],
):
    source = "\n".join(
        re.sub(JUPYTER_MAGIC_COMMAND_PATTERN, _jupyter_replacer, line)
        for line in cell_source
    )

    if not len(source):
        log(f"skip since empty")
        return

    try:
        tree = libcst.parse_module(source)
    except libcst.ParserSyntaxError as error:
        log(f"failed to parse: {error.message}")

        raise NotebookCellParseError(
            f"notebook code cell cannot be parsed",
            str(error),
            source,
        ) from error

    transformer = CommentTransformer(tree)
    tree = tree.visit(transformer)

    for import_node, comment_node in transformer.import_and_comment_nodes:
        new_requirements = _convert_python_import(log, import_node, comment_node)

        _add_to_packages(
            imported_requirements[RequirementLanguage.PYTHON],
            new_requirements,
            log,
        )

    if True:
        new_requirements = [
            ImportedRequirement(
                alias=name,
                language=RequirementLanguage.R
            )
            for name in transformer.r_import_names
        ]

        _add_to_packages(
            imported_requirements[RequirementLanguage.R],
            new_requirements,
            log,
        )

    lines = tree.code.strip("\r\n").splitlines()
    if len(lines):
        log(f"used {len(lines)} line(s)")

        if len(module):
            module.append(f"\n")

        module.append("\n".join(lines))
    else:
        log(f"skip since empty")


def _extract_markdown_cell(
    cell_source: List[str],
    log: LogFunction,
    embedded_files: Dict[str, EmbeddedFile],
):
    if not len(cell_source):
        log(f"skip since empty")
        return

    def get_full_source():
        return "\n".join(cell_source)

    iterator = iter(cell_source)

    if next(iterator) != _KV_DIVIDER:
        return

    source: Union[List[str], str] = []
    valid = True

    try:
        for line in iterator:
            if not line.strip():
                valid = False
                break

            if line == _KV_DIVIDER:
                break

            source.append(line)
        else:
            valid = False

        if not valid:
            return

        source = "\n".join(source)

        configuration: Dict[str, Any] = yaml.safe_load(source)

        if not isinstance(configuration, dict):  # type: ignore
            raise ValueError("root must be a dict")
    except Exception as error:
        log(f"failed to parse: {error}")

        if isinstance(source, list):
            source = "\n".join(source)

        raise NotebookCellParseError(
            f"notebook markdown cell cannot be parsed",
            str(error),
            source,
        ) from error

    file_path = configuration.get("file")
    if not isinstance(file_path, str) or not file_path.strip():
        raise NotebookCellParseError(
            f"file not specified",
            None,
            get_full_source(),
        )

    normalized_file_path = os.path.normpath(file_path).replace("\\", "/")
    lower_file_path = normalized_file_path.lower()

    previous = embedded_files.get(lower_file_path)
    if previous is not None:
        raise NotebookCellParseError(
            f"file `{file_path}` specified multiple time",
            f"file `{file_path}` is conflicting with `{previous.path}`",
            get_full_source(),
        )

    content = "\n".join(iterator).strip()

    embedded_files[lower_file_path] = EmbeddedFile(
        path=file_path,
        normalized_path=normalized_file_path,
        content=content,
    )

    log(f"embed {lower_file_path}: {len(content)} characters")


def _validate(source_code: str):
    try:
        ast.parse(source_code)
    except SyntaxError as error:
        parser_error = py_compile.PyCompileError(
            error.__class__,
            error,
            "<converted_output>",
        )

        raise NotebookCellParseError(
            f"converted notebook code cell cannot be compiled",
            str(parser_error),
            source_code,
            -1,
            parser_error.file
        )


@dataclass(frozen=True)
class FlattenNotebook:
    source_code: str
    embedded_files: List[EmbeddedFile]
    requirements: List["ImportedRequirement"]


def extract_from_cells(
    cells: List[Any],
    *,
    print: Optional[LogFunction] = print,
    validate: bool = True,
) -> FlattenNotebook:
    if print is None:
        def print(_): return None

    imported_requirements: DefaultDict[RequirementLanguage, Dict[str, ImportedRequirement]] = defaultdict(dict)
    module: List[str] = []
    embed_files: Dict[str, EmbeddedFile] = {}

    for index, cell in enumerate(cells):
        cell_id = cell["metadata"].get("id") or f"cell_{index}"

        def log(message: str):
            print(f"convert {cell_id}: {message}")

        cell_source = cell["source"]
        if isinstance(cell_source, str):
            cell_source = cell_source.split("\n")

        cell_source = [
            cut_crlf(line)
            for line in cell_source
        ]

        try:
            cell_type = cell["cell_type"]
            if cell_type == "code":
                _extract_code_cell(cell_source, log, module, imported_requirements)
            elif cell_type == "markdown":
                _extract_markdown_cell(cell_source, log, embed_files)
            else:
                log(f"skip since unknown type: {cell_type}")
                continue
        except NotebookCellParseError as error:
            error.cell_index = index
            error.cell_id = cell_id
            raise

    module.append("")
    source_code = "\n".join(module)

    if validate:
        _validate(source_code)

    return FlattenNotebook(
        source_code=source_code,
        embedded_files=list(embed_files.values()),
        requirements=[
            requirement
            for requirements in imported_requirements.values()
            for requirement in list(requirements.values())
        ],
    )


def extract_from_file(
    path: str,
    *,
    print: Optional[LogFunction] = None,
    validate: bool = True,
) -> FlattenNotebook:
    with open(path) as fd:
        notebook = json.load(fd)

    cells = notebook["cells"]

    return extract_from_cells(
        cells,
        print=print,
        validate=validate,
    )
