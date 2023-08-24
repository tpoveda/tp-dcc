from overrides import override

from tp.core import dcc, tool

from tp.tools.animpicker import view


class AnimPickerTool(tool.Tool):

	id = 'tp.animation.animpicker'
	creator = 'Tomi Poveda'
	tags = ['animation', 'poses', 'picker']

	@override
	def execute(self, *args, **kwargs):

		win = None
		if dcc.is_maya():
			from tp.tools.animpicker.maya import controller
			win = view.AnimPickerView(
				controller=controller.MayaAnimPickerController())
			win.show()

		return win
