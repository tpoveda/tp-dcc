from overrides import override

from tp.core import dcc, tool


class NoddleTool(tool.Tool):

	id = 'tp.rig.noddle'
	creator = 'Tomi Poveda'
	tags = ['rig', 'script']

	@override
	def execute(self, *args, **kwargs):

		win = None
		if dcc.is_maya():
			from tp.tools.rig.noddle.maya import view
			win = view.NoddleView()
			win.show()

		return win
