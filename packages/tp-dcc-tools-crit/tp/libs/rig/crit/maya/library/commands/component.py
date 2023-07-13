from __future__ import annotations

from typing import Tuple, List, Dict

from overrides import override

from tp.maya.api import command
from tp.libs.rig.crit import api as crit


class RenameComponentCommand(command.MayaCommand):
	"""
	Rename component instance with new name, excluding side label
	"""

	id = 'crit.component.rename'
	creator = 'Tomas Poveda'
	is_undoable = True
	is_enabled = True
	ui_data = {'icon': '', 'tooltip': __doc__, 'label': 'Rename Component', 'color': 'white', 'backgroundColor': 'black'}

	_component = None			# type: crit.Component
	_old_name = ''

	@override
	def resolve_arguments(self, arguments: Dict) -> Dict | None:
		component = arguments.get('component')
		name = arguments.get('name')
		if not name:
			self.display_warning('Must specify a valid name argument')
			return
		self._component = component
		self._old_name = name

		return arguments

	@override(check_signature=False)
	def do(self, component: crit.Component | None = None, name: str | None = None):
		component.rename(name)

	@override
	def undo(self):
		if self._component is not None and self._old_name:
			self._component.rename(self._old_name)


class SetSideComponentCommand(command.MayaCommand):
	"""
	Rename component instance side
	"""

	id = 'crit.component.rename.side'
	creator = 'Tomas Poveda'
	is_undoable = True
	is_enabled = True
	ui_data = {'icon': '', 'tooltip': __doc__, 'label': 'Rename Component Side', 'color': '', 'backgroundColor': ''}

	_component = None			# type: crit.Component
	_old_side = ''

	@override
	def resolve_arguments(self, arguments: Dict) -> Dict | None:
		component = arguments.get('component')
		side = arguments.get('side')
		if not side:
			self.display_warning('Must specify a valid side argument')
			return
		self._component = component
		self._old_side = side

		return arguments

	@override(check_signature=False)
	def do(self, component: crit.Component | None = None, side: str | None = None):
		component.set_side(side)

	@override
	def undo(self):
		if self._component is not None and self._old_side:
			self._component.set_side(self._old_side)


class DeleteComponentCommand(command.MayaCommand):
	"""
	Deletes a component
	"""

	id = 'crit.component.delete'
	creator = 'Tomas Poveda'
	is_undoable = True
	is_enabled = True
	use_undo_chunk = True
	disable_queue = True
	ui_data = {'icon': '', 'tooltip': __doc__, 'label': 'Delete Component', 'color': 'white', 'backgroundColor': 'black'}

	_rig = None									# type: crit.Rig
	_components = []							# type: List[crit.Component]
	_serialized_component_data = []				# type: List[Tuple[Dict, bool, bool, bool], ...]

	@override
	def resolve_arguments(self, arguments: Dict) -> Dict | None:
		self._serialized_component_data = []
		for component in arguments.get('components', []):
			self._serialized_component_data.append(
				(component.serialize_from_scene(), component.has_guide(), component.has_skeleton(), component.has_rig()))
		self._rig = arguments.get('rig')
		self._components = arguments.get('components', [])
		if arguments.get('children'):
			child_components = []
			for component in self._components:
				children = list(component.iterate_children())
				child_components.extend(children)
			self._components.extend(child_components)

		return arguments

	@override(check_signature=False)
	def do(self, rig: crit.Rig | None = None, components: List[crit.Component] | None = None, children: bool = True):
		for component in self._components:
			self._rig.delete_component(name=component.name(), side=component.side())

	@override
	def undo(self):
		self._components = []
		if self._rig is not None and self._rig.exists():
			guides_to_build = []
			skeletons_to_build = []
			rigs_to_build = []
			for data, guide, skeleton, rig in self._serialized_component_data:
				component = self._rig.create_component(data['type'], data['name'], data['side'], descriptor=data)
				if guide:
					guides_to_build.append(component)
				if skeleton:
					skeletons_to_build.append(component)
				if rig:
					rigs_to_build.append(component)
				self._components.append(component)
			if guides_to_build:
				self._rig.build_guides(guides_to_build)
			if skeletons_to_build:
				self._rig.build_skeleton(skeletons_to_build)
			if rigs_to_build:
				self._rig.build_rig(rigs_to_build)
