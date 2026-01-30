import json
import os
import sys
from typing import Optional, TextIO, cast

import click

from crunch_convert.__version__ import __version__
from crunch_convert._model import RequirementLanguage
from crunch_convert._utils import MockedWriteTextIO
from crunch_convert.notebook import ConverterError, InconsistantLibraryVersionError, NotebookCellParseError, extract_from_file
from crunch_convert.notebook._utils import print_indented
from crunch_convert.requirements_txt import CachedWhitelist, CrunchHubWhitelist, LocalSitePackageVersionFinder, format_files_from_imported, format_files_from_named, freeze, parse_from_file

the_crunch_api_base_url: str = None  # type: ignore


@click.group()
@click.version_option(__version__, package_name="__version__.__title__")
@click.option("--crunch-api-base-url", envvar="CRUNCH_BASE_API_URL", default="https://api.hub.crunchdao.com/")
def cli(
    crunch_api_base_url: str,
):
    global the_crunch_api_base_url
    the_crunch_api_base_url = crunch_api_base_url


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

    for warning in flatten.warnings:
        print(f"warning {warning}", file=sys.stderr)

    with _open_with_consent(override, python_file_path) as fd:
        fd.write(flatten.source_code)

    if write_requirements:
        whitelist = CachedWhitelist(CrunchHubWhitelist(api_base_url=the_crunch_api_base_url))
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
                fd.write(embedded_file.content)


@cli.group()
def requirements_txt():
    pass  # pragma: no cover


@requirements_txt.command(name="freeze", help="Freeze a requirements.txt file.")
@click.option("--override", is_flag=True, help="Force overwrite of the python file.")
@click.option("--only-if-required", is_flag=True, help="Only freeze if required by the whitelist.")
@click.option("--language", "language_name", type=click.Choice([RequirementLanguage.PYTHON.name, RequirementLanguage.R.name], case_sensitive=False), default=RequirementLanguage.PYTHON.name, help="Language of the requirements.txt file.")
@click.argument("requirements-txt-file-path", type=click.Path(readable=True, dir_okay=False), required=False)
def freeze_command(
    override: bool,
    only_if_required: bool,
    language_name: str,
    requirements_txt_file_path: Optional[str],
):
    if requirements_txt_file_path == RequirementLanguage.PYTHON.txt_file_name:
        override = True

    language = RequirementLanguage[language_name.upper()]

    if requirements_txt_file_path is None:
        requirements_txt_file_path = language.txt_file_name

    with open(requirements_txt_file_path) as fd:
        content = fd.read()

    requirements = parse_from_file(
        language=language,
        file_content=content,
    )

    whitelist = CachedWhitelist(CrunchHubWhitelist(api_base_url=the_crunch_api_base_url))
    version_finder = LocalSitePackageVersionFinder()

    for requirement in requirements:
        library = whitelist.find_library(
            language=language,
            name=requirement.name,
        )

        if library is None:
            print(f"not whitelisted: {requirement.name}")

    requirements_files = format_files_from_named(
        requirements,
        header="extracted from a file",
        whitelist=whitelist,
    )

    if only_if_required:
        frozen_requirements = freeze(
            requirements=requirements,
            freeze_only_if_required=True,
            whitelist=whitelist,
            version_finder=version_finder,
        )
    else:
        frozen_requirements = freeze(
            requirements=requirements,
            freeze_only_if_required=False,
            version_finder=version_finder,
        )

    frozen_requirements_files = format_files_from_named(
        frozen_requirements,
        header="frozen from registry",
        whitelist=whitelist,
    )

    with _open_with_consent(override, language.original_txt_file_name) as fd:
        content = requirements_files[language]
        fd.write(content)

    with _open_with_consent(override, language.txt_file_name) as fd:
        content = frozen_requirements_files[language]
        fd.write(content)


def _open_with_consent(override: bool, file_path: str) -> TextIO:
    if not override and os.path.exists(file_path):
        override = click.confirm(
            f"file {file_path} already exists, override?",
            default=True,
        )

        if not override:
            return cast(TextIO, MockedWriteTextIO())

    return open(file_path, "w")
