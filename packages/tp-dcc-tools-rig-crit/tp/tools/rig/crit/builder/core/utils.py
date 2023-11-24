import maya.cmds as cmds

from tp.maya.om import scene
from tp.common.qt import api as qt

SCENE_UNITS_MSG = """CRIT must be in centimeter units while building. Please switch to centimeters (cm).

Preferences > Settings > Linear: centimeter.

After building completion you can switch back. Switch to cm units now?"""


def check_scene_units(parent: qt.QWidget) -> bool:
	"""
	Returns whether current scene units are valid.

	:param qt.QWidget parent: parent widget.
	:return: True if scene units are valid; False otherwise.
	:rtype: bool
	"""

	if not scene.is_centimeters():
		result = qt.show_warning('Incorrect working units', message=SCENE_UNITS_MSG, parent=parent)
		if result == 'A':
			cmds.currentUnit(linear='cm')
			return True
		return False
	return True
