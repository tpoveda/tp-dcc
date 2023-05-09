from tp.core.managers import tools
from tp.maya.managers import shelves


class MayaToolsManager(tools.ToolsManager):

	APPLICATION = 'maya'

	def __init__(self, parent=None):
		super().__init__(parent=parent)

		self._shelves_manager = shelves.ShelvesManager()
