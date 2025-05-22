
# python-introspection

Python library and CLI tool to introspect Python installations.

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
