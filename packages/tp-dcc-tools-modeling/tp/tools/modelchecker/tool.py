from overrides import override

import os
import inspect

from tp.core import dcc, tool
from tp.common.python import path, yamlio

from tp.tools.modelchecker import view


def root_path():
	"""
	Returns the root directory.

	:return tp-dcc tools repository root path.
	:rtype: str
	"""

	return os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


class ModelCheckerTool(tool.Tool):

	id = 'tp.modeling.modelchecker'
	creator = 'Tomi Poveda'
	tags = ['model', 'checker']

	@override
	def execute(self, *args, **kwargs):

		commands_data = {}
		commands_path = path.join_path(root_path(), dcc.name(), 'commands.yaml')
		if path.is_file(commands_path):
			commands_data = yamlio.read_file(commands_path, maintain_order=True)

		command_module_paths = os.getenv('MODEL_CHECKER_MODULES_PATHS', '').split(os.pathsep)

		win = None
		if dcc.is_maya():
			from tp.tools.modelchecker.maya import controller
			win = view.ModelCheckerView(
				controller=controller.MayaModelCheckerController(commands_data, command_module_paths))
			win.show()

		return win
