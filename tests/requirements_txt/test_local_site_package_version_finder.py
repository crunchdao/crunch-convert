from unittest.mock import MagicMock, patch

import pandas

from crunch_convert import RequirementLanguage
from crunch_convert.requirements_txt import LocalSitePackageVersionFinder


def test_r_unsupported():
    version_finder = LocalSitePackageVersionFinder()

    latest = version_finder.find_latest(
        language=RequirementLanguage.R,
        name="base"
    )

    assert latest is None


def test_python():
    version_finder = LocalSitePackageVersionFinder()

    latest = version_finder.find_latest(
        language=RequirementLanguage.PYTHON,
        name="pandas"
    )

    assert latest == pandas.__version__


def test_python_local_version_stripped():
    version_finder = LocalSitePackageVersionFinder()

    with patch("importlib.metadata.distribution", return_value=MagicMock(version="2.5.1+cu121")):
        latest = version_finder.find_latest(
            language=RequirementLanguage.PYTHON,
            name="torch"
        )

    assert latest == "2.5.1"
