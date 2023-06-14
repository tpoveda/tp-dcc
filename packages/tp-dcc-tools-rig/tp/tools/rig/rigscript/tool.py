from overrides import override

from tp.core import dcc, tool

from tp.tools.rig.rigscript import consts


class RigScriptTool(tool.Tool):

	id = consts.TOOL_ID
	creator = 'Tomi Poveda'
	tags = ['rig', 'script']

	@override
	def execute(self, *args, **kwargs):

		win = None
		if dcc.is_maya():
			from tp.tools.rig.rigscript.maya import view
			win = view.RigScriptView()
			win.show()

		return win
