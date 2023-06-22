from __future__ import annotations

import typing
from typing import List, Dict

from overrides import override

from tp.maya import api
from tp.maya.api import command
from tp.libs.rig.crit import api as crit


class CreateRigCommand(command.MayaCommand):

	id = 'crit.rig.create'
	creator = 'Tomas Poveda'
	is_undoable = False
	is_enabled = True
	ui_data = {
		'icon': '', 'tooltip': 'Creates a new instance of rig or returns the existing one',
		'label': 'Create rig', 'color': 'white', 'backgroundColor': 'black'}

	_rig = None				# type: crit.Rig

	@override
	def resolve_arguments(self, arguments: Dict) -> Dict | None:
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


class CreateComponentsCommand(command.MayaCommand):

	id = 'crit.rig.create.components'
	creator = 'Tomas Poveda'
	is_undoable = True
	is_enabled = True
	use_undo_chunk = True
	disable_queue = True
	ui_data = {
		'icon': '', 'tooltip': 'Creates multiple components', 'label': 'Add multiple components', 'color': 'white',
		'backgroundColor': 'black'}

	_rig = None  				# type: crit.Rig
	_rig_name = []				# type: List[str]
	_components = []			# type: List[Dict]
	_parent_node = None			# type: api.DagNode

	@override
	def resolve_arguments(self, arguments: Dict) -> Dict | None:
		rig = arguments.get('rig', None)
		component_data = arguments.get('components', None)
		if not component_data:
			self.display_warning('Must supply component data list')
			return None
		if rig is None or not isinstance(rig, crit.Rig):
			self.display_warning('Must supply the rig instance to the command')
			return None
		if not rig.exists():
			self.display_warning('Rig does not exist within scene')
			return None

		selection = list(api.selected(filter_types=api.kTransform))
		if selection:
			arguments['parent_node'] = selection[0]
		self._rig = rig
		self._components = component_data
		self._parent_node = arguments.get('parent_node', None)

		return arguments

	@override(check_signature=False)
	def do(
			self, rig: crit.Rig, components: List[Dict], build_guides: bool = False, build_rigs: bool = False,
			parent_node: api.DagNode | None = None) -> List[crit.Component]:

		created_components = []

		for data in self._components:
			new_component = rig.create_component(
				data['type'], name=data['name'], side=data['side'], descriptor=data.get('descriptor', None))
			data['name'] = new_component.name()
			data['side'] = new_component.side()
			if new_component:
				created_components.append(new_component)

		if build_guides:
			pass

		if build_rigs:
			pass

		return created_components
