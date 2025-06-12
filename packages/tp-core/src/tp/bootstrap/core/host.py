from __future__ import annotations

import sys
import typing
import logging
from abc import ABC, abstractmethod

if typing.TYPE_CHECKING:
    from Qt.QtWidgets import QWidget, QMainWindow
    from .manager import PackagesManager


logger = logging.getLogger(__name__)

# Global host instance variable.
_current_host: Host | None = None


def current_host() -> Host | None:
    """Returns the current host instance.

    This function is a convenience method to access the current host instance
    without needing to call `Host.current()` directly.

    Returns:
        The current host instance or None if no host is set.
    """

    return Host.current() if Host._instance else None


class Host(ABC):
    """Base class for host implementations.

    DCC integrations should inherit from this class and implement the
    required methods.

    Each host should handle the initialization of TP DCC Python pipeline in a
    DCC specific way.
    """

    # Singleton instance of the host.
    _instance: Host | None = None

    def __init__(self, packages_manager: PackagesManager, host_name: str):
        """Initializes the host.

        Args:
            packages_manager: The TP DCC Python pipeline packages manager.
            host_name: The name of the host.
        """

        self._packages_manager = packages_manager
        self._host_name = host_name
        self._host: HostApplication | None = None
        self._dialogs: dict[str, list[QWidget]] = {}
        self._initialized = False

    @property
    def initialized(self) -> bool:
        """Whether the host is initialized or not."""

        return self._initialized

    @property
    def host(self) -> HostApplication | None:
        """The host application instance."""

        return self._host

    @classmethod
    def create(
        cls,
        packages_manager: PackagesManager,
        host_class: type[Host],
        host_name: str,
    ) -> Host:
        """Creates a new host instance.

        Args:
            packages_manager: The TP DCC Python pipeline packages manager.
            host_class: The host class to create.
            host_name: The name of the host.

        Returns:
            The created host instance.

        Raises:
            RuntimeError: If the host instance already exists.
        """

        if cls._instance is None:
            cls._instance = host_class(packages_manager, host_name)
            cls._instance.initialize()

        return cls._instance

    @classmethod
    def current(cls) -> Host | None:
        """Returns the current host instance."""

        return cls._instance

    @classmethod
    def stop(cls):
        """Shuts down the host instance."""

        if cls._instance is None:
            logger.debug("No host instance to shut down.")
            return

        cls._instance.shutdown()
        cls._instance = None

    def initialize(self):
        """Initializes the host."""

        if self._initialized:
            logger.debug(f'"{self._host_name}" host already initialized.')
            return

        # Register the pre-startup command callback.
        self._packages_manager.resolver.callbacks.setdefault(
            "pre_startup_commands", []
        ).append(self._pre_startup_command_callback)

        # Step 1) Post-initialization.
        logger.debug("Running host post initialization ...")
        self.post_initialization()

        # Step 2) Environment initialization. Load all packages.
        logger.debug("Running pre environment initialization ...")
        self.pre_environment_initialization()
        self._packages_manager.resolver.resolve_from_environment_configuration_file_path(
            self._packages_manager.resolver.environment_config_file_path()
        )

        logger.debug("Running post environment initialization ...")
        self.post_environment_initialization()

        self._initialized = True

    def post_initialization(self):
        """Post-initialization method called after the host has been created
        but before any packages have been set up.

        This method should be implemented by derived classes to handle any
        post-initialization tasks.
        """

    def pre_environment_initialization(self):
        """Pre-environment initialization method called before any packages
        have been set up but after `post_initialization` has been called.

        This method should be implemented by derived classes to handle any
        pre-environment initialization tasks.
        """

    def post_environment_initialization(self):
        """Post-environment initialization method called after all packages
        have been set up.

        This method should be implemented by derived classes to handle any
        post-environment initialization tasks.
        """

    def shutdown(self):
        """Shuts down the host.

        This method should be implemented by derived classes to handle the
        shutdown process of the host.
        """

    def register_dialog(self, name: str, widget: QWidget):
        """Registers a dialog/window with the host.

        Args:
            name: Name of the dialog.
            widget: The dialog instance to register.
        """

        logger.debug(f"Registering dialog: {name} | {widget}")
        self._dialogs.setdefault(name, []).append(widget)

    def dialogs_by_name(self, name: str) -> list[QWidget]:
        """Returns a list of registered dialogs/windows by name.

        Args:
            name: Name of the dialog.

        Returns:
            A list of registered dialog instances.
        """

        return self._dialogs.get(name, [])

    def unregister_dialog(self, name: str, widget: QWidget):
        """Unregisters a dialog/window with the host.

        Args:
            name: Name of the dialog.
            widget: The dialog instance to unregister.
        """

        logger.debug(f"Unregistering dialog: {name} | {widget}")
        widgets: list[QWidget] = []
        for dialog in self._dialogs.get(name, []):
            if dialog != widget:
                widgets.append(dialog)
        self._dialogs[name] = widgets

    def close_dialog(self, name: str, widget: QWidget):
        """Closes a registered dialog/window.

        Args:
            name: Name of the dialog.
            widget: The dialog instance to close.
        """

        self.unregister_dialog(name, widget)
        widget.deleteLater()

    def close_all_dialogs(self):
        """Closes all registered dialog/windows."""

        for dialog_instances in self._dialogs.values():
            for dialog in dialog_instances:
                dialog.close()
                dialog.deleteLater()

        self._dialogs.clear()

    def set_dialogs_stylesheet(self, style: str):
        """Sets the stylesheet for the registered host dialogs.

        Args:
            style: The stylesheet to set.
        """

        for dialog_instances in self._dialogs.values():
            for dialog in dialog_instances:
                try:
                    dialog.setStyleSheet(style)
                except AttributeError:
                    logger.debug(
                        f'"Dialog {dialog} does not have `setStyleSheet` method."'
                    )

    # noinspection PyMethodMayBeStatic
    def _pre_startup_command_callback(self):
        """Internal callback function that is called by the environment
        resolver before the startup commands for the packages are called.
        """

        from tp.preferences import manager

        manager.set_instance(manager.PreferencesManager(self._packages_manager))


class HostApplication(ABC):
    """Class that contains specific host application information and
    methods.
    """

    def __init__(self, name: str, version: str, version_year: int):
        """Initializes the host application.

        Args:
            name: The name of the host application.
            version: The version of the host application.
            version_year: The year of the host application version.
        """

        self._name = name
        self._version = version
        self._version_year = version_year

    @property
    def name(self) -> str:
        """The name of the host application."""

        return self._name

    @property
    def version(self) -> str:
        """The version of the host application."""

        return self._version

    @property
    def version_year(self) -> int:
        """The year of the host application version."""

        return self._version_year

    @property
    @abstractmethod
    def install_location(self) -> str:
        """The installation location of the host application."""

        raise NotImplementedError(
            "The `install_location` property must be implemented by the host class."
        )

    @property
    @abstractmethod
    def qt_main_window(self) -> QMainWindow | None:
        """The main window of the host application."""

        raise NotImplementedError(
            "The `qt_main_window` property must be implemented by the host class."
        )

    @abstractmethod
    def quit(self, force: bool = True):
        """Quits the host application.

        Args:
            force: Whether to force quit the application or not.
        """

        raise NotImplementedError(
            "The `quit` method must be implemented by the host class."
        )

    @property
    def executable(self) -> str:
        """The executable name of the host application."""

        return sys.executable

    @property
    def python_executable(self) -> str:
        """The Python executable name of the host application."""

        return sys.executable

    @property
    def is_headless(self) -> bool:
        """Whether the host application is running in headless mode or not."""

        return False
