import pandas
import pytest

from crunch_convert.requirements_txt import (LocalSitePackageVersionFinder,
                                             LocalWhitelist, NamedRequirement,
                                             freeze)

from ._libraries import os_library, pandas_library, pytest_library


def test_specs_already_specified():
    pytest_requirement = NamedRequirement(name=pytest_library.name, specs=["==1.0.0"])

    frozen = freeze(
        [
            pytest_requirement,
        ],
        freeze_only_if_required=False,
        version_finder=LocalSitePackageVersionFinder(),
    )

    assert frozen[0] is pytest_requirement


def test_freeze_everything():
    pytest_requirement = NamedRequirement(name=pytest_library.name)
    pandas_requirement = NamedRequirement(name=pandas_library.name)
    os_requirement = NamedRequirement(name=os_library.name)

    frozen = freeze(
        [
            pytest_requirement,
            pandas_requirement,
            os_requirement,
        ],
        freeze_only_if_required=False,
        version_finder=LocalSitePackageVersionFinder(),
    )

    assert frozen[0] is not pytest_requirement
    assert frozen[0].specs == [f"=={pytest.__version__}"]  # type: ignore
    assert pytest_requirement.specs == []

    assert frozen[1] is not pandas_requirement
    assert frozen[1].specs == [f"=={pandas.__version__}"]
    assert pandas_requirement.specs == []

    assert frozen[2] is os_requirement


def test_only_necessary():
    pytest_requirement = NamedRequirement(name=pytest_library.name)
    pandas_requirement = NamedRequirement(name=pandas_library.name)

    frozen = freeze(
        [
            pytest_requirement,
            pandas_requirement,
        ],
        freeze_only_if_required=True,
        whitelist=LocalWhitelist([
            pytest_library,
            pandas_library,
        ]),
        version_finder=LocalSitePackageVersionFinder(),
    )

    assert frozen[0] is pytest_requirement
    assert frozen[1].specs == [f"=={pandas.__version__}"]


def test_not_found_in_whitelist():
    pytest_requirement = NamedRequirement(name=pytest_library.name)

    frozen = freeze(
        [
            pytest_requirement,
        ],
        freeze_only_if_required=True,
        whitelist=LocalWhitelist([]),
        version_finder=LocalSitePackageVersionFinder(),
    )

    assert frozen[0] is pytest_requirement
