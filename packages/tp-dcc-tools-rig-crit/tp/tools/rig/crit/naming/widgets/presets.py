from __future__ import annotations

from overrides import override

from tp.common.qt import api as qt
from tp.libs.rig.crit import api as crit


class PresetView(qt.ExtendedTreeView):
	def __init__(
			self, title: str = 'Presets', parent: qt.QWidget | None = None, expand: bool = True, sorting: bool = True):
		super().__init__(title=title, parent=parent, expand=expand, sorting=sorting)

		self.tree_view.setHeaderHidden(True)

		self._root_source = PresetDataSource('')
		self._preset_model = qt.BaseTreeModel(root=self._root_source, parent=self)
		self.set_model(self._preset_model)

	@property
	def preset_model(self) -> qt.BaseTreeModel:
		return self._preset_model

	def load_preset(
			self, preset: crit.namingpresets.Preset, include_root: bool = True,
			parent: qt.BaseDataSource | None = None):
		"""
		Loads the given preset as root view preset.

		:param  crit.namingpresets.Preset preset: root preset to load.
		:param bool include_root: whether to only load the given preset or their children.
		:param qt.BaseDataSource or None parent: optional data source parent.
		"""

		self._root_source.set_user_objects([])
		if include_root:
			self._load_preset(preset, parent=parent)
		else:
			for child in preset.children:
				self._load_preset(child, parent=parent)

		self._preset_model.refresh()
		self.refresh()
		self.expand_all()

	def _load_preset(self, preset: crit.namingpresets.Preset, parent: qt.BaseDataSource | None = None):
		"""
		Internal function that handles the loading of the given preset.

		:param  crit.namingpresets.Preset preset: root preset to load.
		:param qt.BaseDataSource or None parent: optional data source parent.
		"""

		parent = parent or self._root_source
		preset_data_source = PresetDataSource(preset.name, parent=parent)
		parent.add_child(preset_data_source)
		for child in preset.children:
			self._load_preset(child, parent=preset_data_source)


class PresetDataSource(qt.BaseDataSource):
	def __init__(
			self, label: str, previous_label: str = '', header_text='Preset Name',
			model: qt.QAbstractItemModel | None = None, parent: qt.QWidget | None = None):
		super().__init__(header_text=header_text, model=model, parent=parent)

		self._label = label
		self._previous_label = previous_label

	@override
	def data(self, index: int) -> str:
		return self._label

	@override
	def set_data(self, index: int, value: str) -> bool:
		self._previous_label = str(self._label)
		self._label = value
		return True
