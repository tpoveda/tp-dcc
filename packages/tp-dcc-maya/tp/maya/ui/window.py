#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functionality for Maya windows
"""

from Qt.QtCore import Qt, QSize
from Qt.QtWidgets import QWidget, QMainWindow

import maya.cmds
import maya.OpenMayaUI
import maya.app.general.mayaMixin

from tp.common.qt.widgets import layouts

BOOTSTRAP_WIDGETS = dict()


class MayaWindow(window.MainWindow, object):
    def __init__(self, *args, **kwargs):
        super(MayaWindow, self).__init__(*args, **kwargs)
        self.setProperty('saveWindowPref', True)

    def bootstrap_widget(self):
        bootstrap_widget = self.property("bootstrapWidget")

        if self._current_docked is None and bootstrap_widget is not None:
            self._current_docked = not bootstrap_widget.isFloating()

        return bootstrap_widget

    def docked(self):
        """
        Returns if the window is current docked
        """

        bootstrap = self.bootstrap_widget()

        if bootstrap is None:
            return False
        else:
            return not bootstrap.isFloating()

    def close(self):
        try:
            super(MayaWindow, self).close()
        except RuntimeError:
            pass

        if self.docked():
            self.delete_bootstrap()

    def delete_bootstrap(self):
        """ Delete the bootstrap Widget

        :return:
        :rtype:
        """
        bootstrap = self.bootstrap_widget()

        if bootstrap is not None:
            self.setProperty("bootstrapWidget", None)   # avoid recursion by setting to none
            bootstrap.close()


# class MayaDockWindow(core_window.DockWindow, object):
#     def __init__(self, *args, **kwargs):
#         super(MayaDockWindow, self).__init__(*args, **kwargs)
#
#
# class MayaSubWindow(core_window.SubWindow, object):
#     def __init__(self, *args, **kwargs):
#         super(MayaSubWindow, self).__init__(*args, **kwargs)


class BootStrapWidget(maya.app.general.mayaMixin.MayaQWidgetDockableMixin, QWidget):
    width = maya.cmds.optionVar(query='workspacesWidePanelInitialWidth') * 0.75
    INITIAL_SIZE = QSize(width, 600)
    PREFERRED_SIZE = QSize(width, 420)
    MINIMUM_SIZE = QSize((width * 0.95), 220)

    def __init__(self, widget, title, icon=None, uid=None, parent=None):
        super(BootStrapWidget, self).__init__(parent=parent)

        self._preferred_size = self.PREFERRED_SIZE

        # This cannot be an empty string, otherwise Maya will get crazy
        uid = uid or title or 'BootstrapWidget'
        global BOOTSTRAP_WIDGETS
        BOOTSTRAP_WIDGETS[uid] = self

        # This was causing the dock widge to disappear after creation
        # Not sure why, maybe because the id had - characters, or because maybe there was a widget with the same
        # objectName, for now no setting an objectName seems to work fine
        # self.setObjectName(uid)
        self.setWindowTitle(title)
        if icon:
            self.setWindowIcon(icon)
        self._docking_frame = QMainWindow(self)
        self._docking_frame.layout().setContentsMargins(0, 0, 0, 0)
        self._docking_frame.setWindowFlags(Qt.Widget)
        self._docking_frame.setDockOptions(QMainWindow.AnimatedDocks)

        self.central_widget = widget
        self._docking_frame.setCentralWidget(self.central_widget)

        bootstrap_layout = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        bootstrap_layout.addWidget(self._docking_frame, 0)
        self.setLayout(bootstrap_layout)
        widget.setProperty('bootstrapWidget', self)

    def __del__(self, *args, **kwargs):
        """
        Overriding to do nothing to avoid C++ object already deleted error
        since they try to destroy the workspace after its QObject has already been deleted
        """

        pass

    def setSizeHint(self, size):
        self._preferred_size = size

    def close(self, *args, **kwargs):
        """
        Overridden to call the bootstrap user widget.close()
        """

        self.central_widget.close()
        super(BootStrapWidget, self).close(*args, **kwargs)

    def show(self, **kwargs):
        name = self.objectName()
        name = name + "WorkspaceControl"
        if maya.cmds.workspaceControl(name, query=True, exists=True):
            maya.cmds.deleteUI(name)
            maya.cmds.workspaceControlState(name, remove=True)
        kwargs["retain"] = False
        kwargs["uiScript"] = 'try: from tp.maya.ui import window;window.rebuild("{}")\n' \
                             'except ImportError: pass'.format(self.objectName())
        kwargs["closeCallback"] = 'try: from tp.maya.ui import window;window.bootstrap_destroy_window("{}")\n' \
                                  'except ImportError: pass'.format(self.objectName())
        super(BootStrapWidget, self).show(**kwargs)


def rebuild(object_name):
    """
    If the bootstrap widget exists then we reapply it to mayas layout, otherwise do nothing.

    :param object_name: the bootStrap objectName
    :type object_name: str
    """
    global BOOTSTRAP_WIDGETS
    wid = BOOTSTRAP_WIDGETS.get(object_name)
    if wid is None:
        return False

    parent = maya.OpenMayaUI.MQtUtil.getCurrentParent()
    mixin_ptr = maya.OpenMayaUI.MQtUtil.findControl(wid.objectName())
    maya.OpenMayaUI.MQtUtil.addWidgetToMayaLayout(int(mixin_ptr), int(parent))
    return True


def bootstrap_destroy_window(object_name):
    """
    Function to destroy a bootstrapped widget, this use the maya workspaceControl objectName
    :param object_name: The bootstrap Widget objectName
    :type object_name: str
    :rtype: bool
    """
    global BOOTSTRAP_WIDGETS
    wid = BOOTSTRAP_WIDGETS.get(object_name)

    if wid is not None:
        BOOTSTRAP_WIDGETS.pop(object_name)
        wid.close()
        return True
    return False


class MayaDockedWindow(maya.app.general.mayaMixin.MayaQWidgetDockableMixin, window.MainWindow):
    def __init__(self, parent=None, **kwargs):
        self._dock_area = kwargs.get('dock_area', 'right')
        self._dock = kwargs.get('dock', False)
        super(MayaDockedWindow, self).__init__(parent=parent, **kwargs)

        self.setProperty('saveWindowPref', True)

        if self._dock:
            self.show(dockable=True, floating=False, area=self._dock_area)

    def ui(self):
        if self._dock:
            ui_name = str(self.objectName())
            if maya.cmds.about(version=True) >= 2017:
                workspace_name = '{}WorkspaceControl'.format(ui_name)
                workspace_name = workspace_name.replace(' ', '_')
                workspace_name = workspace_name.replace('-', '_')
                if maya.cmds.workspaceControl(workspace_name, exists=True):
                    maya.cmds.deleteUI(workspace_name)
            else:
                dock_name = '{}DockControl'.format(ui_name)
                dock_name = dock_name.replace(' ', '_')
                dock_name = dock_name.replace('-', '_')
                # dock_name = 'MayaWindow|%s' % dock_name       # TODO: Check if we need this
                if maya.cmds.dockControl(dock_name, exists=True):
                    maya.cmds.deleteUI(dock_name, controlong=True)

            self.setAttribute(Qt.WA_DeleteOnClose, True)

        super(MayaDockedWindow, self).ui()
