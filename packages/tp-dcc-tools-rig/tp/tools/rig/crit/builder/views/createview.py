from __future__ import annotations

import typing

from tp.common.qt import api as qt

from tp.tools.rig.crit.builder.views import componentstree

if typing.TYPE_CHECKING:
	from tp.tools.rig.crit.builder.models.rig import RigModel
	from tp.tools.rig.crit.builder.ui import CritBuilderWindow


class CreateView(qt.QWidget):

	def __init__(self, parent: CritBuilderWindow | None = None):
		super().__init__(parent)

		self._crit_builder = parent

		self._components_tree_view = componentstree.ComponentsTreeView(parent=self)

		self._setup_ui()

	def apply_rig(self, rig_model: RigModel):
		"""
		Applies the given rig model to the component stack.

		:param RigModel rig_model: rig model instance.
		"""

		self._components_tree_view.clear()
		self._components_tree_view.apply_rig(rig_model)
		self._components_tree_view.sync()

	def clear_tree(self):
		"""
		Clears all the tree nodes in the tree widget.
		"""

		self._components_tree_view.tree_widget.clear()

	def _setup_ui(self):
		"""
		Internal function that setups create view UI.
		"""

		main_layout = qt.vertical_layout()
		self.setLayout(main_layout)

		main_layout.addWidget(self._components_tree_view)
