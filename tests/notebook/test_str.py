from crunch_convert.notebook._notebook import ImportInfo


def test_import_info():
    info = ImportInfo(None, ["a"], [">1"])
    assert str(info) == "[a]>1"

    info = ImportInfo("pandas", ["a"], [">1"])
    assert str(info) == "pandas[a]>1"
