from __future__ import annotations

import typing
from functools import partial

from overrides import override

from tp.common.qt import api as qt

if typing.TYPE_CHECKING:
	from tp.tools.rig.freeform.regionseditor.model import FreeformRegionsEditorModel


class FreeformRegionsEditorWindow(qt.FramelessWindow):

	_highlight_check: qt.QCheckBox
	_filter_line_edit: qt.BaseLineEdit
	_mirror_from_line_edit: qt.BaseLineEdit
	_mirror_to_line_edit: qt.BaseLineEdit
	_joints_from_line_edit: qt.BaseLineEdit
	_joints_to_line_edit: qt.BaseLineEdit
	_mirror_button: qt.BaseToolButton
	_regions_list: RegionsListView
	_side_line_edit: qt.BaseLineEdit
	_group_line_edit: qt.BaseLineEdit
	_region_line_edit: qt.BaseLineEdit
	_com_object_line_edit: qt.BaseLineEdit
	_com_object_line_edit: qt.BaseLineEdit
	_com_region_line_edit: qt.BaseLineEdit
	_com_weight_spin: qt.QDoubleSpinBox
	_root_line_edit: qt.BaseLineEdit
	_root_button: qt.BaseToolButton
	_end_line_edit: qt.BaseLineEdit
	_end_button: qt.BaseToolButton
	_add_button: qt.BaseToolButton
	_remove_button: qt.BaseToolButton
	_new_region_button: qt.BaseToolButton

	def __init__(self, model: FreeformRegionsEditorModel, parent: qt.QWidget | None = None):

		self._model = model

		super().__init__(
			name='FreeformRegionsEditor', title='Freeform Regions Editor', width=300, height=600, parent=parent)

	@override
	def setup_ui(self):
		super().setup_ui()

		main_layout = self.main_layout()

		filter_layout = qt.horizontal_layout()
		self._filter_line_edit = qt.line_edit(parent=self)
		self._highlight_check = qt.checkbox('Highlight', parent=self)
		filter_layout.addWidget(qt.label('Filter: ', parent=self))
		filter_layout.addWidget(self._filter_line_edit)
		filter_layout.addWidget(self._highlight_check)

		accordion_widget = qt.AccordionWidget(parent=self)
		accordion_widget.setMaximumHeight(120)
		mirror_grid_layout = qt.grid_layout()
		mirror_regions_widget = qt.widget(layout=mirror_grid_layout, parent=self)
		self._mirror_from_line_edit = qt.line_edit(parent=self)
		self._mirror_to_line_edit = qt.line_edit(parent=self)
		self._joints_from_line_edit = qt.line_edit(parent=self)
		self._joints_to_line_edit = qt.line_edit(parent=self)
		self._mirror_button = qt.tool_button('Mirror', parent=self)
		mirror_grid_layout.addWidget(qt.label('Regions:', parent=self), 0, 0, qt.Qt.AlignRight)
		mirror_grid_layout.addWidget(self._mirror_from_line_edit, 0, 1)
		mirror_grid_layout.addWidget(self._mirror_to_line_edit, 0, 2)
		mirror_grid_layout.addWidget(qt.label('Joints:', parent=self), 1, 0, qt.Qt.AlignRight)
		mirror_grid_layout.addWidget(self._joints_from_line_edit, 1, 1)
		mirror_grid_layout.addWidget(self._joints_to_line_edit, 1, 2)
		mirror_grid_layout.addWidget(self._mirror_button, 0, 3, 2, 1)
		accordion_widget.add_item('Mirror Filtered Regions', mirror_regions_widget, collapsed=False)

		self._regions_list = RegionsListView(parent=self)
		self._regions_list.setModel(self._model.proxy_model)
		self._regions_list.setSizePolicy(qt.QSizePolicy.Preferred, qt.QSizePolicy.MinimumExpanding)

		grid_layout = qt.grid_layout()
		self._side_line_edit = qt.line_edit(parent=self)
		self._group_line_edit = qt.line_edit(parent=self)
		self._region_line_edit = qt.line_edit(parent=self)
		self._com_object_line_edit = qt.line_edit(parent=self)
		self._com_region_line_edit = qt.line_edit(parent=self)
		self._com_weight_spin = qt.QDoubleSpinBox(parent=self)
		self._root_line_edit = qt.line_edit(parent=self)
		self._root_button = qt.tool_button(icon='cursor', parent=self)
		self._end_line_edit = qt.line_edit(parent=self)
		self._end_button = qt.tool_button(icon='cursor', parent=self)
		grid_layout.addWidget(qt.label('Side:', parent=self), 0, 0, qt.Qt.AlignRight)
		grid_layout.addWidget(self._side_line_edit, 0, 1, 1, 2)
		grid_layout.addWidget(qt.label('Group:', parent=self), 0, 3, qt.Qt.AlignRight)
		grid_layout.addWidget(self._group_line_edit, 0, 4, 1, 2)
		grid_layout.addWidget(qt.label('Region:', parent=self), 1, 0, qt.Qt.AlignRight)
		grid_layout.addWidget(self._region_line_edit, 1, 1, 1, 5)
		grid_layout.addWidget(qt.label('COM:', parent=self), 2, 0, qt.Qt.AlignRight)
		grid_layout.addWidget(self._com_object_line_edit, 2, 1)
		grid_layout.addWidget(qt.label('Region:', parent=self), 2, 2, qt.Qt.AlignRight)
		grid_layout.addWidget(self._com_region_line_edit, 2, 3)
		grid_layout.addWidget(qt.label('Weight:', parent=self), 2, 4, qt.Qt.AlignRight)
		grid_layout.addWidget(self._com_weight_spin, 2, 5)
		grid_layout.addWidget(qt.label('Root', parent=self), 3, 0, qt.Qt.AlignRight)
		grid_layout.addWidget(self._root_line_edit, 3, 1, 1, 4)
		grid_layout.addWidget(self._root_button, 3, 5)
		grid_layout.addWidget(qt.label('End', parent=self), 4, 0, qt.Qt.AlignRight)
		grid_layout.addWidget(self._end_line_edit, 4, 1, 1, 4)
		grid_layout.addWidget(self._end_button, 4, 5)

		buttons_layout = qt.horizontal_layout()
		self._add_button = qt.tool_button('Add', parent=self)
		self._remove_button = qt.tool_button('Remove', parent=self)
		self._new_region_button = qt.tool_button('New Region', parent=self)
		buttons_layout.addWidget(self._add_button)
		buttons_layout.addWidget(self._remove_button)
		buttons_layout.addStretch()
		buttons_layout.addWidget(self._new_region_button)

		main_layout.addLayout(filter_layout)
		main_layout.addWidget(qt.divider(parent=self))
		main_layout.addWidget(accordion_widget)
		main_layout.addWidget(qt.divider(parent=self))
		main_layout.addWidget(self._regions_list)
		main_layout.addWidget(qt.divider(parent=self))
		main_layout.addLayout(grid_layout)
		main_layout.addWidget(qt.divider(parent=self))
		main_layout.addLayout(buttons_layout)

	@override
	def setup_signals(self):
		super().setup_signals()

		self._highlight_check.toggled.connect(self._model.updater('highlight_regions'))
		self._model.listen('highlight_regions', self._highlight_check.setChecked, value=False)
		self._side_line_edit.textChanged.connect(self._model.updater('side'))
		self._model.listen('side', self._side_line_edit.setText, value='')
		self._group_line_edit.textChanged.connect(self._model.updater('group'))
		self._model.listen('group', self._group_line_edit.setText, value='')
		self._region_line_edit.textChanged.connect(self._model.updater('region'))
		self._model.listen('region', self._region_line_edit.setText, value='')
		self._root_line_edit.textChanged.connect(self._model.updater('root'))
		self._com_object_line_edit.textChanged.connect(self._model.updater('com_object'))
		self._model.listen('com_object', self._com_object_line_edit.setText, value='')
		self._com_region_line_edit.textChanged.connect(self._model.updater('com_region'))
		self._model.listen('com_region', self._com_region_line_edit.setText, value='')
		self._com_weight_spin.valueChanged.connect(self._model.updater('com_weight'))
		self._model.listen('com_weight', self._com_weight_spin.setValue, value=0.0)
		self._model.listen('root', self._root_line_edit.setText, value='')
		self._end_line_edit.textChanged.connect(self._model.updater('end'))
		self._model.listen('end', self._end_line_edit.setText, value='')

		self._root_button.clicked.connect(partial(self._model.pickEvent.emit, 'root'))
		self._end_button.clicked.connect(partial(self._model.pickEvent.emit, 'end'))
		self._add_button.clicked.connect(self._model.add_region)


class RegionsListView(qt.QListView):

	@override
	def mousePressEvent(self, event: qt.QMouseEvent) -> None:
		if not self.indexAt(event.pos()).isValid():
			self.selectionModel().clear()
		super().mousePressEvent(event)
