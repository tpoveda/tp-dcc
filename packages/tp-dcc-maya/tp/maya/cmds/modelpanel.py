#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions to work with Maya model panels
"""

from Qt.QtWidgets import QWidget, QVBoxLayout

import maya.cmds

from tp.maya.cmds import gui


class ModelPanelWidget(QWidget, object):
    def __init__(self, name='modelPanelWidget', **kwargs):
        super(ModelPanelWidget, self).__init__(**kwargs)

        unique_name = name + str(id(self))
        self.setObjectName(unique_name + 'Widget')
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setObjectName(unique_name + 'Layout')
        self.setLayout(main_layout)

        maya.cmds.setParent(main_layout.objectName())
        pane_layout_name = maya.cmds.paneLayout()
        self._model_panel = maya.cmds.modelPanel(unique_name, label="ModelPanel", menuBarVisible=False)
        pane_layout_widget = gui.to_qt_object(pane_layout_name)
        main_layout.addWidget(pane_layout_widget)
        self.set_model_panel_options()
        self.hide_bar_layout()
        self.hide_menu_bar()
        # self.show_bar_layout()

    def name(self):
        """
        Returns model panel name
        :return: str
        """

        return self._model_panel

    def model_panel(self):
        """
        Returns model panel widget
        :return:
        """

        return gui.to_qt_object(self.name())

    def bar_layout(self):
        """
        Returns model panel bar layout
        :return: str
        """

        return maya.cmds.modelPanel(self.name(), query=True, barLayout=True)

    def show_bar_layout(self):
        """
        Shows model panel bar layout
        """

        bar_layout = self.bar_layout()
        if maya.cmds.frameLayout(bar_layout, query=True, exists=True):
            maya.cmds.frameLayout(bar_layout, edit=True, collapse=False)

    def hide_bar_layout(self):
        """
        Hides model panel bar layout
        """

        bar_layout = self.bar_layout()
        if maya.cmds.frameLayout(bar_layout, query=True, exists=True):
            maya.cmds.frameLayout(bar_layout, edit=True, collapse=True)

    def show_menu_bar(self):
        """
        Shows model panel menu bar
        """

        maya.cmds.modelPanel(self.name(), edit=True, menuBarVisible=True)

    def hide_menu_bar(self):
        """
        Hides model panel menu bar
        """

        maya.cmds.modelPanel(self.name(), edit=True, menuBarVisible=False)

    def set_camera(self, camera_name):
        """
        Sets the camera used by the model panel
        :param camera_name: str
        """

        maya.cmds.modelPanel(self.name(), edit=True, cam=camera_name)

    def set_model_panel_options(self):
        """
        Set options for model panel
        """

        model_panel = self.name()

        maya.cmds.modelEditor(model_panel, edit=True, allObjects=False)
        maya.cmds.modelEditor(model_panel, edit=True, grid=False)
        maya.cmds.modelEditor(model_panel, edit=True, dynamics=False)
        maya.cmds.modelEditor(model_panel, edit=True, activeOnly=False)
        maya.cmds.modelEditor(model_panel, edit=True, manipulators=False)
        maya.cmds.modelEditor(model_panel, edit=True, headsUpDisplay=False)
        maya.cmds.modelEditor(model_panel, edit=True, selectionHiliteDisplay=False)

        maya.cmds.modelEditor(model_panel, edit=True, polymeshes=True)
        maya.cmds.modelEditor(model_panel, edit=True, nurbsSurfaces=True)
        maya.cmds.modelEditor(model_panel, edit=True, subdivSurfaces=True)
        maya.cmds.modelEditor(model_panel, edit=True, displayTextures=True)
        maya.cmds.modelEditor(model_panel, edit=True, displayAppearance="smoothShaded")

        current_model_panel = gui.current_model_panel()

        if current_model_panel:
            camera = maya.cmds.modelEditor(current_model_panel, query=True, camera=True)
            display_lights = maya.cmds.modelEditor(current_model_panel, query=True, displayLights=True)
            display_textures = maya.cmds.modelEditor(current_model_panel, query=True, displayTextures=True)

            maya.cmds.modelEditor(model_panel, edit=True, camera=camera)
            maya.cmds.modelEditor(model_panel, edit=True, displayLights=display_lights)
            maya.cmds.modelEditor(model_panel, edit=True, displayTextures=display_textures)
