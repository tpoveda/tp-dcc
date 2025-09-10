from __future__ import annotations

from maya import cmds
from Qt.QtWidgets import QWidget, QMessageBox

from tp.libs.maya.om import scene

SCENE_UNIT_MSG = """ModRig must be in centimeter units while building. 
Please switch to cms.

Preferences > Settings > Linear: centimeter.

After completion any unit scale may be used for animation.
You can switch back after the rig has been built.

Switch to cm units now?"""


def check_scene_units(parent: QWidget | None = None) -> bool:
    """Checks if the scene is in centimeter units. If not, prompts the user
    to switch to centimeters.

    Args:
        parent: Optional QWidget parent for the message box.

    Returns:
        `True` if the scene is in centimeters or the user chose to switch,
        `False` otherwise.
    """

    if scene.is_centimeters():
        return True

    result = QMessageBox.warning(
        parent,
        "Incorrect Working Units",
        SCENE_UNIT_MSG,
        QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
    )
    if result == QMessageBox.Yes:
        cmds.currentUnit(linear="cm")
        return True

    return False
