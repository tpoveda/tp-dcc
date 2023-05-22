#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Dcc window classes
"""

import sys

from Qt.QtWidgets import QApplication

from tp.core import dcc


if dcc.is_mayapy():
    QApplication(sys.argv)
    from tp.maya.ui.window import MayaBatchWindow as Window
elif dcc.is_maya():
    from tp.maya.ui.window import MayaWindow as Window
elif dcc.is_nuke():
    from tp.nuke.ui.window import NukeWindow as Window
elif dcc.is_houdini():
    from tp.houdini.ui.window import HoudiniWindow as Window
elif dcc.is_blender():
    from tp.blender.ui.window import BlenderWindow as Window
elif dcc.is_unreal():
    from tp.unreal.ui.window import UnrealWindow as Window
elif dcc.is_max():
    from tp.max.ui.window import MaxWindow as Window
elif dcc.is_substance_painter():
    from tp.painter.ui.window import SubstancePainterWindow as Window
elif dcc.is_substance_designer():
    from tp.designer.ui.window import SubstanceDesignerWindow as Window
elif dcc.is_fusion():
    from tp.fusion.ui.window import FusionWindow as Window
else:
    from tp.common.qt.widgets.windows import StandaloneWindow as Window
