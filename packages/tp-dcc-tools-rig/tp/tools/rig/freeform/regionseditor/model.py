from __future__ import annotations

from typing import Any

from overrides import override

from tp.common.qt import api as qt


class RegionEvent:
	def __init__(
			self, region: FreeformRegion | None = None, data: str = '', success: bool = False, valid: bool = True, value: str = ''):

		self.region = region
		self.data = data
		self.success = success
		self.valid = valid

		self.value = value


class FreeformRegion:
	def __init__(
			self, side: str, name: str, group: str, root: str, end: str, com_object: str, com_region: str,
			com_weight: float):
		self.side = side
		self.name = name
		self.group = group
		self.root = root
		self.end = end
		self.com_object = com_object
		self.com_region = com_region
		self.com_weight = com_weight


class FreeformRegionsListModel(qt.QAbstractListModel):

	def __init__(self):
		super().__init__()

		self._regions: list[FreeformRegion] = []

	@property
	def regions(self) -> list[FreeformRegion]:
		return self._regions

	@override
	def rowCount(self, parent: qt.QModelIndex = qt.QModelIndex()):
		return len(self._regions)

	@override
	def data(self, index: qt.QModelIndex, role: qt.Qt.ItemDataRole = ...) -> Any:
		if role == qt.Qt.DisplayRole:
			row = index.row()
			return f'{self._regions[row].side} {self._regions[row].name}'

	@override
	def flags(self, index: qt.QModelIndex) -> qt.Qt.ItemFlags | qt.Qt.ItemFlag:
		return qt.Qt.ItemIsEnabled | qt.Qt.ItemIsSelectable


class FreeformRegionsEditorModel(qt.Model):

	rigNameChanged = qt.Signal(str)

	pickEvent = qt.Signal(str)
	addRegionEvent = qt.Signal(RegionEvent)
	rootChangedEvent = qt.Signal(RegionEvent)
	endChangedEvent = qt.Signal(RegionEvent)
	selectionChangedEvent = qt.Signal(RegionEvent)

	def __init__(self):
		super().__init__()

		self._rig_name = ''
		self._selected_region_item: FreeformRegion | None = None
		self._check_root_end_connection = True

		self._regions_model = FreeformRegionsListModel()
		self._regions_proxy_model = qt.QSortFilterProxyModel()
		self._regions_proxy_model.setSourceModel(self._regions_model)

	@property
	def rig_name(self) -> str:
		return self._rig_name

	@rig_name.setter
	def rig_name(self, value: str):
		self._rig_name = value
		self.rigNameChanged.emit(self._rig_name)

	@property
	def model(self) -> FreeformRegionsListModel:
		return self._regions_model

	@property
	def proxy_model(self) -> qt.QSortFilterProxyModel:
		return self._regions_proxy_model

	@property
	def selected_region_item(self):
		return self._selected_region_item

	@selected_region_item.setter
	def selected_region_item(self, value):
		if self.selected_region_item == value:
			return
		self._selected_region_item = value
		if value is not None:
			pass

	@property
	def check_root_end_connection(self) -> bool:
		return self._check_root_end_connection

	@property
	def root(self) -> str:
		return self.state.root

	@root.setter
	def root(self, value: str):

		if self.root == value:
			return
		if self.selected_region_item is not None and self.selected_region_item.is_valid and self.check_root_end_connection:
			region_event = RegionEvent(region=self.selected_region_item, value=value)
			self.rootChangedEvent.emit(region_event)
			if region_event.success:
				self.selected_region_item.root = value
				self.update('root', value)
		else:
			self.update('root', value)

		if self.state.highlight_regions:
			region_event = RegionEvent(region=self.selected_region_item, success=self.state.highlight_regions)
			self.selectionChangedEvent.emit(region_event)

	@property
	def end(self) -> str:
		return self.state.end

	@end.setter
	def end(self, value: str):
		if self.end == value:
			return
		if self.selected_region_item is not None and self.selected_region_item.is_valid and self.check_root_end_connection:
			region_event = RegionEvent(region=self.selected_region_item, value=value)
			self.endChangedEvent.emit(region_event)
			if region_event.success:
				self.selected_region_item.end = value
				self.update('end', value)
		else:
			self.update('end', value)

		if self.state.highlight_regions:
			region_event = RegionEvent(region=self.selected_region_item, success=self.state.highlight_regions)
			self.selectionChangedEvent.emit(region_event)

	def add_region(self):
		"""
		Adds new region.
		"""

		region_to_add = FreeformRegion(
			side=self.state.side, name=self.state.region, group=self.state.group, root=self.root, end=self.end,
			com_object=self.state.com_object, com_region=self.state.com_region, com_weight=self.state.com_weight)
		region_event = RegionEvent(region=region_to_add)
		self.addRegionEvent.emit(region_event)
		if region_event.success:
			self._regions_model.layoutChanged.emit()
			self._regions_model.regions.append(region_event.region)
			self._regions_model.layoutChanged.emit()
			self.root = ''
			self.end = ''
