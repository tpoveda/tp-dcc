from __future__ import annotations

import os
import sys
import timeit
import typing
import inspect
import platform
from dataclasses import dataclass, field

try:
    from packaging.version import Version
except ImportError:
    from distutils.version import LooseVersion as Version  # type: ignore

if typing.TYPE_CHECKING:
    from .manager import PluginsManager


class PluginDependencyError(Exception):
    """Exception raised when plugin dependencies cannot be resolved."""

    pass


@dataclass
class PluginMetadata:
    """Data class that stores metadata information about a plugin."""

    author: str = "Tomi Poveda"
    version: str = "0.0.1"
    description: str = ""
    compatible_applications: list[str] = field(default_factory=list)

    def get_version(self) -> Version:
        """Returns the version as a `Version` object.

        Returns:
            The version as a `Version` object.
        """

        return Version(self.version)


class Plugin:
    """Base class for all plugins."""

    # The unique identifier of the plugin.
    # Ideally it should be a descriptive name following the format:
    #   "plugin.exporter.camera"
    id: str = ""
    dependencies: list[str] = []
    metadata: PluginMetadata = PluginMetadata()

    def __init__(self, manager: PluginsManager | None = None):
        """Initializes the plugin.

        Args:
            manager: The plugin manager. Defaults to None.
        """

        super().__init__()

        self._manager = manager
        self._stats = PluginExecutionStats(self)

    @property
    def manager(self) -> PluginsManager | None:
        """Getter that returns the plugin manager.

        Returns:
            The plugin manager.
        """

        return self._manager

    @property
    def stats(self) -> PluginExecutionStats:
        """Getter that returns the plugin execution statistics.

        Returns:
            The plugin execution statistics.
        """

        return self._stats

    def initialize(self):
        """Initialization logic when plugin is loaded.

        This method can be overridden by subclasses.
        """

        pass

    def shutdown(self):
        """Cleanup logic when plugin is unloaded.

        This method can be overridden by subclasses.
        """

        pass


@dataclass
class PluginInfo:
    """Data class that stores information about a plugin."""

    id: str
    name: str
    module: str
    file_path: str
    python_version: str
    node: str
    os_release: str
    os_version: str
    processor: str
    machine_type: str
    executable: str
    env: dict = field(default_factory=dict)
    syspath: list[str] = field(default_factory=list)
    execution_time: float = 0.0
    last_used: float = 0.0
    traceback: str = ""


class PluginExecutionStats:
    """Class that stores the statistics of a plugin execution."""

    def __init__(self, plugin: Plugin):
        """Initializes the plugin execution statistics.

        Args:
            plugin: The plugin instance.
        """

        super().__init__()

        self._plugin = plugin
        self._id = plugin.id
        self._start_time: float = 0.0
        self._execution_time: float = 0.0
        self._end_time: float = 0.0
        try:
            file_path = inspect.getfile(self._plugin.__class__)
        except TypeError:
            file_path = "__main__"
        self._info = PluginInfo(
            id=self._id,
            name=self._plugin.__class__.__name__,
            module=self._plugin.__class__.__module__,
            file_path=file_path,
            python_version=sys.version,
            node=platform.node(),
            os_release=platform.release(),
            os_version=platform.platform(),
            processor=platform.processor(),
            machine_type=platform.machine(),
            executable=sys.executable,
            env=os.environ.copy(),
            syspath=sys.path.copy(),
        )

    @property
    def plugin(self) -> Plugin:
        """Getter that returns the plugin instance.

        Returns:
            The plugin instance.
        """

        return self._plugin

    @property
    def id(self) -> str:
        """Getter that returns the plugin identifier.

        Returns:
            The plugin identifier.
        """

        return self._id

    @property
    def start_time(self) -> float:
        """Getter that returns the plugin start time.

        Returns:
            The plugin start time.
        """

        return self._start_time

    @property
    def execution_time(self) -> float:
        """Getter that returns the plugin execution time.

        Returns:
            The plugin execution time.
        """

        return self._execution_time

    @property
    def end_time(self) -> float:
        """Getter that returns the plugin end time.

        Returns:
            The plugin end time.
        """

        return self._end_time

    @property
    def info(self) -> PluginInfo:
        """Getter that returns the plugin information.

        Returns:
            The plugin information.
        """

        return self._info

    def start(self):
        """Starts the plugin execution timer."""

        self._start_time = timeit.default_timer()

    def finish(self, traceback: str | None = None):
        """Finishes the plugin execution timer.

        Args:
            traceback: The traceback of the plugin execution. Defaults to None.
        """

        self._end_time = timeit.default_timer()
        self._execution_time = self._end_time - self._start_time
        self._info.execution_time = self._execution_time
        self._info.last_used = self._end_time
        if traceback:
            self._info.traceback = traceback
