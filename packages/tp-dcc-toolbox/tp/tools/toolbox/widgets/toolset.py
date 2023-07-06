from __future__ import annotations

from typing import List

from tp.common.qt import api as qt


class ToolsetWidget(qt.StackItem):
	"""
	Main widget class that is placed within toolbox tree widget items.
	"""

	ID = ''
	UI_DATA = {
		'label': 'Toolset', 'icon': 'tpdcc', 'tooltip': '', 'defaultActionDoubleClick': False, 'helpUrl': '',
		'autoLinkProperties': True}
	TAGS = []							# type: List[str]
	CREATOR = ''

	def __init__(self, parent: qt.QWidget | None = None):
		super().__init__(parent=parent)
