# Crunch Convert Tool

[![PyTest](https://github.com/crunchdao/crunch-convert/actions/workflows/pytest.yml/badge.svg)](https://github.com/crunchdao/crunch-convert/actions/workflows/pytest.yml)

This Python library is designed for the [CrunchDAO Platform](https://hub.crunchdao.com/), exposing the conversion tools in a very small CLI.

- [Crunch Convert Tool](#crunch-convert-tool)
- [Features](#features)
  - [Automatic line commenting](#automatic-line-commenting)
  - [Specifying package versions](#specifying-package-versions)
  - [R imports via rpy2](#r-imports-via-rpy2)
  - [Embedded Files](#embedded-files)
- [Installation](#installation)
- [Usage](#usage)
  - [Via the CLI](#via-the-cli)
  - [Via the Code](#via-the-code)
- [Contributing](#contributing)
- [License](#license)

# Features

## Automatic line commenting

Only includes the functions, imports, and classes will be kept.

Everything else is commented out to prevent side effects when your code is loaded into the cloud environment. (e.g. when you're exploring the data, debugging your algorithm, or doing visualizating using Matplotlib, etc.)

You can prevent this behavior by using special comments to tell the system to keep part of your code:

- To start a section that you want to keep, write: `@crunch/keep:on`
- To end the section, write: `@crunch/keep:off`

```python
# @crunch/keep:on

# keep global initialization
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# keep constants
TRAIN_DEPTH = 42
IMPORTANT_FEATURES = [ "a", "b", "c" ]

# @crunch/keep:off

# this will be ignored
x, y = crunch.load_data()

def train(...):
    ...
```

The result will be:

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

TRAIN_DEPTH = 42
IMPORTANT_FEATURES = [ "a", "b", "c" ]

#x, y = crunch.load_data()

def train(...):
    ...
```

> [!TIP]
> You can put a `@crunch/keep:on` at the top of the cell and never close it to keep everything.

## Specifying package versions

Since submitting a notebook does not include a `requirements.txt`, users can instead specify the version of a package using import-level [requirement specifiers](https://pip.pypa.io/en/stable/reference/requirement-specifiers/#examples) in a comment on the same line.

```python
# Valid statements
import pandas # == 1.3
import sklearn # >= 1.2, < 2.0
import tqdm # [foo, bar]
import scikit # ~= 1.4.2
from requests import Session # == 1.5
```

Specifying multiple times will cause the submission to be rejected if they are different.

```python
# Inconsistant versions will be rejected
import pandas # == 1.3
import pandas # == 1.5
```

Specifying versions on standard libraries does nothing (but they will still be rejected if there is an inconsistent version).

```python
# Will be ignored
import os # == 1.3
import sys # == 1.5
```

If an optional dependency is required for the code to work properly, an import statement must be added, even if the code does not use it directly.

```python
import castle.algorithms

# Keep me, I am needed by castle
import torch
```

It is possible for multiple import names to resolve to different libraries on PyPI. If this happens, you must specify which one you want. If you do not want a specific version, you can use `@latest`, as without this, we cannot distinguish between commented code and version specifiers.

```python
# Prefer https://pypi.org/project/EMD-signal/
import pyemd # EMD-signal @latest

# Prefer https://pypi.org/project/pyemd/
import pyemd # pyemd @latest
```

## R imports via rpy2

For notebook users, the packages are automatically extracted from the `importr("<name>")` calls, which is provided by [rpy2](https://rpy2.github.io/).

```python
# Import the `importr` function
from rpy2.robjects.packages import importr

# Import the "base" R package
base = importr("base")
```

The following format must be followed:
- The import must be declared at the root level.
- The result must be assigned to a variable; the variable's name will not matter.
- The function name must be `importr`, and it must be imported as shown in the example above.
- The first argument must be a string constant, variables or other will be ignored.
- The other arguments are ignored; this allows for [custom import mapping](https://rpy2.github.io/doc/latest/html/robjects_rpackages.html#importing-r-packages) if necessary.

The line will not be commented, [read more about line commenting here](#automatic-line-commenting).

## Embedded Files

Additional files can be embedded in cells to be submitted with the Notebook. In order for the system to recognize a cell as an Embed File, the following syntax must be followed:

```
---
file: <file_name>.md
---

<!-- File content goes here -->
Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Aenean rutrum condimentum ornare.
```

Submitting multiple cells with the same file name will be rejected.

While the focus is on Markdown files, any text file will be accepted. Including but not limited to: `.txt`, `.yaml`, `.json`, ...

# Installation

Use [pip](https://pypi.org/project/crunch-convert/) to install the `crunch-convert`.

```bash
pip install --upgrade crunch-convert
```

# Usage

## Via the CLI

```bash
crunch-convert notebook my-notebook.ipynb
```

## Via the Code

```python
from crunch_convert.notebook import extract_from_file

flatten = extract_from_file("notebook.ipynb")

with open("main.py", "w") as fd:
  fd.write(flatten.source_code)

with open("requirements.txt", "w") as fd:
  for requirement in flatten.requirements:
    fd.write(str(requirement) + "\n")

for embedded_file in flatten.embedded_files:
  with open(embedded_file.normalized_path, "w") as fd:
    fd.write(embedded_file.content)
```

# Contributing

Pull requests are always welcome! If you find any issues or have suggestions for improvements, please feel free to submit a pull request or open an issue in the GitHub repository.

# License

[MIT](https://choosealicense.com/licenses/mit/)
