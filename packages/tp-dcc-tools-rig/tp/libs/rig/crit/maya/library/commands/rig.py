from __future__ import annotations

from typing import Dict

from overrides import override

from tp.maya.api import command
from tp.libs.rig.crit import api as crit


class CreateRigCommand(command.MayaCommand):

	id = 'crit.rig.create'
	creator = 'Tomas Poveda'
	is_undoable = False
	is_enabled = True

	_rig = None				# type: crit.Rig

	@override
	def resolve_arguments(self, arguments: Dict) -> Dict:
		arguments['namespace'] = arguments.get('namespace', None)
		name = arguments.get('name')
		name = name or 'CritRig'
		arguments['name'] = crit.naming.unique_name_for_rig(crit.iterate_scene_rigs(), name)

		return arguments

	@override(check_signature=False)
	def do(self, name: str | None = None, namespace: str | None = None) -> crit.Rig:
		new_rig = crit.Rig()
		self._rig = new_rig
		new_rig.start_session(name, namespace=namespace)

		return new_rig
