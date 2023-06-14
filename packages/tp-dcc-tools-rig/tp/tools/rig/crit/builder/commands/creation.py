from __future__ import annotations

import typing

from overrides import override

from tp.commands import crit
from tp.tools.rig.crit.builder.core import command, utils

if typing.TYPE_CHECKING:
	from tp.libs.rig.crit.maya.core.rig import Rig


class CreateRigUiCommand(command.CritUiCommand):

	ID = 'createRig'

	@override(check_signature=False)
	def execute(self, name: str) -> Rig | None:
		"""
		Creates a new rig instance.

		:param str name: name of the rig.
		:return: newly created rig instance.
		:rtype: Rig or None
		"""

		success = utils.check_scene_units(parent=self._ui_interface.builder())
		if not success:
			return None

		new_rig = crit.create_rig(name=name)
		self.request_refresh(False)

		return new_rig
