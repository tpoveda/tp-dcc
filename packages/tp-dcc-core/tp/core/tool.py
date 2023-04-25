#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains classes to define Dcc tools
"""

from tp.core import log, window, menu

logger = log.tpLogger


class DccTool(object):
    """
    Base class used by Dcc tools
    """

    ID = None

    def __init__(self):
        super().__init__()

        self._parent = None
        self._menu_manager = menu.MenuManager()

        self.ui = None
        self.window = None

        self._setup_ui()

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def setup_ui(self):
        """
        Function that can be overridden to add custom ui.
        """

        pass

    def show(self):
        """
        Shows DCC tool UI
        """

        if not self.window:
            logger.warning('Tool {} has no UI defined!'.format(self))
            return

        self.window.show()

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _setup_ui(self):
        """
        Internal function that setups tool UI.
        """

        self.setup_ui()
        if not self.ui:
            return

        self.window = window.Window(id=self.__class__.__name__)
        self.window.main_layout.addWidget(self.ui)
