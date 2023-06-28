from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
	from tp.tools.rig.crit.builder.ui import CritBuilderWindow
	from tp.tools.rig.crit.builder.controller import CritBuilderController
	from tp.tools.rig.crit.builder.views.componentstree import ComponentsTreeWidget


class CritUiInterface:
	"""
	Class that stores references to different CRIT related UIs/widgets. Used to simplify the code when needed to connect
	different CRIT widgets.
	"""

	_INSTANCE = None							# type: CritUiInterface

	def __init__(self):
		super().__init__()

		self._crit_builder = None				# type: CritBuilderWindow
		self._controller = None					# type: CritBuilderController
		self._components_tree = None			# type: ComponentsTreeWidget

	@classmethod
	def create(cls) -> CritUiInterface:
		"""
		Returns CRIT UI interface instance. Creates a new one if it does not exist.

		:return: CRIT UI interface instance.
		:rtype: CritUiInterface
		"""

		if not CritUiInterface._INSTANCE:
			CritUiInterface._INSTANCE = CritUiInterface()

		return CritUiInterface._INSTANCE

	@classmethod
	def instance(cls) -> CritUiInterface | None:
		"""
		Returns CRIT UI interface instance.

		:return: CRIT UI interface instance.
		:rtype: CritUiInterface or None
		"""

		return CritUiInterface._INSTANCE

	@classmethod
	def destroy(cls):
		"""
		Deletes CRIT UI interface instance.
		"""

		CritUiInterface._INSTANCE = None

	def refresh_ui(self, force: bool = False):
		"""
		Refreshes all CRIT related UIs.

		:param bool force: whether to force the refresh.
		"""

		self._crit_builder.refresh_ui() if force else self._crit_builder.check_refresh()

	def builder(self) -> CritBuilderWindow | None:
		"""
		Returns CRIT Builder window reference.

		:return: CRIT Builder window instance.
		:rtype: CritBuilderWindow or None
		"""

		return self._crit_builder

	def set_builder(self, value: CritBuilderWindow):
		"""
		Sets CRIT Builder window reference.

		:param CritBuilderWindow value: CRIT Builder window instance.
		"""

		self._crit_builder = value

	def controller(self) -> CritBuilderController | None:
		"""
		Returns CRIT Builder controller reference.

		:return: CRIT Builder controller instance.
		:rtype: CritBuilderController or None
		"""

		return self._controller

	def set_controller(self, value: CritBuilderController):
		"""
		Sets CRIT Builder controller reference.

		:param CritBuilderController value: CRIT Builder controller instance.
		"""

		self._controller = value

	def components_tree(self) -> ComponentsTreeWidget | None:
		"""
		Returns the components tree view instance.

		:return: components tree view.
		:rtype: ComponentsTreeWidget or None
		"""

		return self._components_tree

	def set_components_tree(self, value: ComponentsTreeWidget):
		"""
		Sets components tree view instance.

		:param ComponentsTreeWidget value: components tree view.
		"""

		self._components_tree = value
