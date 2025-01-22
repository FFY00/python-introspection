import argparse
import json
import pathlib
import sys

import python_introspection
import python_introspection._cli


class CommandLineError(ValueError):
    pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--interpreter',
        default=sys.executable,
        help='Python interpreter to introspect (default: current interpreter).',
    )
    parser.add_argument(
        '--output',
        type=pathlib.Path,
        help='Output file.',
    )
    subparsers = parser.add_subparsers(
        required=True,
        dest='action',
        help='Action to perform.',
    )
    install_details_parser = subparsers.add_parser(
        'generate-build-details',
        help='Generate the content of the build-details.json (PEP 739) file.',
    )
    install_details_parser.add_argument(
        '--schema-version',
        default='1.0',
        help='Schema version of the build-details.json file to generate.',
    )
    install_details_parser.add_argument(
        '--relative-paths',
        action='store_true',
        help='Whether to specify paths as absolute, or as relative paths to ``base_prefix``.',
    )

    args = parser.parse_args()

    interpreter = python_introspection.PythonInterpreter(args.interpreter)

    if args.action == 'generate-build-details':
        data = interpreter.generate_build_details(
            schema_version=args.schema_version,
            relative_paths=args.relative_paths,
        )
    assert data

    json_data = json.dumps(data, indent=2)
    if args.output:
        args.parent.mkdir(parents=True, exist_ok=True)
    else:
        print(json_data)


if __name__ == '__main__':
    with python_introspection._cli.Console() as console:
        try:
            main()
        except CommandLineError as e:
            console.error(str(e))
            sys.exit(1)
        except Exception as e:
            console.error(str(e), print_exception=True)
            sys.exit(1)
