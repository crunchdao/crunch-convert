from crunch_convert import RequirementLanguage


def test_python():
    assert "PYTHON" == RequirementLanguage.PYTHON.value
    assert "requirements.txt" == RequirementLanguage.PYTHON.txt_file_name
    assert True is RequirementLanguage.PYTHON.supports_extras_and_specs


def test_r():
    assert "R" == RequirementLanguage.R.value
    assert "requirements.r.txt" == RequirementLanguage.R.txt_file_name
    assert False is RequirementLanguage.R.supports_extras_and_specs
