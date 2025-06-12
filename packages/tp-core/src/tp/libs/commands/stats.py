from __future__ import annotations

import os
import sys
import time
import typing
import inspect
import platform

from .. import dcc

if typing.TYPE_CHECKING:
    from .command import AbstractCommand


class CommandStats:
    """Command stats class that stores information about the command execution."""

    def __init__(self, command: AbstractCommand):
        """Args:
        command: command instance.
        """

        self._start_time = 0.0
        self._end_time = 0.0
        self._execution_time = 0.0
        self._info: dict = {}

        self._init(command)

    @property
    def start_time(self) -> float:
        """Getter that returns the command start time.

        Returns:
            command start time.
        """

        return self._start_time

    @start_time.setter
    def start_time(self, value: float):
        """Setter that sets the command start time.

        Args:
            value: command start time.
        """

        self._start_time = value

    @property
    def end_time(self) -> float:
        """Getter that returns the command end time.

        Returns:
            command end time.
        """

        return self._end_time

    @end_time.setter
    def end_time(self, value: float):
        """Setter that sets the command end time.

        Args:
            value: command end time.
        """

        self._end_time = value

    @property
    def execution_time(self) -> float:
        """Getter that returns the command execution time.

        Returns:
            command execution time.
        """

        return self._execution_time

    def _init(self, command: AbstractCommand):
        """Internal function that initializes info for the command and its environment.

        Args:
            command: command instance.
        """

        # noinspection PyBroadException
        try:
            file_path = inspect.getfile(command.__class__)
        except Exception:
            file_path = ""

        self._info.update(
            {
                "name": command.__class__.__name__,
                "module": command.__class__.__module__,
                "filepath": file_path,
                "id": command.id,
                "application": dcc.current_dcc(),
            }
        )
        self._info.update(
            {
                "pythonVersion": sys.version,
                "node": platform.node(),
                "OSRelease": platform.release(),
                "OSVersion": platform.platform(),
                "processor": platform.processor(),
                "machineType": platform.machine(),
                "env": os.environ,
                "syspath": sys.path,
                "executable": sys.executable,
            }
        )

    def finish(self, trace: str | None = None):
        """Function that is called when plugin finishes its execution.

        Args:
            trace: traceback of the command execution.
        """

        self._end_time = time.time()
        self._execution_time = self._end_time - self._start_time
        self._info["executionTime"] = self._execution_time
        self._info["lastUsed"] = self._end_time
        if trace:
            self._info["traceback"] = trace
