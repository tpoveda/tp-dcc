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
