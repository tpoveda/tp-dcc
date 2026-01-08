from __future__ import annotations

import sys
from functools import partial
from pathlib import Path
from typing import Any

from loguru import logger
from Qt.QtCore import Signal
from Qt.QtWidgets import QApplication, QWidget

from tp.core import host


class StandaloneHost(host.Host):
    """Host implementation for standalone applications."""

    def post_initialization(self):
        """Post-initialization method called after the host has been created
        but before any packages have been set up.

        Sets the internal `host` variable and host `name`.
        """

        self._host = StandaloneHostApplication("standalone", "0.0.0", 0)

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

        # noinspection PyArgumentList
        app = QApplication.instance()
        if app is None:
            # noinspection PyUnusedLocal
            app = QApplication(sys.argv)

        widget = window_class(**class_kwargs)
        if hasattr(widget, "closed") and isinstance(widget.closed, Signal):
            # noinspection PyUnresolvedReferences
            widget.closed.connect(partial(self.close_dialog, name, widget))
        self.register_dialog(name, widget)

        if show:
            widget.show()

        return widget

    def close_dialog(self, name: str, widget: QWidget):
        """Closes a registered dialog/window.

        Args:
            name: Name of the dialog.
            widget: The dialog instance to close.
        """

        super().close_dialog(name, widget)

        if not self._dialogs.get(name, []):
            # noinspection PyArgumentList
            app = QApplication.instance()
            if app is not None:
                app.quit()

    def close_all_dialogs(self):
        """Closes all registered dialog/windows."""

        super().close_all_dialogs()

        # noinspection PyArgumentList
        app = QApplication.instance()
        if app is not None:
            app.quit()


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

    def set_current_hotkey_set(self, name: str) -> bool:
        """Sets the current hotkey set in the host application.

        Args:
            name: The name of the hotkey set to set as current.

        Returns:
            `True` if the hotkey set was successfully set; `False` otherwise.
        """

        return True

    def set_source_key_set(self, name: str, source: str) -> bool:
        """Sets the source key set in the host application.

        Args:
            name: The name of the key set to set.
            source: The source of the key set to set as the source.

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
