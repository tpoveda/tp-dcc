from overrides import override

from tp.core import dcc, tool
from tp.tools.renamer import consts


class RenamerTool(tool.Tool):

	id = consts.TOOL_ID
	creator = 'Tomi Poveda'
	tags = ['name', 'rename']

	@override
	def execute(self, *args, **kwargs):

		win = None
		if dcc.is_maya():
			from tp.tools.renamer.maya import view
			win = view.RenamerView()
			win.show()

		return win
