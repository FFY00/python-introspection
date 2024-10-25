import importlib.resources

import pytest

import python_introspection.scripts


SCRIPTS_PATH = importlib.resources.files(python_introspection.scripts)
SCRIPTS = [script for script in SCRIPTS_PATH.iterdir() if script.is_file() and not script.name.startswith('_')]


@pytest.mark.parametrize('script', [pytest.param(script, id=script.name) for script in SCRIPTS])
def test_valid_syntax(script) -> None:
    compile(source=script.read_text(), filename=script.name, mode='exec')
