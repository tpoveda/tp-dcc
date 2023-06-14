from overrides import override

from tp.core import log, dcc, tool
from tp.common.qt import api as qt

from tp.tools.rig.crit.naming import ui as naming
from tp.tools.rig.crit.builder import ui as builder

logger = log.rigLogger


class CritTool(tool.Tool):

	id = 'tp.rig.crit.ui'
	creator = 'Tomi Poveda'
	tags = ['crit', 'rig', 'ui']

	@override
	def execute(self, *args, **kwargs):

		if not dcc.is_maya() or dcc.version() < 2020:
			qt.show_warning(title='Unsupported version', message='Only supports Maya +2020')
			return

		win = builder.CritBuilderWindow()
		win.show()


class CritNamingConvention(tool.Tool):

	id = 'tp.rig.crit.naming'
	creator = 'Tomi Poveda'
	tags = ['crit', 'rig', 'ui', 'naming']

	@override
	def execute(self, *args, **kwargs):

		if not dcc.is_maya() or dcc.version() < 2020:
			qt.show_warning(title='Unsupported version', message='Only supports Maya +2020')
			return

		win = naming.NamingConventionWindow()
		win.show()

		return win
