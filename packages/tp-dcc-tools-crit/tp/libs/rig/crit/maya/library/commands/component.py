from __future__ import annotations

from typing import Tuple, List, Dict

from overrides import override

import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya

from tp.maya import api
from tp.maya.api import command
from tp.maya.om import scene, nodes
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


class AddParentComponentFromSelectionCommand(command.MayaCommand):
	"""
	Adds component parent from selection
	"""

	id = 'crit.component.parent.selectionAdd'
	creator = 'Tomas Poveda'
	is_undoable = True
	use_undo_chunk = True
	disable_queue = True
	ui_data = {'icon': '', 'tooltip': __doc__, 'label': 'Parent Component', 'color': '', 'backgroundColor': ''}

	_driven_components = []
	_driver_components = []

	@override
	def resolve_arguments(self, arguments: Dict) -> Dict | None:
		selection = list(api.selected(filter_types=api.kTransform))
		if len(selection) < 2:
			self.display_warning('Must have at least 2 nodes selected')
			return

		driven_nodes = selection[:-1]
		driver = selection[-1]
		if not crit.Guide.is_guide(driver):
			self.display_warning('Driver is not a guide')
			return
		driver_guide = crit.Guide(driver.object())
		if driver_guide.is_root():
			self.display_warning('Parenting to the root guide is not allowed')
			return
		driver_component = crit.component_from_node(driver)
		if not driver_component.id_mapping()[crit.consts.SKELETON_LAYER_TYPE].get(driver_guide.id()):
			self.display_warning('Setting parent to a guide which does not belong to a joint is not allowed')
			return

		visited = set()
		driven_component_map = []
		for driven in driven_nodes:
			if not crit.Guide.is_guide(driven):
				self.display_warning('Driven is not a guide')
				return
			driven_component = crit.component_from_node(driven)
			if not driven_component:
				continue
			if driven_component in visited or driven_component == driver_component:
				continue
			visited.add(driven_component)
			driven_component_map.append(driven_component)
		if driver_component is None:
			self.display_warning('Failed to find any CRIT components in selection.')
			return
		if not driven_component_map:
			self.display_warning('No valid driven guides to parent')
			return
		self._driver_components = (driver_component, driver_guide)
		self._driven_components = driven_component_map

		arguments['driver'] = self._driver_components[1]
		arguments['driven'] = driven_component_map

		return arguments

	@override(check_signature=False)
	def do(self, driver: crit.Component | None = None, driven: List[crit.Component] | None = None):
		driver = self._driver_components
		success = False
		for component in self._driven_components:
			success = component.set_parent(driver[0], driver[1])

		return success

	@override
	def undo(self):
		driver = self._driver_components
		for component in self._driver_components:
			component.remove_parent(driver[0])


class SelectGuidesCommand(command.MayaCommand):
	"""
	Selects all guide pivots of components
	"""

	id = 'crit.component.guide.select'
	creator = 'Tomas Poveda'
	is_undoable = True
	is_enabled = True
	ui_data = {'icon': '', 'tooltip': __doc__, 'label': 'Select Guides', 'color': '', 'backgroundColor': ''}

	_old_selection = OpenMaya.MSelectionList()

	@override
	def resolve_arguments(self, arguments: Dict) -> Dict | None:
		super().resolve_arguments(arguments)

		components = arguments.get('components', [])
		selection = scene.selected_nodes()
		self._old_selection = map(OpenMaya.MObjectHandle, selection)

		if not components:
			for node in selection:
				component = crit.component_from_node(node)
				if component and component.has_guide():
					components.append(component)
			if not components:
				self.display_warning('No components found!')
				return
		else:
			new_components = []
			for component in components:
				if component.has_guide():
					new_components.append(component)
			return {'components': new_components}

		return {'components': components}

	@override(check_signature=False)
	def do(self, components: List[crit.Component] | None = None):
		self._old_selection = OpenMaya.MGlobal.getActiveSelectionList()
		new_selection = set()
		for component in components:
			for guide in component.guide_layer().iterate_guides():
				new_selection.add(guide.fullPathName())
		if new_selection:
			cmds.select(list(new_selection), replace=True)

	@override
	def undo(self):
		if self._old_selection:
			cmds.select([nodes.name(i.object()) for i in self._old_selection], deselect=True)


class SelectGuideRootPivotCommand(command.MayaCommand):
	"""
	Selects all guide root pivots of components
	"""

	id = 'crit.component.guide.select.root'
	creator = 'Tomas Poveda'
	is_undoable = True
	is_enabled = True
	ui_data = {'icon': '', 'tooltip': __doc__, 'label': 'Select Root Guide', 'color': '', 'backgroundColor': ''}

	_old_selection = OpenMaya.MSelectionList()

	@override
	def resolve_arguments(self, arguments: Dict) -> Dict | None:
		super().resolve_arguments(arguments)

		components = arguments.get('components', [])
		selection = scene.selected_nodes()
		self._old_selection = map(OpenMaya.MObjectHandle, selection)

		if not components:
			for node in selection:
				component = crit.component_from_node(node)
				if component and component.has_guide():
					components.append(component)
			if not components:
				self.display_warning('No components found!')
				return
		else:
			new_components = []
			for component in components:
				if component.has_guide():
					new_components.append(component)
			return {'components': new_components}

		return {'components': components}

	@override(check_signature=False)
	def do(self, components: List[crit.Component] | None = None):
		new_selection = set()
		for component in components:
			root_guide = component.guide_layer().guide_root()
			if root_guide is not None:
				new_selection.add(root_guide.fullPathName())
		if new_selection:
			cmds.select(list(new_selection), replace=True)

	@override
	def undo(self):
		if self._old_selection:
			cmds.select([nodes.name(i.object()) for i in self._old_selection], deselect=True)


class SelectGuideShapesCommand(command.MayaCommand):
	"""
	Selects all shapes of given guides
	"""

	id = 'crit.component.guide.select.shapes'
	creator = 'Tomas Poveda'
	is_undoable = True
	is_enabled = True
	ui_data = {'icon': '', 'tooltip': __doc__, 'label': 'Select Guide Shapes', 'color': '', 'backgroundColor': ''}

	_old_selection = OpenMaya.MSelectionList()

	@override
	def resolve_arguments(self, arguments: Dict) -> Dict | None:
		super().resolve_arguments(arguments)

		guides = arguments.get('guides', [])

		if not guides:
			for node in scene.selected_nodes():
				if crit.Guide.is_guide(api.node_by_object(node.object())):
					guides.append(crit.Guide(node.object()))
		if not guides:
			self.display_warning('No guides found!')
			return

		self._old_selection = OpenMaya.MGlobal.getActiveSelectionList()

		return {'guides': guides}

	@override(check_signature=False)
	def do(self, guides: List[crit.Guide] | None = None):
		new_selection = set()
		for guide in guides:
			shape_node = guide.shape_node()
			if shape_node is not None:
				new_selection.add(shape_node.fullPathName())
		if new_selection:
			cmds.select(list(new_selection), replace=True)

	@override
	def undo(self):
		if self._old_selection:
			cmds.select([nodes.name(i.object()) for i in self._old_selection], deselect=True)


class SelectAllGuideShapesCommand(command.MayaCommand):
	"""
	Selects all guide shapes
	"""

	id = 'crit.component.guide.select.shapes.all'
	creator = 'Tomas Poveda'
	is_undoable = True
	is_enabled = True
	ui_data = {'icon': '', 'tooltip': __doc__, 'label': 'Select All Guide Shapes', 'color': '', 'backgroundColor': ''}

	_old_selection = OpenMaya.MSelectionList()

	@override
	def resolve_arguments(self, arguments: Dict) -> Dict | None:
		super().resolve_arguments(arguments)

		components = arguments.get('components', [])
		selection = scene.selected_nodes()
		self._old_selection = map(OpenMaya.MObjectHandle, selection)

		if not components:
			for node in selection:
				component = crit.component_from_node(node)
				if component and component.has_guide():
					components.append(component)
			if not components:
				self.display_warning('No components found!')
				return
		else:
			new_components = []
			for component in components:
				if component.has_guide():
					new_components.append(component)
			return {'components': new_components}

		return {'components': components}

	@override(check_signature=False)
	def do(self, components: List[crit.Component] | None = None):
		new_selection = set()
		for component in components:
			for guide in component.guide_layer().iterate_guides():
				shape_node = guide.shape_node()
				if shape_node is not None:
					new_selection.add(shape_node.fullPathName())
		if new_selection:
			cmds.select(list(new_selection), replace=True)

	@override
	def undo(self):
		if self._old_selection:
			cmds.select([nodes.name(i.object()) for i in self._old_selection], deselect=True)


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
