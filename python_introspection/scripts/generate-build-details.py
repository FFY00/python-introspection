import argparse
import importlib.machinery
import json
import os
import sys
import sysconfig
import traceback
import warnings


if False:  # TYPE_CHECKING
    pass


def version_info_to_dict(obj):  # (object) -> dict[str, Any]
    field_names = ('major', 'minor', 'micro', 'releaselevel', 'serial')
    return {field: getattr(obj, field) for field in field_names}


def get_dict_key(dict_, key):  # (dict[str, Any], tuple[Any, ...]) -> dict[str, Ant]
    for entry in key.split('.'):
        dict_ = dict_[entry]
    return dict_


def generate_data(
    schema_version: str,
    relative_paths: bool = False,
):  # type: (str) -> dict[str, Any]
    """Generate the build-details.json data (PEP 739).

    :param schema_version: The schema version of the data we want to generate.
    :param relative_paths: Whether to specify paths as absolute, or as relative to ``base_prefix``.
    """
    data = {
        'schema_version': schema_version,
        'base_prefix': sysconfig.get_config_var('prefix'),
        'platform': sysconfig.get_platform(),
    }
    data['language'] = {
        'version': sysconfig.get_python_version(),
        'version_info': {
            field: getattr(sys.version_info, field) for field in ('major', 'minor', 'micro', 'releaselevel', 'serial')
        },
    }
    data['implementation'] = vars(sys.implementation)
    data['implementation']['version'] = version_info_to_dict(sys.implementation.version)
    data['interpreter'] = {
        'path': sys.executable,
    }
    data['abi'] = {
        'flags': list(sys.abiflags),
        'extension_suffix': sysconfig.get_config_var('EXT_SUFFIX'),
    }
    for suffix in importlib.machinery.EXTENSION_SUFFIXES:
        if suffix.startswith('.abi'):
            data['abi']['stable_abi_suffix'] = suffix
            break
    data['suffixes'] = {
        'source': importlib.machinery.SOURCE_SUFFIXES,
        'bytecode': importlib.machinery.BYTECODE_SUFFIXES,
        'optimized_bytecode': importlib.machinery.OPTIMIZED_BYTECODE_SUFFIXES,
        'debug_bytecode': importlib.machinery.DEBUG_BYTECODE_SUFFIXES,
        'extensions': importlib.machinery.EXTENSION_SUFFIXES,
    }
    libdir = sysconfig.get_config_var('LIBDIR')
    dynamic_libpython_name = sysconfig.get_config_var('LDLIBRARY')
    static_libpython_name = sysconfig.get_config_var('LIBRARY')
    data['libpython'] = {
        'dynamic': os.path.join(libdir, dynamic_libpython_name) if dynamic_libpython_name else None,
        'static': os.path.join(libdir, static_libpython_name) if static_libpython_name else None,
        'link_to_libpython': bool(sysconfig.get_config_var('LIBPYTHON')),
    }
    data['c_api'] = {
        'headers': sysconfig.get_path('include'),
        'pkgconfig_path': sysconfig.get_config_var('LIBPC'),
    }

    # update path values to make them relative to base_prefix, when relative_paths is enabled
    path_entries = [
        'interpreter.path',
        'libpython.dynamic',
        'libpython.static',
        'c_api.headers',
        'c_api.pkgconfig_path',
    ]
    if relative_paths:
        for entry in path_entries:
            # get the section and item keys
            section, item = entry.rsplit('.', maxsplit=1)
            # get the section dictionary
            try:
                section_dict = get_dict_key(data, section)
            except KeyError:
                continue
            # update the value
            new_path = os.path.relpath(section_dict[item], data['base_prefix'])
            # join '.' so that the path is formated as './path' instead of 'path'
            new_path = os.path.join('.', new_path)
            section_dict[item] = new_path

    return data


def main():  # type: () -> None
    parser = argparse.ArgumentParser(exit_on_error=False)
    parser.add_argument(
        '--schema-version',
        default='1',
        help='Schema version of the build-details.json file to generate.',
    )
    parser.add_argument(
        '--relative-paths',
        action='store_true',
        help='Whether to specify paths as absolute, or as relative paths to ``base_prefix``.',
    )

    args = parser.parse_args()

    with warnings.catch_warnings(record=True) as data_generation_warnings:
        data = generate_data(
            schema_version=args.schema_version,
            relative_paths=args.relative_paths,
        )

    output = {
        'data': data,
        'warnings': [
            {
                'message': str(warning.message),
                'category': '.'.join(warning.category.__module__, warning.category.__qualname__),
                'filename': warning.filename,
                'lineno': warning.lineno,
            }
            for warning in data_generation_warnings
        ],
    }

    json_output = json.dumps(output, indent=2)
    print(json_output)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        data = {
            'error': {
                'kind': str(e.__class__),
                'message': str(e),
            }
        }
