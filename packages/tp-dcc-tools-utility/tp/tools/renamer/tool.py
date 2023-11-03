from overrides import override

from tp.core import dcc, tool


class RenamerTool(tool.Tool):

	id = 'tp.utility.renamer'
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


from tp.core.managers import tools
tools.ToolsManager().launch_tool_by_id('tp.utility.renamer')