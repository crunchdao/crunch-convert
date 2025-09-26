import json
import os
from tempfile import TemporaryDirectory
from typing import Iterable, List, cast

import pytest
from click.testing import CliRunner
from parameterized import parameterized  # type: ignore

from crunch_convert.cli import cli as cli_group


def _get_notebook_paths() -> Iterable[str]:
    cloned_directory = os.getenv("CLONED_COMPETITIONS_REPOSITORY_PATH")
    if not cloned_directory:
        return cast(List[str], [])

    competitions_directory = os.path.join(cloned_directory, "competitions")
    for competition_name in os.listdir(competitions_directory):
        quickstarters_directory = os.path.join(competitions_directory, competition_name, "quickstarters")

        if not os.path.isdir(quickstarters_directory):
            continue

        for quickstarter_name in os.listdir(quickstarters_directory):
            quickstarter_directory = os.path.join(quickstarters_directory, quickstarter_name)

            manifest_file = os.path.join(quickstarter_directory, "quickstarter.json")
            if not os.path.exists(manifest_file):
                continue

            with open(manifest_file, "r") as file:
                manifest = json.loads(file.read())

            if not manifest.get("notebook") or manifest.get("language") != "PYTHON":
                continue

            entrypoint_file = os.path.join(quickstarter_directory, manifest["entrypoint"])
            if not os.path.exists(entrypoint_file):
                continue

            yield entrypoint_file


notebook_paths = list(_get_notebook_paths())


@parameterized.expand(  # type: ignore
    [
        (notebook_path,)
        for notebook_path in notebook_paths
    ],
    skip_on_empty=True
)
@pytest.mark.skipif(len(notebook_paths) == 0, reason="No notebook paths found.")
def test_convert(notebook_path: str):
    runner = CliRunner()

    with TemporaryDirectory() as temp_dir:
        main_file = os.path.join(temp_dir, "main.py")

        result = runner.invoke(
            cli_group,
            [
                "notebook",
                "--override",
                notebook_path,
                main_file,
            ]
        )

        assert 0 == result.exit_code
        assert 0 != os.path.getsize(main_file), "main file is empty"
