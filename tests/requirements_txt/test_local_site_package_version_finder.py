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
