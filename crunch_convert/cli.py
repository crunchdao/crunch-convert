import json
import os
from typing import Optional, TextIO, cast

import click

from crunch_convert.__version__ import __version__
from crunch_convert._utils import MockedWriteTextIO
from crunch_convert.notebook import (ConverterError,
                                     InconsistantLibraryVersionError,
                                     NotebookCellParseError, extract_from_file)
from crunch_convert.notebook._utils import print_indented
from crunch_convert.requirements_txt import (CrunchHubWhitelist,
                                             LocalSitePackageVersionFinder,
                                             format_files_from_imported,
                                             format_files_from_named, freeze,
                                             parse_from_file)


@click.group()
@click.version_option(__version__, package_name="__version__.__title__")
def cli():
    pass  # pragma: no cover


@cli.command(help="Convert a notebook to a python script.")
@click.option("--override", is_flag=True, help="Force overwrite of the python file.")
@click.option("--write-requirements", is_flag=True, help="Write the requirements.txt files.")
@click.option("--write-embedded-files", is_flag=True, help="Write the embedded files.")
@click.option("--no-freeze", is_flag=True, help="Don't freeze the requirements in requirements.txt with locally installed versions.")
@click.argument("notebook-file-path", required=True)
@click.argument("python-file-path", default="main.py")
def notebook(
    override: bool,
    write_requirements: bool,
    write_embedded_files: bool,
    no_freeze: bool,
    notebook_file_path: str,
    python_file_path: str,
):
    print("convert file:", notebook_file_path)

    try:
        flatten = extract_from_file(
            notebook_file_path,
            print=print,
            validate=True,
        )
    except IOError as error:
        print(f"{notebook_file_path}: cannot read notebook file: {error}")
        raise click.Abort()
    except json.JSONDecodeError as error:
        print(f"{notebook_file_path}: cannot parse notebook file: {error}")
        raise click.Abort()
    except ConverterError as error:
        print(f"{notebook_file_path}: convert failed: {error}")

        if isinstance(error, NotebookCellParseError):
            print(f"  cell: {error.cell_id} ({error.cell_index})")
            print(f"  source:")
            print_indented(error.cell_source)
            print(f"  parser error:")
            print_indented(error.parser_error or "None")

        elif isinstance(error, InconsistantLibraryVersionError):
            print(f"  package name: {error.package_name}")
            print(f"  first version: {error.old}")
            print(f"  other version: {error.new}")

        raise click.Abort()

    with _open_with_consent(override, python_file_path) as fd:
        fd.write(flatten.source_code)

    if write_requirements:
        whitelist = CrunchHubWhitelist()
        version_finder = LocalSitePackageVersionFinder()

        requirements_files = format_files_from_imported(
            flatten.requirements,
            header="extracted from a notebook",
            whitelist=whitelist,
        )

        for requirement_language, content in requirements_files.items():
            real_content: str = content
            original_content: Optional[str] = None

            if not no_freeze:
                requirements = parse_from_file(
                    language=requirement_language,
                    file_content=content
                )

                for requirement in requirements:
                    print("freeze requirements:", requirement.name, requirement.extras, requirement.specs)

                frozen_requirements = freeze(
                    requirements=requirements,
                    freeze_only_if_required=False,
                    version_finder=version_finder,
                )

                if requirements != frozen_requirements:
                    frozen_content = format_files_from_named(
                        frozen_requirements,
                        header="frozen from local site-packages",
                        whitelist=whitelist,
                    )

                    real_content = frozen_content[requirement_language]
                    original_content = content

            with _open_with_consent(override, requirement_language.txt_file_name) as fd:
                fd.write(real_content)

            if original_content is not None:
                with _open_with_consent(override, requirement_language.original_txt_file_name) as fd:
                    fd.write(original_content)

    if write_embedded_files:
        for embedded_file in flatten.embedded_files:
            with _open_with_consent(override, embedded_file.normalized_path) as fd:
                fd.write(flatten.source_code)


def _open_with_consent(override: bool, file_path: str) -> TextIO:
    if not override and os.path.exists(file_path):
        override = click.confirm(
            f"file {file_path} already exists, override?",
            default=True,
        )

    if override:
        return open(file_path, "w")

    return cast(TextIO, MockedWriteTextIO())
