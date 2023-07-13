from overrides import override

import os
import inspect

from tp.core import dcc, tool
from tp.common.qt import api as qt

from tp.tools.objectstoolbox import view


def root_path():
	"""
	Returns the root directory.

	:return tp-dcc tools repository root path.
	:rtype: str
	"""

	return os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


class ObjectsToolbox(tool.Tool):

	id = 'tp.modeling.objectstoolbox'
	creator = 'Tomi Poveda'
	tags = ['model', 'objects', 'toolbox']

	@override
	def execute(self, *args, **kwargs):

		win = None
		if dcc.is_maya():
			from tp.tools.objectstoolbox.maya import controller
			toolbox_view = view.ObjectsToolboxView(controller=controller.MayaObjectsToolboxController())
			win = qt.FramelessWindow()
			win.main_layout().addWidget(toolbox_view)
			win.show()

		return win
