
from crunch_convert._model import RequirementLanguage
from crunch_convert.requirements_txt._whitelist import Library

sklearn_library = Library(
    name="scikit-learn",
    alias="sklearn",
    language=RequirementLanguage.PYTHON,
    standard=False,
)

pandas_library = Library(
    name="pandas",
    alias="pandas",
    language=RequirementLanguage.PYTHON,
    standard=False,
)

pandas_in_r_library = Library(
    name="pandas",
    alias="pandas",
    language=RequirementLanguage.R,
    standard=False,
)

emd_signal_library = Library(
    name="EMD-signal",
    alias="pyemd",
    language=RequirementLanguage.PYTHON,
    standard=False,
)

pyemd_library = Library(
    name="pyemd",
    alias="pyemd",
    language=RequirementLanguage.PYTHON,
    standard=False,
)

os_library = Library(
    name="os",
    alias="os",
    language=RequirementLanguage.PYTHON,
    standard=True,
)
