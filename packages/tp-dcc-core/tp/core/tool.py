#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains classes to define Dcc tools
"""

from tp.core import log, window, menu

logger = log.tpLogger


class DccTool:
    """
    Base class used by tp-dcc-tools framework to implement DCC tools that have access to tp-dcc-tools functionality.
    """

    ID = None                               # Unique tool ID
    UI_DATA = {                             # Dictionary containing tool DCC UI related data
        'label': 'DCC Tool',
        'icon': 'tpdcc',
        'tooltip': '',
        'helpUrl': ''
    }
    TAGS = []                               # List of tags that can be use to filter tools within DCC menus
    CREATOR = ''                            # Tool creator

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
