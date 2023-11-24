from __future__ import annotations

import typing

from overrides import override

from tp.common.qt import api as qt
from tp.commands import crit
from tp.tools.rig.crit.builder.core import command

if typing.TYPE_CHECKING:
    from tp.tools.rig.crit.builder.models.component import ComponentModel


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


class SetComponentSideUiCommand(command.CritUiCommand):

    ID = 'setComponentSide'
    UI_DATA = {'icon': 'solo', 'label': 'Set Component Side'}

    @override(check_signature=False)
    def execute(self, side: str, component_model: ComponentModel | None = None):
        """
        Sets component side.

        :param str side: new component side.
        :param ComponentModel or None component_model: optional component model to set side of. If not given, current
            selected component side will be set.
        """

        if not self._rig_model:
            return

        model = component_model or self.selected_components()[0]
        model.side = side
        self.request_refresh()
        self.refresh_components([model])
