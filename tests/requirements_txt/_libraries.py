from crunch_convert import RequirementLanguage
from crunch_convert.requirements_txt import Library

pytest_library = Library(
    name="pytest",
    aliases=["pytest"],
    language=RequirementLanguage.PYTHON,
    standard=False,
    freeze=False,
)

sklearn_library = Library(
    name="scikit-learn",
    aliases=["sklearn"],
    language=RequirementLanguage.PYTHON,
    standard=False,
    freeze=True,
)

pandas_library = Library(
    name="pandas",
    aliases=["pandas"],
    language=RequirementLanguage.PYTHON,
    standard=False,
    freeze=True,
)

pandas_in_r_library = Library(
    name="pandas",
    aliases=["pandas"],
    language=RequirementLanguage.R,
    standard=False,
    freeze=True,
)

emd_signal_library = Library(
    name="EMD-signal",
    aliases=["pyemd"],  # should be "PyEMD", but used in the collision test
    language=RequirementLanguage.PYTHON,
    standard=False,
    freeze=False,
)

pyemd_library = Library(
    name="pyemd",
    aliases=["pyemd"],
    language=RequirementLanguage.PYTHON,
    standard=False,
    freeze=False,
)

os_library = Library(
    name="os",
    aliases=["os"],
    language=RequirementLanguage.PYTHON,
    standard=True,
    freeze=False,
)
