import re

import requests

from crunch_convert import RequirementLanguage
from crunch_convert.requirements_txt import CrunchHubVersionFinder

from ._env import api_base_url

version_finder = CrunchHubVersionFinder(
    api_base_url=api_base_url,
)


def test_not_exists():
    latest = version_finder.find_latest(
        language=RequirementLanguage.PYTHON,
        name="idontexists"
    )

    assert latest is None


def test_python():
    name = "pandas"

    latest = version_finder.find_latest(
        language=RequirementLanguage.PYTHON,
        name=name,
    )

    def find_lastest_version_from_pypi(package_name: str) -> str:
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json")
        response.raise_for_status()

        info = response.json()["info"]
        return info["version"]

    assert latest == find_lastest_version_from_pypi(name)


def test_r():
    name = "tidyverse"

    latest = version_finder.find_latest(
        language=RequirementLanguage.R,
        name=name,
    )

    def find_lastest_version_from_cran(package_name: str) -> str:
        response = requests.get(f"https://cloud.r-project.org/web/packages/{package_name}/")
        response.raise_for_status()

        match = re.search(r"<tr>\s*<td>Version:<\/td>\s*<td>(.+)<\/td>\s+<\/tr>", response.text)
        assert match is not None, "regex match failed"

        return match.group(1)

    assert latest == find_lastest_version_from_cran(name)
