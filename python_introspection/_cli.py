import importlib
import itertools
import logging
import os
import platform
import sys
import textwrap
import traceback
import warnings

from typing import ClassVar, TextIO


if sys.version_info >= (3, 9):
    from collections.abc import Mapping
else:
    from typing.abc import Mapping


class Console:
    _STYLES_COLOR_ENABLED: ClassVar[Mapping[str, str]] = {
        'red': '\33[91m',
        'green': '\33[92m',
        'yellow': '\33[93m',
        'white': '\33[97m',
        'grey': '\33[37m',
        'bold': '\33[1m',
        'dim': '\33[2m',
        'underline': '\33[4m',
        'reset': '\33[0m',
    }
    _STYLES_COLOR_DISABLED: ClassVar[Mapping[str, str]] = {style: '' for style in _STYLES_COLOR_ENABLED}

    def __init__(self) -> None:
        self.styles = self._get_styles_dict()

    def _should_enable_colors(self) -> bool:
        # selected via environment variables
        if 'NO_COLOR' in os.environ:
            if 'FORCE_COLOR' in os.environ:
                warnings.warn(
                    'Both NO_COLOR and FORCE_COLOR environment variables are set, disabling color', stacklevel=2
                )
            return False
        elif 'FORCE_COLOR' in os.environ:
            return True
        # defaults
        # Windows needs the colorama patch, se the context manager must be active
        if platform.system() == 'Windows' and not self._active:
            return False
        return sys.stdout.isatty()

    def _get_styles_dict(self) -> bool:
        if self._should_enable_colors:
            return self._STYLES_COLOR_ENABLED
        else:
            return self._STYLES_COLOR_DISABLED

    def __enter__(self):
        self._active = True

        # fix colors in Windows
        if platform.system() == 'Windows':
            self._original_stdout = sys.stdout
            self._original_stderr = sys.stderr
            try:
                import colorama
            except ModuleNotFoundError:
                pass
            else:
                colorama.just_fix_windows_console()

        # replace warning display handler
        self._original_showwarning = warnings.showwarning
        warnings.showwarning = self._custom_showwarning

        # setup logging
        log_formatter = ConsoleLogFormatter(self)
        log_handler = logging.StreamHandler()
        log_handler.setFormatter(log_formatter)
        logging.basicConfig(
            level=os.environ.get('LOGLEVEL', 'INFO').upper(),
            handlers=[log_handler],
        )

        # update the active colors dict
        self.styles = self._get_styles_dict()

        return self

    def __exit__(self, type, value, traceback):
        self._active = False

        # restore the original stdout and stderr manually since colorama doesn't provide that functionality
        if platform.system() == 'Windows':
            sys.stdout = self._original_stdout
            sys.stderr = self._original_stderr

        # restore the original warning display handler
        warnings.showwarning = self._original_showwarning

        # reset the logging configuration
        logging.shutdown()
        importlib.reload(logging)

        # update the active styles dict
        self.styles = self._get_styles_dict()

    def _custom_showwarning(
        self,
        message: Warning | str,
        category: type[Warning],
        filename: str,
        lineno: int,
        file: TextIO | None = None,
        line: str | None = None,
    ) -> None:  # pragma: no cover
        self.warn(str(message), source=f'{filename}:{lineno}')

    def _visible_text_lenght(self, text: str) -> int:
        """Takes a text with style placeholders and calculates the text length considering only the visible characters."""
        return len(text.format(**self.styles_DISABLED))

    def _wrap_text(self, text: str, line_prefix: str = '') -> list[str]:
        """Wraps text to fit the console width, keeping whitespace and empty lines."""
        wrapper = textwrap.TextWrapper(
            width=os.get_terminal_size().columns - self._visible_text_lenght(line_prefix),
            break_long_words=False,
            break_on_hyphens=False,
            drop_whitespace=False,
            replace_whitespace=False,
        )
        return list(itertools.chain.from_iterable(wrapper.wrap(line) if line else [''] for line in text.splitlines()))

    def render_text(self, fmt: str, *args: str, **kwargs: str) -> str:
        return fmt.format(*args, **kwargs, **self.styles)

    def print(self, fmt: str = '', *args: str, end='\n', file: TextIO | None = None, **kwargs: str) -> None:
        """Format and print message to the console."""
        print(self.render_text(fmt, *args, **kwargs), end=end, file=file, flush=True)

    def print_exception(self, *, style: str = 'dim', prefix: str = '') -> None:
        """Print current exception to stderr."""
        self.print('{dim}', end='', file=sys.stderr)
        tb_lines = traceback.format_exc().splitlines()
        for line in tb_lines:
            self.print(prefix + '{}', line, file=sys.stderr)
        self.print('{reset}', end='', file=sys.stderr)

    def log(self, message: str, *, level: str, level_style: str = 'reset') -> None:
        """Log message to console. If the message is too big, it will be printed in a block."""
        message_lines = self._wrap_text(message)
        self.print(f'{{{level_style}}}{level}{{reset}}', end='')
        assert len(message_lines) != 0
        # print in a single line (LEVEL MESSAGE)
        if len(message_lines) == 1:
            self.print(' {}', message, file=sys.stderr)
        # print message block
        if len(message_lines) > 1:
            self.print(file=sys.stderr)
            for line in message_lines:
                self.print(f'{{{level_style}}}|{{reset}} {{}}', line, file=sys.stderr)

    def warn(self, message: str, source: str | None = None) -> None:
        """Print warning to console."""
        if source is not None:
            self.print('{dim}({}){reset} ', source, end='')
        self.log(message, level='WARNING', level_style='yellow')

    def error(self, message: str, *, print_exception: bool = False) -> None:
        """Print error to console. Optionally, also print the current exception."""
        if print_exception:
            self.print_exception()
            self.print(file=sys.stderr)
        self.log(message, level='ERROR', level_style='red')


class ConsoleLogFormatter(logging.Formatter):
    _LEVEL_STYLES: ClassVar[Mapping[int, tuple[str, ...]]] = {
        logging.DEBUG: ('grey',),
        logging.INFO: ('white',),
        logging.WARNING: ('yellow',),
        logging.ERROR: ('red',),
        logging.CRITICAL: ('bold', 'red'),
    }

    def __init__(self, console: Console) -> None:
        super().__init__()
        self._console = console
        output_format = (
            '{dim}%(asctime)s{reset} {white}{bold}%(name)s{reset} '
            '%(module)s:%(funcName)s:%(lineno)d '
            '{level_style}%(levelname)s'
            '{reset}: \t%(message)s'
        )
        self._formatters = {
            level: logging.Formatter(
                self._console.render_text(
                    output_format,
                    level_style=self._console.render_text(''.join(f'{{{style}}}' for style in styles)),
                )
            )
            for level, styles in self._LEVEL_STYLES.items()
        }

    def format(self, record: logging.LogRecord) -> str:
        return self._formatters[record.levelno].format(record)
