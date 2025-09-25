import json
import os

import click

from crunch_convert.__version__ import __version__
from crunch_convert.notebook import (ConverterError,
                                     InconsistantLibraryVersionError,
                                     NotebookCellParseError, extract_cells)
from crunch_convert.notebook._utils import print_indented


@click.group()
@click.version_option(__version__, package_name="__version__.__title__")
def cli():
    pass


@cli.command(help="Convert a notebook to a python script.")
@click.option("--override", is_flag=True, help="Force overwrite of the python file.")
@click.argument("notebook-file-path", required=True)
@click.argument("python-file-path", default="main.py")
def notebook(
    override: bool,
    notebook_file_path: str,
    python_file_path: str,
):
    with open(notebook_file_path) as fd:
        notebook = json.load(fd)

    try:
        cells = notebook["cells"]

        flatten = extract_cells(
            cells=cells,
            print=print,
        )
    except ConverterError as error:
        print(f"convert failed: {error}")

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

    if not override and os.path.exists(python_file_path):
        override = click.prompt(
            f"file {python_file_path} already exists, override?",
            type=bool,
            default=False,
            prompt_suffix=" "
        )

        if not override:
            raise click.Abort()

    with open(python_file_path, "w") as fd:
        fd.write(flatten.source_code)
