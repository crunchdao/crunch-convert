from crunch_convert import RequirementLanguage
from crunch_convert.requirements_txt import Library

pytest_library = Library(
    name="pytest",
    alias="pytest",
    language=RequirementLanguage.PYTHON,
    standard=False,
    freeze=False,
)

sklearn_library = Library(
    name="scikit-learn",
    alias="sklearn",
    language=RequirementLanguage.PYTHON,
    standard=False,
    freeze=True,
)

pandas_library = Library(
    name="pandas",
    alias="pandas",
    language=RequirementLanguage.PYTHON,
    standard=False,
    freeze=True,
)

pandas_in_r_library = Library(
    name="pandas",
    alias="pandas",
    language=RequirementLanguage.R,
    standard=False,
    freeze=True,
)

emd_signal_library = Library(
    name="EMD-signal",
    alias="pyemd",
    language=RequirementLanguage.PYTHON,
    standard=False,
    freeze=False,
)

pyemd_library = Library(
    name="pyemd",
    alias="pyemd",
    language=RequirementLanguage.PYTHON,
    standard=False,
    freeze=False,
)

os_library = Library(
    name="os",
    alias="os",
    language=RequirementLanguage.PYTHON,
    standard=True,
    freeze=False,
)
