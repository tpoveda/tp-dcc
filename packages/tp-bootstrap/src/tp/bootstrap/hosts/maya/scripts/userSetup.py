from __future__ import annotations

import os
import sys

from maya import cmds


def setup():
    """Loads TP DCC Pipeline for Autodesk Maya."""

    scripts_folder = os.path.dirname(__file__)
    plugins_folder = os.path.join(os.path.dirname(scripts_folder), "plug-ins")
    for folder in [scripts_folder, plugins_folder]:
        if folder not in sys.path:
            sys.path.append(folder)

    cmds.loadPlugin("tpplugin.py")
