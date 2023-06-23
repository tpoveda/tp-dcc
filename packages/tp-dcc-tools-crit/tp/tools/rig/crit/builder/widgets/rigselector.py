from __future__ import annotations

import typing
from typing import List

from tp.preferences.interfaces import core
from tp.common.qt import api as qt

if typing.TYPE_CHECKING:
	from tp.tools.rig.crit.builder.ui import CritBuilderWindow


class RigSelector(qt.QWidget):
	"""
	Custom widget that contains a combo box that allow users to:
		- Set the current active CRIT rig.
		- Add CRIT rigs.
		- Remove CRIT rigs.
		- Rename CRIT rigs.
	"""

	addRigClicked = qt.Signal()
	renameClicked = qt.Signal()
	deleteRigClicked = qt.Signal()

	def __init__(self, crit_builder: CritBuilderWindow):
		super().__init__(crit_builder)

		self._builder_ui = crit_builder
		self._theme_pref = core.theme_preference_interface()

		self._main_layout = qt.horizontal_layout(spacing=qt.dpi_scale(2), margins=(0, 0, 0, 0), parent=self)
		self._main_layout.setAlignment(qt.Qt.AlignTop)

		self._rig_combo_box = qt.combobox(parent=self)
		self._create_button = qt.styled_button(
			style=qt.consts.ButtonStyles.TRANSPARENT_BACKGROUND, icon='plus', tooltip='Create New Rig',
			theme_updates=False, parent=self)
		self._rename_button = qt.styled_button(
			style=qt.consts.ButtonStyles.TRANSPARENT_BACKGROUND, icon='rename', tooltip='Rename Rig',
			theme_updates=False, parent=self)
		self._delete_button = qt.styled_button(
			style=qt.consts.ButtonStyles.TRANSPARENT_BACKGROUND, icon='trash', tooltip='Delete Rig',
			theme_updates=False, parent=self)

		self._setup_ui()
		self._setup_signals()
		self._check_rig_exists()

	def current_text(self) -> str:
		"""
		Returns rig name combo box current text.

		:return: combo box text.
		:rtype: str
		"""

		return self._rig_combo_box.currentText()

	def set_current_index(self, index: int, update: bool = True):
		"""
		Sets current rig combo box index.

		:param int index: combo box item index to set.
		:param bool update: whether to update widget.
		"""

		if not update:
			self.setUpdatesEnabled(False)

		self._rig_combo_box.setCurrentIndex(index)

		if not self.updatesEnabled():
			self.setUpdatesEnabled(True)

	def update_list(self, rig_names: List[str], set_to: str = '', keep_same: bool = False) -> str:
		"""
		Clears the rig names combo box and updates it with the new list of rig names.

		:param List[str] rig_names: list of rig names.
		:param str set_to: set to this rig when after combo box is updated.
		:param bool keep_same: whether to try to set the rig to the same rig as before the update.
		:return: current selected rig name.
		:rtype: str
		"""

		self.setUpdatesEnabled(False)

		try:
			orig_index = 0 if not keep_same else self._rig_combo_box.findText(self._rig_combo_box.currentText())
			self._rig_combo_box.clear()
			self._rig_combo_box.addItems(rig_names)
			if keep_same:
				orig_index = len(rig_names) - 1 if orig_index >= len(rig_names) else orig_index
				self._rig_combo_box.setCurrentIndex(orig_index)
			elif set_to:
				rig_index = rig_names.index(set_to)
				if rig_index >= 0:
					self._rig_combo_box.setCurrentIndex(rig_index)
		finally:
			self.setUpdatesEnabled(True)

		self._check_rig_exists()

		return self._rig_combo_box.currentText()

	def _setup_ui(self):
		"""
		Internal function that setup widget UI.
		"""

		self.setLayout(self._main_layout)
		self.setFixedHeight(qt.dpi_scale(18))
		self._rig_combo_box.setMinimumWidth(qt.dpi_scale(18))
		self._main_layout.addWidget(self._rig_combo_box)
		self._main_layout.addWidget(self._create_button)
		self._main_layout.addWidget(self._rename_button)
		self._main_layout.addWidget(self._delete_button)
		self._main_layout.setStretchFactor(self._rig_combo_box, 5)

	def _setup_signals(self):
		"""
		Internal function that setup widget signals.
		"""

		self._create_button.leftClicked.connect(self._create_button_left_clicked)
		self._rename_button.leftClicked.connect(self._rename_button_left_clicked)
		self._delete_button.leftClicked.connect(self._delete_button_left_clicked)
		self._rig_combo_box.currentTextChanged.connect(self._on_rig_combo_box_current_text_changed)

	def _check_rig_exists(self):
		"""
		Internal function that updates widgets based on whether rig exists.
		"""

		rig_exists = self._builder_ui.controller.current_rig_exists()
		self._rename_button.setEnabled(rig_exists)
		self._delete_button.setEnabled(rig_exists)

	def _create_button_left_clicked(self):
		"""
		Internal callback function that is called when Create Rig button is clicked by the user.
		Emits addRigClicked signal and updates widget based on whether rig exists.
		"""

		self.addRigClicked.emit()
		self._check_rig_exists()

	def _rename_button_left_clicked(self):
		"""
		Internal callback function that is called when Rename Rig button is clicked by the user.
		Emits renameClicked signal and updates widget based on whether rig exists.
		"""

		self.renameClicked.emit()
		self._check_rig_exists()

	def _delete_button_left_clicked(self):
		"""
		Internal callback function that is called when Delete Rig button is clicked by the user.
		Emits deleteRigClicked signal and updates widget based on whether rig exists.
		"""

		self.deleteRigClicked.emit()
		self._check_rig_exists()

	def _on_rig_combo_box_current_text_changed(self, text: str):
		"""
		Internal callback function that is called each time rig combo box text changes.

		:param str text: combo box current text (which indeed is the rig name).
		"""

		self._builder_ui.set_rig(self._rig_combo_box.currentText(), apply=self.updatesEnabled())
