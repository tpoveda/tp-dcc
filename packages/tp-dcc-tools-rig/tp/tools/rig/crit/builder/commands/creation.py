from __future__ import annotations

import typing

from overrides import override

from tp.commands import crit
from tp.tools.rig.crit.builder.core import command, utils

if typing.TYPE_CHECKING:
	from tp.libs.rig.crit.maya.core.rig import Rig
	from tp.libs.rig.crit.maya.core.component import Component
	from tp.libs.rig.crit.maya.descriptors.component import ComponentDescriptor


class CreateRigUiCommand(command.CritUiCommand):

	ID = 'createRig'
	UI_DATA = {'icon': 'add', 'label': 'Create rig instance'}

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


class CreateComponentUiCommand(command.CritUiCommand):

	ID = 'createComponent'
	UI_DATA = {'icon': 'add', 'label': 'Create component'}

	@override(check_signature=False)
	def execute(
			self, component_type: str, name: str, side: str,
			descriptor: ComponentDescriptor | None = None) -> Component | None:
		"""
		Creates a new component instance.

		:param str component_type: type of the component to create.
		:param str name: name of the component to create.
		:param str side: side of the component to create.
		:param ComponentDescriptor descriptor: optional component descriptor to use.
		:return: newly created component.
		:rtype: Component or None
		"""

		if not self._rig_model:
			return None

		success = utils.check_scene_units(parent=self._ui_interface.builder())
		if not success:
			return None

		name = descriptor.get('name', name) if descriptor is not None else name
		side = descriptor.get('side', side) if descriptor is not None else side

		components_to_create = {'type': component_type, 'name': name, 'side': side, 'descriptor': descriptor}
		components = crit.create_components(self._rig_model.rig, components=[components_to_create], build_guides=True)
		self.request_refresh(False)

		return components[0] if components else None
