import pytest

from crunch_convert.notebook import (ImportedRequirement,
                                     ImportedRequirementLanguage)


def test_merge_nothing():
    a = ImportedRequirement(alias="a")
    b = ImportedRequirement(alias="b")

    success, _ = a.merge(b)

    assert success
    assert ("a", None, [], []) == (a.alias, a.name, a.extras, a.specs)


def test_merge_ignore_if_set_name():
    a = ImportedRequirement(alias="a", name="xyz")
    b = ImportedRequirement(alias="b")

    success, _ = a.merge(b)

    assert success
    assert ("a", "xyz", [], []) == (a.alias, a.name, a.extras, a.specs)


def test_merge_ignore_if_set_extras():
    a = ImportedRequirement(alias="a", extras=["tiny"])
    b = ImportedRequirement(alias="b")

    success, _ = a.merge(b)

    assert success
    assert ("a", None, ["tiny"], []) == (a.alias, a.name, a.extras, a.specs)


def test_merge_ignore_if_set_full():
    a = ImportedRequirement(alias="a", name="xyz", extras=["tiny"], specs=["==1"])
    b = ImportedRequirement(alias="b")

    success, _ = a.merge(b)

    assert success
    assert ("a", "xyz", ["tiny"], ["==1"]) == (a.alias, a.name, a.extras, a.specs)


def test_merge_ignore_if_set_specs():
    a = ImportedRequirement(alias="a", specs=["==1"])
    b = ImportedRequirement(alias="b")

    success, _ = a.merge(b)

    assert success
    assert ("a", None, [], ["==1"]) == (a.alias, a.name, a.extras, a.specs)


def test_merge_name():
    a = ImportedRequirement(alias="a")
    b = ImportedRequirement(alias="b", name="xyz")

    success, _ = a.merge(b)

    assert success
    assert ("a", "xyz", [], []) == (a.alias, a.name, a.extras, a.specs)


def test_merge_extras():
    a = ImportedRequirement(alias="a")
    b = ImportedRequirement(alias="b", extras=["full"])

    success, _ = a.merge(b)

    assert success
    assert ("a", None, ["full"], []) == (a.alias, a.name, a.extras, a.specs)


def test_merge_specs():
    a = ImportedRequirement(alias="a")
    b = ImportedRequirement(alias="b", specs=["==1"])

    success, _ = a.merge(b)

    assert success
    assert ("a", None, [], ["==1"]) == (a.alias, a.name, a.extras, a.specs)


def test_merge_specs_and_extras():
    a = ImportedRequirement(alias="a")
    b = ImportedRequirement(alias="b", extras=["full"], specs=["==1"])

    success, _ = a.merge(b)

    assert success
    assert ("a", None, ["full"], ["==1"]) == (a.alias, a.name, a.extras, a.specs)


def test_merge_different_language():
    a = ImportedRequirement(alias="a", language=ImportedRequirementLanguage.PYTHON)
    b = ImportedRequirement(alias="b", language=ImportedRequirementLanguage.R)

    with pytest.raises(ValueError) as excinfo:
        a.merge(b)

    assert "cannot merge requirements with different languages: PYTHON != R" == str(excinfo.value)


def test_merge_different_name():
    a = ImportedRequirement(alias="a", name="abc")
    b = ImportedRequirement(alias="b", name="def", extras=["full"], specs=["==1"])

    success, message = a.merge(b)

    assert not success
    assert message == "name is different"


def test_merge_different_extras():
    a = ImportedRequirement(alias="a", extras=["tiny"])
    b = ImportedRequirement(alias="b", extras=["full"])

    success, message = a.merge(b)

    assert not success
    assert message == "extras are different"


def test_merge_different_specs():
    a = ImportedRequirement(alias="a", specs=["==1"])
    b = ImportedRequirement(alias="b", specs=["==2"])

    success, message = a.merge(b)

    assert not success
    assert message == "specs are different"


def test_merge_different_extras_and_specs():
    a = ImportedRequirement(alias="a", extras=["tiny"], specs=["==1"])
    b = ImportedRequirement(alias="b", extras=["full"], specs=["==2"])

    success, message = a.merge(b)

    assert not success
    assert message == "both extras and specs are different"


def test_merge_different_full():
    a = ImportedRequirement(alias="a", name="abc", extras=["tiny"], specs=["==1"])
    b = ImportedRequirement(alias="b", name="def", extras=["full"], specs=["==2"])

    success, message = a.merge(b)

    assert not success
    assert message == "name, extras and specs are all different"


def test_str_alias_only():
    a = ImportedRequirement(alias="a")

    assert "a  # unknown name, using alias instead" == str(a)


def test_str_with_name():
    a = ImportedRequirement(alias="a", name="abc")

    assert "abc  # alias of 'a'" == str(a)


def test_str_full():
    a = ImportedRequirement(alias="a", name="abc", extras=["tiny"], specs=["==1"])

    assert "abc[tiny]==1  # alias of 'a'" == str(a)
