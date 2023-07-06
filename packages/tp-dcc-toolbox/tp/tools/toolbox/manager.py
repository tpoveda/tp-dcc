from tp.common import plugin
from tp.common.python import decorators


@decorators.add_metaclass(decorators.Singleton)
class ToolboxManager:

	def __init__(self):
		super().__init__()

		self._toolbox_factory = plugin.PluginFactory(interface=[ToolsManager], plugin_id='APPLICATION', name='Toolbox')

	def shutdown(self):
		pass
