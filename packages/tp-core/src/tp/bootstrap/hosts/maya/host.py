from __future__ import annotations

import os
import re
import sys
import logging
import platform
from pathlib import Path
from typing import cast, Optional

from maya import cmds
from maya import OpenMayaUI
from maya.api import OpenMaya
from Qt import QtCompat
from Qt.QtWidgets import QMainWindow

from tp.bootstrap.core import host
from tp.libs.maya.meta import base

logger = logging.getLogger(__name__)


class MayaHost(host.Host):
    """Host implementation for Maya."""

    def post_initialization(self):
        """Post-initialization method called after the host has been created
        but before any packages have been set up.

        Sets the internal `host` variable and host `name`.
        """

        version = cmds.about(installedVersion=True)
        matches = re.search(
            r"(maya)\s+([a-zA-Z]+)?\s*(.*)",
            version,
            re.IGNORECASE,
        )
        self._host = MayaHostApplication("maya", version, matches.group(3))

    def post_environment_initialization(self):
        """Post-environment initialization method called after all packages
        have been set up.

        Creates the TP DCC menu and shelves in Maya and handles the
        registration of metadata classes.
        """

        base.MetaRegistry()

    def shutdown(self):
        """Shuts down the host.

        Closes all the TP DCC tools dialogs/windows and removes the TP DCC
        menu and shelves.
        """

        logger.info("Unloading TP DCC Python pipeline, please wait ...")
        if not self._host.is_headless:
            pass

        cmds.flushUndo()


class MayaLoguruHandler:
    """Custom Loguru sink for Maya.

    This class is used to display log messages in the Maya script editor.
    It overrides the `__call__` method to handle different log levels and
    display the messages accordingly and with the correct color.
    """

    def __call__(self, message):
        text = message.format()
        level = message.record["level"].name

        if level == "INFO":
            OpenMaya.MGlobal.displayInfo(text)
        elif level == "WARNING":
            OpenMaya.MGlobal.displayWarning(text)
        elif level in ("ERROR", "CRITICAL"):
            OpenMaya.MGlobal.displayError(text)
        else:
            sys.__stdout__.write(f"{text}\n")
            sys.__stdout__.flush()


class MayaHostApplication(host.HostApplication):
    """Host application implementation for Maya."""

    @property
    def install_location(self) -> str:
        """Returns the installation location of the host application."""

        return str(Path(sys.executable).parent.parent)

    @property
    def qt_main_window(self) -> QMainWindow | None:
        """The main window of the host application."""

        ptr = OpenMayaUI.MQtUtil.mainWindow()
        return cast(Optional[QMainWindow], QtCompat.wrapInstance(int(ptr), QMainWindow))

    @property
    def python_executable(self) -> str:
        """The Python executable name of the host application."""

        pyexe = os.path.join(self._maya_location(self._version), "bin", "mayapy")
        if platform.system() == "Windows":
            pyexe += ".exe"

        return pyexe

    def quit(self, force: bool = True):
        """Quits the host application.

        Args:
            force: Whether to force quit the application or not.
        """

        cmds.quit(force=force)

    @staticmethod
    def _maya_location(version: str) -> str:
        """Internal function that returns location where Maya is installed.

        Args:
            version: The version of Maya to get the location for.

        Returns:
            The location where Maya is installed.
        """

        location = os.environ.get("MAYA_LOCATION", "")
        if location:
            return location

        system = platform.system()
        if system == "Windows":
            return str(Path("C:/Program Files/Autodesk") / f"Maya{version}")

        elif system == "Darwin":
            return str(
                Path("/Applications/Autodesk")
                / f"maya{version}"
                / "Maya.app"
                / "Contents"
            )
        else:
            return str(Path("/usr/autodesk") / f"maya{version}-x64")
