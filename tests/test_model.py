from crunch_convert import RequirementLanguage


def test_r():
    assert "R" == RequirementLanguage.R.value
    assert "requirements.r.txt" == RequirementLanguage.R.txt_file_name


def test_python():
    assert "PYTHON" == RequirementLanguage.PYTHON.value
    assert "requirements.txt" == RequirementLanguage.PYTHON.txt_file_name
