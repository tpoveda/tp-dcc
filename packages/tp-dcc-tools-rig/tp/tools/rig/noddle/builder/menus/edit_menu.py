from __future__ import annotations

import typing

from tp.common.qt import api as qt
from tp.common.resources import api as resources

if typing.TYPE_CHECKING:
    from tp.tools.rig.noddle.builder.window import NoddleBuilderWindow


class EditMenu(qt.QMenu):
    def __init__(self, main_window: NoddleBuilderWindow, parent: qt.QWidget | None = None):
        super().__init__(parent=parent or main_window)

        self._main_window = main_window
        self._workspace_widget = main_window.workspace_widget

        self._setup_actions()
        self._setup_shortcuts()
        self._setup_sub_menus()
        self._populate()
        self._setup_signals()

        self.setTearOffEnabled(True)

    def _setup_actions(self):
        """
        Internal function that creates all menu actions.
        """

        pass

    def _setup_shortcuts(self):
        """
        Internal function that setup all action shortcuts
        """

        pass

    def _setup_sub_menus(self):
        """
        Internal function that creates all menu sub-menus.
        """

        pass

    def _populate(self):
        """
        Internal function that populates sub-menus and menu itself.
        """

        pass

    def _setup_signals(self):
        """
        Internal function that setup menu actions signal connections.
        """

        pass
