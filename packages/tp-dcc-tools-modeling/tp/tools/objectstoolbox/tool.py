from overrides import override

import os
import inspect

from tp.core import dcc, tool

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
			from tp.tools.modelchecker.maya import controller
			win = view.ObjectsToolboxView(
				controller=controller.MayaObjecstToolboxController(commands_data, command_module_paths))
			win.show()

		return win
