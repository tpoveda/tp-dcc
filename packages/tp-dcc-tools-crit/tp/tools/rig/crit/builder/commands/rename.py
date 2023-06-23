from overrides import override

from tp.common.qt import api as qt
from tp.commands import crit
from tp.tools.rig.crit.builder.core import command


class RenameRigUiCommand(command.CritUiCommand):

	ID = 'renameRig'
	UI_DATA = {'icon': 'pencil', 'label': 'Rename Rig'}

	@override(check_signature=False)
	def execute(self):
		"""
		Renames current active rig.
		"""

		if self.rig_exists():
			return

		text = qt.input_dialog(
			title='Rename Rig', message='Enter new rig name:', text=self._rig_model.name, parent=self._crit_builder)
		if not text:
			return

		if text != self._rig_model.name:
			crit.rename_rig(self._rig_model.rig, text)

		self.request_refresh()
		self._crit_builder.update_rig_name()
