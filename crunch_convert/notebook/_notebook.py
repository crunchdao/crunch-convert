import ast
import json
import os
import py_compile
import re
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, DefaultDict, Dict, List, Match, NamedTuple, Optional, Set, Tuple, Union, cast

import libcst
import libcst.metadata
import yaml

import requirements
from crunch_convert._model import RequirementLanguage, Warning, WarningCategory, WarningLocation
from crunch_convert.notebook._model import EmbeddedFile, ImportedRequirement
from crunch_convert.notebook._r import is_r_import
from crunch_convert.notebook._utils import cut_crlf, format_requirement_line, strip_hashes

_FAKE_PACKAGE_NAME = "x__fake_package_name__"
_PACKAGE_NAME_PATTERN = r"[a-zA-Z_][a-zA-Z0-9_-]*[a-zA-Z0-9]"
_LATEST_VERSION = "@latest"
_IGNORE_VERSION = "@ignore"

_DOT = "."
_KV_DIVIDER = "---"

_CRUNCH_KEEP_ON = "@crunch/keep:on"
_CRUNCH_KEEP_OFF = "@crunch/keep:off"
_CRUNCH_KEEP_NONE = "@crunch/keep:none"

JUPYTER_MAGIC_COMMAND_PATTERN = r"^(\s*?)(!|%|pip3? )"

_EMPTY_EXTRAS_AND_SPECS: Tuple[List[str], List[str]] = ([], [])


LogFunction = Callable[[str], None]


class BadCellHandling(Enum):
    RAISE = "raise"
    IGNORE = "ignore"
    COMMENT = "comment"


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


class _IgnoreImportType:
    pass


_IgnoreImport = _IgnoreImportType()


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
) -> Optional[Union[ImportInfo, _IgnoreImportType]]:
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

    version_part = line[match.start(2):].strip()

    if version_part == _IGNORE_VERSION:
        return _IgnoreImport

    if version_part == _LATEST_VERSION:
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
        ],
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

    import_info = _extract_import_version(log, comment_node)

    if import_info is _IgnoreImport:
        log(f"skip version: ignored by comment")
        return []

    if import_info is None:
        import_info = ImportInfo(None, [], [])

    (
        package_name,
        extras,
        specs,
    ) = cast(ImportInfo, import_info)

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
            language=RequirementLanguage.PYTHON,
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

_UNAFFECTED = (
    libcst.Module,

    libcst.Comment,
    libcst.EmptyLine,
    libcst.TrailingWhitespace,
)

_KEEP = (
    libcst.FunctionDef,
    libcst.ClassDef,

    libcst.SimpleStatementLine,

    *_UNAFFECTED,
    *_IMPORT,
)


class Comment(libcst.Comment):

    semicolon = False

    def _codegen_impl(self, state, default_semicolon=None) -> None:  # type: ignore
        super()._codegen_impl(state)  # type: ignore


class EmptyLine(libcst.EmptyLine):

    semicolon = False

    def _codegen_impl(self, state, default_semicolon=None) -> None:  # type: ignore
        super()._codegen_impl(state)  # type: ignore


class NestedImportFinder(libcst.CSTVisitor):

    def __init__(self):
        self.found = 0

    def on_visit(
        self,
        node: libcst.CSTNode,
    ) -> bool:
        if isinstance(node, _IMPORT):
            self.found += 1

        return True

    @staticmethod
    def count(node: libcst.CSTNode):
        finder = NestedImportFinder()
        node.visit(finder)

        return finder.found


class _KeepMode(Enum):
    NECESSARY = "necessary"
    EVERYTHING = "everything"
    NOTHING = "nothing"

    def should_leave_untouched(
        self,
        node: libcst.CSTNode,
        is_r_import_node: bool,
    ) -> bool:
        if self is _KeepMode.NECESSARY:
            return isinstance(node, _KEEP) or isinstance(node, _IMPORT) or is_r_import_node

        elif self is _KeepMode.EVERYTHING:
            return True

        elif self is _KeepMode.NOTHING:
            return isinstance(node, _UNAFFECTED)

        else:
            raise NotImplementedError(f"keep mode: {self}")

    @staticmethod
    def from_comment(comment: Optional[libcst.Comment]) -> Optional["_KeepMode"]:
        if comment is None:
            return None

        line = strip_hashes(comment.value)
        if line == _CRUNCH_KEEP_ON:
            return _KeepMode.EVERYTHING
        elif line == _CRUNCH_KEEP_OFF:
            return _KeepMode.NECESSARY
        elif line == _CRUNCH_KEEP_NONE:
            return _KeepMode.NOTHING
        else:
            return None


class _ConstantUsageChecker(libcst.CSTVisitor):
    METADATA_DEPENDENCIES = (
        libcst.metadata.ScopeProvider,
        libcst.metadata.PositionProvider,
    )

    def __init__(self):
        super().__init__()

        self.cell_id: Optional[str] = None

        self._surviving_globals: Set[str] = set()
        self._deleted_globals: Set[str] = set()

        self._current_keep_mode = _KeepMode.NECESSARY

    def visit_Module(self, node: libcst.Module) -> None:
        self._current_keep_mode = _KeepMode.NECESSARY

        if self.cell_id is None:
            raise Exception("cell_id should not be None at the beginning of visit_Module")

    def visit_EmptyLine(self, node: libcst.EmptyLine) -> None:
        keep_mode = _KeepMode.from_comment(node.comment)
        if keep_mode is not None:
            self._current_keep_mode = keep_mode

    def visit_Assign(self, node: libcst.Assign) -> None:
        for target in node.targets:
            self._extract_names_from_targets(target.target)

    def visit_AnnAssign(self, node: libcst.AnnAssign) -> None:
        self._extract_names_from_targets(node.target)

    def visit_AugAssign(self, node: libcst.AugAssign) -> None:
        self._extract_names_from_targets(node.target)

    def _extract_names_from_target(self, node: libcst.CSTNode) -> List[libcst.Name]:
        if isinstance(node, libcst.Name):
            return [node]

        elif isinstance(node, (libcst.Tuple, libcst.List)):
            names: List[libcst.Name] = []

            for element in node.elements:
                names.extend(self._extract_names_from_target(element.value))

            return names

        return []

    def _extract_names_from_targets(self, node: libcst.BaseAssignTargetExpression):
        for name_node in self._extract_names_from_target(node):
            self._process_global_binding(name_node)

    def _process_global_binding(self, name_node: libcst.Name) -> None:
        scope = self.get_metadata(libcst.metadata.ScopeProvider, name_node)
        if not isinstance(scope, libcst.metadata.GlobalScope):
            return

        name = name_node.value

        if self._current_keep_mode == _KeepMode.EVERYTHING:
            self._surviving_globals.add(name)
            self._deleted_globals.discard(name)
        else:
            self._deleted_globals.add(name)

    def _is_nested_in_non_global(self, scope: libcst.metadata.Scope) -> bool:
        while (
            isinstance(scope, libcst.metadata.ComprehensionScope)
            or (isinstance(scope, libcst.metadata.FunctionScope) and isinstance(scope.node, libcst.Lambda))
        ):
            scope = scope.parent

        return not isinstance(scope, libcst.metadata.GlobalScope)

    def analyze(self, cell_id: str, tree: libcst.metadata.MetadataWrapper):
        self.cell_id = cell_id

        tree.visit(self)

        self.cell_id = None

    def check_references(self, cell_id: str, tree: libcst.metadata.MetadataWrapper) -> List[Warning]:
        warnings: List[Warning] = []

        if not self._deleted_globals:
            return warnings

        scopes = set(tree.resolve(libcst.metadata.ScopeProvider).values())
        positions = tree.resolve(libcst.metadata.PositionProvider)

        for scope in scopes:
            if scope is None or isinstance(scope, libcst.metadata.GlobalScope):
                continue

            if not self._is_nested_in_non_global(scope):
                continue

            for access in scope.accesses:
                if not isinstance(access.node, libcst.Name):
                    continue

                name = access.node.value
                if name not in self._deleted_globals:
                    continue

                referents = access.referents
                has_any_global_assign = any(
                    isinstance(assignment.scope, libcst.metadata.GlobalScope)
                    for assignment in referents
                )
                if len(referents) and not has_any_global_assign:
                    continue

                position = positions[access.node].start

                warnings.append(Warning(
                    category=WarningCategory.GLOBAL_VARIABLE,
                    message=f"found potential use of global variable `{name}` that will be commented out",
                    location=WarningLocation(
                        file=cell_id,
                        line=position.line,
                        column=position.column,
                    ),
                ))

        return warnings


class _CommentTransformer(libcst.CSTTransformer):
    METADATA_DEPENDENCIES = (libcst.metadata.PositionProvider,)

    METHOD_GROUP = "group"
    METHOD_LINE = "line"

    def __init__(
        self,
        cell_id: str,
        tree: libcst.Module,
    ):
        self.cell_id = cell_id
        self.tree = tree

        self.import_and_comment_nodes: List[Tuple[ImportNodeType, Optional[libcst.Comment]]] = []
        self.r_import_names: List[str] = []

        self._method_stack: List[str] = []
        self._previous_import_node: Optional[ImportNodeType] = None
        self._keep_mode = _KeepMode.NECESSARY

        self.warnings: List[Warning] = []

    def on_visit(
        self,
        node: libcst.CSTNode,
    ) -> bool:
        # print("visit", type(node), "\\n".join(self._to_lines(node)))

        if isinstance(node, (libcst.Module, libcst.SimpleStatementLine)):
            self._method_stack.append(self.METHOD_GROUP)
            return True

        elif isinstance(node, libcst.BaseCompoundStatement):
            found_imports = NestedImportFinder.count(node)
            if found_imports:
                position = self.get_metadata(libcst.metadata.PositionProvider, node).start  # type: ignore
                assert isinstance(position, libcst.metadata.CodePosition)

                self.warnings.append(Warning(
                    category=WarningCategory.NESTED_IMPORT,
                    message=f"found {found_imports} nested import{'s' if found_imports > 1 else ''} in {node.__class__.__name__} statement",
                    location=WarningLocation(
                        file=self.cell_id,
                        line=position.line,
                        column=position.column,
                    ),
                ))

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

        is_r_import_node = False
        if self._keep_mode != _KeepMode.NOTHING:
            is_r_import_node = self._handle_imports(original_node) or False

        if isinstance(original_node, libcst.EmptyLine):
            keep_mode = _KeepMode.from_comment(original_node.comment)
            if keep_mode is not None:
                self._keep_mode = keep_mode

        if self._keep_mode.should_leave_untouched(original_node, is_r_import_node):
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

    def _handle_imports(self, original_node: libcst.CSTNode) -> Optional[bool]:
        """
        :rtype: bool | None: True if the node is an R import, None otherwise
        """

        if isinstance(original_node, _IMPORT):
            self._previous_import_node = original_node
            return

        r_requirement = is_r_import(original_node)
        if r_requirement is not None:
            self.r_import_names.append(r_requirement)
            self._previous_import_node = cast(ImportNodeType, original_node)
            return True

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

    def _to_lines(self, node: libcst.CSTNode) -> List[str]:
        return self.tree.code_for_node(node).splitlines()


def _jupyter_replacer(match: Match[str]) -> str:
    spaces = match.group(1)
    command = match.group(2)

    if len(spaces):
        return f"{spaces}pass  #{command}"

    return f"#{command}"


class _NotebookProcessor:

    def __init__(
        self,
        bad_cell_handling: BadCellHandling,
        print: LogFunction,
    ):
        self.bad_cell_handling = bad_cell_handling
        self.print = print

        self.module: List[str] = []

        self.all_warnings: List[Warning] = []
        self.cell_id_order: List[str] = []

        self.embedded_files: Dict[str, EmbeddedFile] = {}
        self.imported_requirements: DefaultDict[RequirementLanguage, Dict[str, ImportedRequirement]] = defaultdict(dict)

        self.constant_usage_checker = _ConstantUsageChecker()

        self.cell_ids_and_trees: List[Tuple[str, libcst.metadata.MetadataWrapper]] = []

    def extract_cell(
        self,
        cell: Dict[str, Any],
        cell_id: str,
    ):
        def log(message: str):
            self.print(f"convert {cell_id}: {message}")

        cell_source = cell["source"]
        if isinstance(cell_source, str):
            cell_source = cell_source.split("\n")

        cell_source = [
            cut_crlf(line)
            for line in cell_source
        ]

        cell_type = cell["cell_type"]
        if cell_type == "code":
            self._extract_code_cell(
                log=log,
                cell_id=cell_id,
                cell_source=cell_source,
            )
        elif cell_type == "markdown":
            self._extract_markdown_cell(
                log=log,
                cell_source=cell_source,
            )
        else:
            log(f"skip since unknown type: {cell_type}")

    def _extract_code_cell(
        self,
        *,
        log: LogFunction,
        cell_id: str,
        cell_source: List[str],
    ):
        source = "\n".join(
            re.sub(JUPYTER_MAGIC_COMMAND_PATTERN, _jupyter_replacer, line)
            for line in cell_source
        )

        if not len(source):
            log(f"skip since empty")
            return

        try:
            original_tree = libcst.parse_module(source)
        except libcst.ParserSyntaxError as error:
            log(f"failed to parse: {error.message}")

            if BadCellHandling.IGNORE == self.bad_cell_handling:
                log(f"skipped")
                return

            elif BadCellHandling.COMMENT == self.bad_cell_handling:
                log(f"commented out")

                if len(self.module):
                    self.module.append(f"\n")

                self.module.append(f"# bad cell: {error.message}")
                self.module.append(re.sub("^", "#", source, flags=re.MULTILINE))
                return

            raise NotebookCellParseError(
                f"notebook code cell cannot be parsed",
                str(error),
                source,
            ) from error

        tree = libcst.metadata.MetadataWrapper(original_tree)
        self.cell_ids_and_trees.append((cell_id, tree))

        self.constant_usage_checker.analyze(cell_id, tree)

        transformer = _CommentTransformer(cell_id, original_tree)
        tree = tree.visit(transformer)

        self.cell_id_order.append(cell_id)
        self.all_warnings.extend(transformer.warnings)

        for import_node, comment_node in transformer.import_and_comment_nodes:
            new_requirements = _convert_python_import(log, import_node, comment_node)

            _add_to_packages(
                self.imported_requirements[RequirementLanguage.PYTHON],
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
                self.imported_requirements[RequirementLanguage.R],
                new_requirements,
                log,
            )

        lines = tree.code.strip("\r\n").splitlines()
        if len(lines):
            log(f"used {len(lines)} line(s)")

            if len(self.module):
                self.module.append(f"\n")

            self.module.append("\n".join(lines))
        else:
            log(f"skip since empty")

    def _extract_markdown_cell(
        self,
        log: LogFunction,
        cell_source: List[str],
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

        previous = self.embedded_files.get(lower_file_path)
        if previous is not None:
            raise NotebookCellParseError(
                f"file `{file_path}` specified multiple time",
                f"file `{file_path}` is conflicting with `{previous.path}`",
                get_full_source(),
            )

        content = "\n".join(iterator).strip()

        self.embedded_files[lower_file_path] = EmbeddedFile(
            path=file_path,
            normalized_path=normalized_file_path,
            content=content,
        )

        log(f"embed {lower_file_path}: {len(content)} characters")

    def finalize(self):
        for cell_id, tree in self.cell_ids_and_trees:
            warnings = self.constant_usage_checker.check_references(cell_id, tree)
            self.all_warnings.extend(warnings)

        self.all_warnings.sort(key=lambda warning: (
            self.cell_id_order.index(warning.location.file),
            warning.location.line,
            warning.location.column
        ))

        if len(self.module) and self.module[-1] != "":
            self.module.append("")

        return self.all_warnings, "\n".join(self.module)


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
    warnings: List[Warning]


def extract_from_cells(
    cells: List[Any],
    *,
    print: Optional[LogFunction] = print,  # pyright: ignore[reportRedeclaration]
    validate: bool = True,
    bad_cell_handling: BadCellHandling = BadCellHandling.RAISE,
) -> FlattenNotebook:
    if print is None:
        def print(_): return None

    processor = _NotebookProcessor(
        bad_cell_handling=bad_cell_handling,
        print=print,  # pyright: ignore[reportUnknownArgumentType]
    )

    for index, cell in enumerate(cells):
        cell_id = cell["metadata"].get("id") or f"cell_{index}"

        try:
            processor.extract_cell(
                cell=cell,
                cell_id=cell_id,
            )
        except NotebookCellParseError as error:
            error.cell_index = index
            error.cell_id = cell_id
            raise

    (
        all_warnings,
        source_code,
    ) = processor.finalize()

    if validate:
        _validate(source_code)

    return FlattenNotebook(
        source_code=source_code,
        embedded_files=list(processor.embedded_files.values()),
        requirements=[
            requirement
            for requirements in processor.imported_requirements.values()
            for requirement in list(requirements.values())
        ],
        warnings=all_warnings,
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
