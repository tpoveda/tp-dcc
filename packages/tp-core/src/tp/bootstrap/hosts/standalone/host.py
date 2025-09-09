from __future__ import annotations

import sys
from pathlib import Path

from tp.core import host


class StandaloneHost(host.Host):
    """Host implementation for standalone applications."""

    def post_initialization(self):
        """Post-initialization method called after the host has been created
        but before any packages have been set up.

        Sets the internal `host` variable and host `name`.
        """

        self._host = StandaloneHostApplication("standalone", "0.0.0", 0)


class StandaloneHostApplication(host.HostApplication):
    """Host application implementation for standalone applications."""

    @property
    def install_location(self) -> str:
        """Returns the installation location of the host application."""

        return str(Path(sys.executable).parent)

    @property
    def qt_main_window(self) -> None:
        """The main window of the host application."""

        return None

    def python_executable(self) -> str:
        """Returns the path to the Python executable used by the host application."""

        return sys.executable

    def quit(self, force: bool = True):
        """Quits the host application.

        Args:
            force: Whether to force to quit the application or not.
        """

        sys.exit(0)

    def hotkey_set_exists(self, name: str) -> bool:
        """Checks if a hotkey set with the given name exists in the host application.

        Args:
            name: The name of the hotkey set to check.

        Returns:
            True if the hotkey set exists, False otherwise.
        """

        return False

    def current_hotkey_set_name(self) -> str:
        """Returns the name of the current hotkey set in the host application.

        Returns:
            The name of the current hotkey set.
        """

        return ""

    def set_source_key_set(self, name: str, source: str) -> bool:
        """Sets the source key set in the host application.

        Args:
            name: The name of the key set to set.
            source: The source of the key set to set as source.

        Returns:
            `True` if the key set was successfully set; `False` otherwise.
        """

        return True

    def set_source_key_set(self, name: str) -> bool:
        """Sets the source key set in the host application.

        Args:
            name: The name of the key set to set as source.

        Returns:
            `True` if the key set was successfully set; `False` otherwise.
        """

        return True

    def available_key_sets(self) -> list[str]:
        """Returns a list of available key sets in the host application.

        Returns:
            A list of available key set names.
        """

        return []

    def delete_key_set(self, name: str) -> bool:
        """Deletes a key set with the given name from the host application.

        Args:
            name: The name of the key set to delete.

        Returns:
            `True` if the key set was successfully deleted; `False` otherwise.
        """

        return True
