# python-introspection [![PyPI version](https://badge.fury.io/py/python-introspection.svg)](https://pypi.org/project/python-introspection/)

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/FFY00/python-introspection/main.svg)](https://results.pre-commit.ci/latest/github/FFY00/python-introspection/main)
[![Discord](https://img.shields.io/discord/803025117553754132?label=PyPA%20Discord)](https://discord.gg/pypa)

<!-- [![CI test](https://github.com/FFY00/python-introspection/actions/workflows/test.yml/badge.svg)](https://github.com/FFY00/python-introspection/actions/workflows/test.yml) -->
<!-- [![codecov](https://codecov.io/gh/FFY00/python-introspection/branch/main/graph/badge.svg)](https://codecov.io/gh/FFY00/python-introspection) -->
<!-- [![Documentation Status](https://readthedocs.org/projects/python-introspection/badge/?version=latest)](https://python-introspection.readthedocs.io/en/latest/?badge=latest) -->

Python library and CLI tool to introspect Python installations.

## Installation

```sh
$ pip install python-instrospection

```

## Usage (CLI)

```sh
$ python -m python_introspection (options) <command> ...
```

Option                 | Description
---------------------- | -------------------------------------------------------
`--interpreter <path>` | Selects the Python interpreter to instrospect.
`--write-to <path>`    | Write introspection data to the specified file.


### `generate-build-details`

Generated a`build-details.json` file (from [PEP 739](https://peps.python.org/pep-0739/)).

```sh
$ python -m python_introspection generate-build-details (options)
```

Option                 | Description
-------------------------- | ---------------------------------------------------
`--schema-version <value>` | Schema version of the build-details.json file to generate.
`--relative-paths`         | Whether to specify paths as absolute, or as relative paths to `base_prefix`.
