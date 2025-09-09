from __future__ import annotations

import os
import re
import sys
import platform
from typing import Any
from pathlib import Path
from functools import partial
from typing import cast, Optional

from maya import cmds
from loguru import logger
from maya import OpenMayaUI
from maya.api import OpenMaya
from Qt import QtCompat
from Qt.QtCore import Signal
from Qt.QtWidgets import QWidget, QMainWindow

from tp.core import host
from tp.libs.maya.meta import base


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

    def show_dialog(
        self,
        window_class: type[QWidget],
        name: str = "",
        show: bool = True,
        allows_multiple: bool = False,
        *class_args: Any,
        **class_kwargs: Any,
    ) -> QWidget:
        """Shows a dialog/window of the given class.

        Args:
            window_class: The class of the dialog to show.
            name: Name of the dialog.
            show: Whether to show the dialog immediately or not.
            allows_multiple: Whether to allow multiple instances of the dialog
                with the same name.
            class_args: Positional arguments to pass to the dialog class.
            class_kwargs: Keyword arguments to pass to the dialog class.

        Returns:
            The created and shown dialog instance.
        """

        matching_widget_instances = self._dialogs.get(name, [])
        if not allows_multiple:
            for instance in matching_widget_instances:
                logger.warning(
                    f"Only one instance of '{instance.objectName()}' allowed. "
                    f"Bringing it to front."
                )
                instance.activateWindow()
                instance.show()
                return instance

        if "parent" not in class_kwargs:
            class_kwargs["parent"] = self.host.qt_main_window

        widget = window_class(**class_kwargs)
        if hasattr(widget, "closed") and isinstance(widget.closed, Signal):
            # noinspection PyUnresolvedReferences
            widget.closed.connect(partial(self.close_dialog, name, widget))
        self.register_dialog(name, widget)

        if show:
            widget.show()

        return widget

    def shutdown(self):
        """Shuts down the host.

        Closes all the TP DCC tools dialogs/windows and removes the TP DCC
        menu and shelves.
        """

        logger.info("Unloading Maya tpDcc Python pipeline, please wait ...")
        if not self._host.is_headless:
            self.close_all_dialogs()

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
            force: Whether to force to quit the application or not.
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

    def hotkey_set_exists(self, name: str) -> bool:
        """Checks if a hotkey set with the given name exists in the host application.

        Args:
            name: The name of the hotkey set to check.

        Returns:
            True if the hotkey set exists, False otherwise.
        """

        return cmds.hotkeySet(name, exists=True)

    def current_hotkey_set_name(self) -> str:
        """Returns the name of the current hotkey set in the host application.

        Returns:
            The name of the current hotkey set.
        """

        return cmds.hotkeySet(query=True, current=True)

    def set_current_hotkey_set(self, name: str) -> bool:
        """Sets the current hotkey set in the host application.

        Args:
            name: The name of the hotkey set to set as current.

        Returns:
            `True` if the hotkey set was successfully set; `False` otherwise.
        """

        cmds.hotkeySet(name, current=True, edit=True)

        return True

    def set_source_key_set(self, name: str, source: str) -> bool:
        """Sets the source key set in the host application.

        Args:
            name: The name of the key set to set.
            source: The source of the key set to set as source.

        Returns:
            `True` if the key set was successfully set; `False` otherwise.
        """

        cmds.hotkeySet(name, source=source, current=True)

        return True

    def available_key_sets(self) -> list[str]:
        """Returns a list of available key sets in the host application.

        Returns:
            A list of available key set names.
        """

        # noinspection PyTypeChecker
        return cmds.hotkeySet(query=True, hotkeySetArray=True)

    def delete_key_set(self, name: str) -> bool:
        """Deletes a key set with the given name from the host application.

        Args:
            name: The name of the key set to delete.

        Returns:
            `True` if the key set was successfully deleted; `False` otherwise.
        """

        cmds.hotkeySet(name, edit=True, delete=True)

        return True
