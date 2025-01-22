import importlib
import importlib.resources
import json
import logging
import os
import shlex
import subprocess
import warnings

from typing import Any, Literal


_scripts = importlib.resources.files('python_introspection.scripts')


def _type_string_to_obj(type_string: str) -> type[Any] | None:
    module, name = type_string.rsplit('.', maxsplit=1)
    try:
        return getattr(importlib.import_module(module), name)
    except ModuleNotFoundError:
        return None


class IntrospectionError(Exception):
    pass


class IntrospectionCommandError(IntrospectionError):
    def __init__(
        self,
        process: subprocess.CompletedProcess,
        message: str | None = None,
        error_info: dict[str, str] | None = None,
    ) -> None:
        if not message:
            if error_info:
                assert 'message' in error_info
                message = error_info['message']
            else:
                try:
                    process.check_returncode()
                except subprocess.CalledProcessError as e:
                    message = str(e)
                else:
                    error_msg = (
                        "If the process exited successfully, either 'message' or 'error_info' must be specified."
                    )
                    raise ValueError(error_msg)
        super().__init__(message)
        self.command = process.args
        self.stderr = process.stderr
        self.error_info = error_info


class PythonInterpreter:
    def __init__(self, path: str | os.PathLike) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._path = os.fspath(path)

    def _propagate_script_warnings(self, warnings_details: list[dict[str, Any]]) -> None:
        for item in warnings_details:
            try:
                warnings.warn_explicit(
                    message=item['message'],
                    category=_type_string_to_obj(item['category']) or UserWarning,
                    filename=item['filename'],
                    lineno=item['lineno'],
                )
            except Exception:
                warnings.warn(f'Failed to propagate script warning: {item}', stacklevel=2)

    def _run_script(self, script_name: str, *args: str) -> dict[str, Any]:
        command = [self._path, os.fspath(_scripts / script_name), *args]
        self._logger.debug(f'Running command: {shlex.join(command)}')
        process = subprocess.run(command, capture_output=True, text=True)

        try:
            script_output = json.loads(process.stdout)
        except json.JSONDecodeError:
            script_output = {}

        self._propagate_script_warnings(script_output.get('warnings', []))

        if process.returncode != 0 or 'error' in script_output:
            raise IntrospectionCommandError(process, error_info=script_output.get('error'))
        if 'data' not in script_output:
            raise IntrospectionCommandError(
                process,
                message=(
                    f"The introspection script ({shlex.join(process.args)}) didn't return any data — this is a bug.\n\n"
                    'Please report it to https://github.com/FFY00/python-instrospection/issues.'
                ),
            )

        return script_output['data']

    def generate_build_details(
        self,
        *,
        schema_version: Literal['1.0'] = '1.0',
        relative_paths: bool = False,
        config_file_path: os.PathLike | str | None = None,
    ) -> dict[str, Any]:
        args = ['--schema-version', schema_version]
        if relative_paths:
            args.append('--relative-paths')
        if config_file_path:
            args.append(f'--config-file-path={os.fspath(config_file_path)}')
        return self._run_script('generate-build-details.py', *args)
