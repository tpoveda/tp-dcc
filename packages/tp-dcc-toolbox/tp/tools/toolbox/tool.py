from overrides import override

from tp.core import tool
from tp.tools.toolbox import view


class Toolbox(tool.Tool):

	id = 'tp.tools.toolbox'
	creator = 'Tomi Poveda'
	tags = ['toos', 'toolbox']
	ui_data = {
		'icon': 'tpdcc', 'tooltip': 'Toolbox window', 'label': 'Toolbox', 'color': '', 'backgroundColor': '',
		'multipleTools': True, 'dock': {'dockable': True, 'tabControl': ("AttributeEditor", -1), 'floating': False}}

	@override
	def execute(self, *args, **kwargs):
		return view.ToolBoxWindow.launch(toolbox_kwargs=kwargs or {})
